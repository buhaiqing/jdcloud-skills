# Redaction Reference — `jdcloud-audit-ops`

> **用途**：所有审计事件详情中的 `requestParameters` / `responseElements`，以及任何导出到 GCL trace、CI log、Slack、Email、SIEM、对象存储或工单系统的数据，在输出前都必须先调用本页的脱敏逻辑。

## Why this matters

操作审计日志用于 SecOps / AIOps 取证，可能包含 API 请求参数、响应内容、账号标识、公网 IP、手机号、邮箱或临时凭证。审计数据本身是高敏数据：

- **不要**把 raw secret 写入 GCL trace / CI log / Slack / Email / SIEM。
- **不要**在调试日志中打印 `requestParameters` / `responseElements` 原文。
- **不要**把外部 webhook token、SMTP 密码、Splunk HEC token 等写入示例输出。
- 如需保留取证关联能力，使用 `forensic_sealed` 模式输出 SHA-256 前缀，而不是输出原文。

## Privacy modes

| Mode | Use case | Behavior |
|---|---|---|
| `masked_default` | 默认展示、机器人回答、普通审计报告 | secret 类字段替换为 `***`；手机号、邮箱、身份证、公网 IP 做 mask |
| `full_internal` | 受控内网人工排障视图 | secret 类字段仍替换为 `***`；非 secret PII 可保留原文；需控制访问权限 |
| `forensic_sealed` | 复盘证据包、跨系统关联 | secret 类字段替换为 `***`；PII 输出 `sha256:<12位前缀>`，便于关联但不暴露原文 |

> **强约束**：`password` / `secret` / `token` / `privateKey` 等 secret 类字段在所有模式下都不得原文输出。

## Python reference implementation

> 这是 **reference implementation / pseudo-code**，用于复制到本地脚本或 agent runtime。它不联网、不读取真实凭据。

```python
import copy
import hashlib
import ipaddress
import re
from typing import Any

SECRET_KEYS = {
    "password", "passwd", "pwd",
    "secret", "secretkey", "accesskey", "accesskeysecret",
    "token", "authorization", "credential",
    "privatekey", "sessionkey", "apikey",
}

# 这些字段不是 secret，但外部导出时建议 mask/hash。
PII_KEYS = {
    "username", "user", "account", "email", "phone", "mobile",
    "sourceip", "sourceipaddress", "clientip", "ip", "userid", "principal",
    "resourceid", "useragent",
}

# 证据锚点字段：即使 forensic_sealed 也保留原样，用于关联和追踪。
# 这些字段本身不含敏感内容，但误哈希会导致失去可追溯性。
EVIDENCE_ANCHOR_KEYS = {
    "eventid", "eventname", "eventtime", "requestid",
    "resourcetype", "regionid", "errorcode", "errormessage",
}

EMAIL_RE = re.compile(r"(?P<name>[A-Za-z0-9._%+-]+)@(?P<domain>[A-Za-z0-9.-]+\.[A-Za-z]{2,})")
PHONE_RE = re.compile(r"(?<!\d)(?:\+?86[- ]?)?(1[3-9]\d{9})(?!\d)")
ID_CARD_RE = re.compile(r"(?<!\d)(\d{6})(\d{8})(\d{3}[0-9Xx])(?!\d)")
IPV4_RE = re.compile(r"(?<!\d)((?:\d{1,3}\.){3}\d{1,3})(?!\d)")


def _sha256_prefix(value: Any, prefix_len: int = 12) -> str:
    raw = str(value).encode("utf-8", errors="replace")
    return "sha256:" + hashlib.sha256(raw).hexdigest()[:prefix_len]


def _normalize_key(key: Any) -> str:
    return re.sub(r"[^a-z0-9]", "", str(key).lower())


def _is_secret_key(key: Any) -> bool:
    normalized = _normalize_key(key)
    return normalized in SECRET_KEYS or any(marker in normalized for marker in ("password", "secret", "token", "privatekey", "credential"))


def _is_pii_key(key: Any) -> bool:
    normalized = _normalize_key(key)
    return normalized in PII_KEYS or any(marker in normalized for marker in ("email", "phone", "mobile", "sourceip", "clientip", "userid"))


def _is_evidence_anchor(key: Any) -> bool:
    normalized = _normalize_key(key)
    return normalized in EVIDENCE_ANCHOR_KEYS or any(marker in normalized for marker in ("eventid", "eventname", "eventtime", "requestid"))


def _mask_email(match: re.Match) -> str:
    name = match.group("name")
    domain = match.group("domain")
    visible = name[:2] if len(name) >= 2 else name[:1]
    return f"{visible}***@{domain}"


def _mask_phone(match: re.Match) -> str:
    phone = match.group(1)
    return phone[:3] + "****" + phone[-4:]


def _mask_id_card(match: re.Match) -> str:
    return match.group(1) + "********" + match.group(3)[-1]


def _mask_public_ipv4(match: re.Match) -> str:
    ip = match.group(1)
    try:
        parsed = ipaddress.ip_address(ip)
    except ValueError:
        return ip
    if parsed.version == 4 and parsed.is_global:
        parts = ip.split(".")
        return ".".join(parts[:3] + ["0"]) + "/24"
    # 私网 / 保留地址保留原样，用于内网排障
    return ip


def _mask_resource_id(value: str) -> str:
    """对资源 ID 做部分 mask，保留前缀用于定位，隐藏后缀防泄露。"""
    if not value or len(value) <= 6:
        return "***"
    # 保留前 4 个字符，其余 mask
    return value[:4] + "****"


def _transform_pii_string(value: str, mode: str, key_hint: Any = None) -> str:
    if mode == "full_internal":
        return value
    if mode == "forensic_sealed":
        # 对整段字符串做哈希，避免混合文本中泄露上下文。
        # 证据锚点字段在 walk 层已保护，不会走到这里。
        return _sha256_prefix(value)

    masked = EMAIL_RE.sub(_mask_email, value)
    masked = PHONE_RE.sub(_mask_phone, masked)
    masked = ID_CARD_RE.sub(_mask_id_card, masked)
    masked = IPV4_RE.sub(_mask_public_ipv4, masked)

    # resourceId 特殊处理：部分 mask
    if key_hint is not None and _normalize_key(key_hint) == "resourceid":
        masked = _mask_resource_id(masked)

    return masked


def mask_sensitive(data: Any, mode: str = "masked_default") -> Any:
    """Recursively redact JD Cloud Audit Log data.

    Args:
        data: dict/list/str or scalar value from audit event detail.
        mode: one of "masked_default", "full_internal", "forensic_sealed".

    Returns:
        A deep-copied, redacted object. The input object is not mutated.
    """
    if mode not in {"masked_default", "full_internal", "forensic_sealed"}:
        raise ValueError("mode must be masked_default, full_internal, or forensic_sealed")

    def walk(obj: Any, key_hint: Any = None) -> Any:
        if key_hint is not None and _is_secret_key(key_hint):
            return "***"

        if isinstance(obj, dict):
            return {k: walk(v, k) for k, v in obj.items()}

        if isinstance(obj, list):
            return [walk(item, key_hint) for item in obj]

        if isinstance(obj, str):
            # 证据锚点字段在所有模式下保留原样
            if key_hint is not None and _is_evidence_anchor(key_hint):
                return obj
            if key_hint is not None and _is_pii_key(key_hint):
                if mode == "forensic_sealed":
                    return _sha256_prefix(obj)
                if mode == "masked_default":
                    return _transform_pii_string(obj, mode, key_hint)
                return obj
            return _transform_pii_string(obj, mode, key_hint)

        # 数字、布尔、None 默认保留；如字段名显示为 secret，上方已处理。
        return copy.deepcopy(obj)

    return walk(data)


def redact_sensitive_fields(data: Any, mode: str = "masked_default") -> Any:
    """Alias for mask_sensitive(), used by older examples."""
    return mask_sensitive(data, mode=mode)
```

## Usage: event detail output

```python
# response/result 结构需按实际 OpenAPI 返回调整；此处为 reference implementation 示例。
detail = response.result.get("eventDetail", {})
safe_detail = mask_sensitive(detail, mode="masked_default")

print(f"Event ID: {safe_detail.get('eventId')}")
print(f"Action: {safe_detail.get('eventName')}")
print(f"Request Params: {safe_detail.get('requestParameters', {})}")
print(f"Response Elements: {safe_detail.get('responseElements', {})}")
```

## Usage: Elasticsearch / Splunk export

```python
# 外部导出必须先完成安全审批；导出的对象使用 masked_default 或 forensic_sealed。
safe_event = redact_sensitive_fields(event, mode="masked_default")

elasticsearch_doc = {
    "event_id": safe_event.get("eventId"),
    "timestamp": safe_event.get("eventTime"),
    "user": safe_event.get("username"),
    "source_ip": safe_event.get("sourceIpAddress"),
    "resource_id": safe_event.get("resourceId"),
    "request": safe_event.get("requestParameters", {}),
    "response": safe_event.get("responseElements", {}),
}

splunk_payload = {
    "event": safe_event,
    "sourcetype": "jdcloud:audit",
    "index": "security",
}
```

## Operational guardrails

1. **GCL trace**：只保存脱敏后的 `result_excerpt`，且限制长度（建议 ≤ 2 KB）。
2. **CI log**：禁止打印 raw response；只打印 event count、requestId、eventId、masked summary。
3. **Slack / Email**：只发送 eventId、severity、masked summary、证据链接；不要发送完整事件。
4. **SIEM / 外部系统**：必须经过审批、TLS 传输、最小字段集、保留期策略和访问控制。
5. **Raw archive**：如合规要求必须保存原始归档，必须加密、最小权限、限定保留期，并记录审批人与用途。
