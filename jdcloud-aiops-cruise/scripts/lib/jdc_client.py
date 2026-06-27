"""
jdcloud-aiops-cruise / lib / jdc_client.py
========================================
Unified JD Cloud API client.

Design decisions (learned from experience):
- Uses urllib + manual JDCLOUD3-HMAC-SHA256 signing directly.
  Does NOT rely on jdcloud_sdk client classes (too many version compatibility issues).
- Handles auto-pagination, retry with backoff, and unified error handling.
- Supports all services needed for aiops-cruise: vm, lb, redis, mongodb, vpc, kubernetes, monitor.

Usage:
    from lib.jdc_client import JdcClient
    client = JdcClient(ak="...", sk="...", region="cn-north-1")
    vms = client.list_vms(tag_key="客户", tag_value="烟台振华")
    metrics = client.get_metric("i-xxx", "cpu_util", hours=6)
"""

import json
import os
import time
import hashlib
import hmac
import urllib.parse
import urllib.request
import urllib.error
from datetime import datetime, timezone, timedelta
from pathlib import Path

# ──────────────────────────────────────────────
#  Service → API endpoint mapping
# ──────────────────────────────────────────────

SERVICE_ENDPOINTS = {
    "vm":          "vm.jdcloud-api.com",
    "lb":          "lb.jdcloud-api.com",
    "redis":       "redis.jdcloud-api.com",
    "rds":         "rds.jdcloud-api.com",
    "vpc":         "vpc.jdcloud-api.com",
    "monitor":     "monitor.jdcloud-api.com",
    "kubernetes":  "kubernetes.jdcloud-api.com",
    "disk":        "disk.jdcloud-api.com",
    "es":          "es.jdcloud-api.com",
    "mongodb":     "mongodb.jdcloud-api.com",
    "nc":          "nc.jdcloud-api.com",
}

# ──────────────────────────────────────────────
#  Credential resolution
# ──────────────────────────────────────────────

def resolve_credentials(ak: str | None = None, sk: str | None = None) -> tuple[str, str]:
    """Resolve AK/SK from params, env vars, or .env file. Returns (ak, sk)."""
    if ak and sk:
        return ak, sk
    for src in [os.environ, _load_dotenv()]:
        env_ak = src.get("JDC_ACCESS_KEY") or src.get("JDCLOUD_ACCESS_KEY")
        env_sk = src.get("JDC_SECRET_KEY") or src.get("JDCLOUD_SECRET_KEY")
        if env_ak and env_sk:
            return env_ak, env_sk
    raise RuntimeError(
        "No JD Cloud credentials. Set JDC_ACCESS_KEY / JDC_SECRET_KEY"
    )

def _load_dotenv() -> dict:
    """Load .env file. Honors JDC_DOTENV_PATH, then walks up from this file."""
    env_path = os.environ.get("JDC_DOTENV_PATH")
    if not env_path:
        start_dir = Path(__file__).resolve().parent
        env_path = _find_dotenv(start_dir)
    result = {}
    if env_path and os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                result[k.strip()] = v.strip().strip("\"'")
    return result


def _find_dotenv(start_dir: Path) -> str | None:
    """Walk upward from start_dir looking for a .env file."""
    cur = start_dir
    visited = set()
    while cur and cur not in visited:
        visited.add(cur)
        candidate = cur / ".env"
        if candidate.exists():
            return str(candidate)
        # Stop at filesystem root or a directory that looks like a repo root
        if cur.parent == cur or (cur / ".git").exists():
            break
        cur = cur.parent
    return None

# ──────────────────────────────────────────────
#  JDCLOUD3-HMAC-SHA256 signing helpers
# ──────────────────────────────────────────────

def _hmac(key: bytes, msg: str) -> bytes:
    return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()

def _signing_key(sk: str, date_stamp: str, region: str, service: str) -> bytes:
    """Derive signing key matching jdcloud_sdk exactly.

    kDate     = HMAC("JDCLOUD3" + sk, date_stamp)
    kRegion   = HMAC(kDate, region)
    kService  = HMAC(kRegion, service)
    kSigning  = HMAC(kService, "jdcloud3_request")
    """
    k_date = _hmac(("JDCLOUD3" + sk).encode("utf-8"), date_stamp)
    k_region = _hmac(k_date, region)
    k_service = _hmac(k_region, service)
    return _hmac(k_service, "jdcloud3_request")

def _resolve_cred_scope_region(uri: str, region: str) -> str:
    """Credential scope's region field.

    - URI has /regions/{id}/ → use actual region name
    - Otherwise             → use 'jdcloud-api' (generic service group)
    """
    return region if "/regions/" in uri else "jdcloud-api"

def _canonical_path(uri: str) -> str:
    """Normalize URI path: unquote → collapse slashes → requote (safe='/~')."""
    decoded = urllib.parse.unquote_plus(uri)
    collapsed = __import__("re").sub(r"/+", "/", decoded)
    if not collapsed.startswith("/"):
        collapsed = "/" + collapsed
    return urllib.parse.quote(collapsed, safe="/~")

def _canonical_qs(params: dict) -> str:
    """Build canonical query string matching jdcloud_sdk.

    For each param: URL-decode(key) → URL-encode(safe='~'), same for value.
    Sort by key. Skip empty keys.
    """
    if not params:
        return ""
    pairs = []
    for k in sorted(params.keys()):
        v = params[k]
        if v is None:
            continue
        k_enc = urllib.parse.quote(urllib.parse.unquote_plus(str(k)), safe="~")
        v_enc = urllib.parse.quote(urllib.parse.unquote_plus(str(v)), safe="~")
        pairs.append(f"{k_enc}={v_enc}")
    return "&".join(pairs)

def _signed_headers(ak: str, sk: str, region: str, service: str,
                    date_stamp: str, amz_date: str, path: str,
                    qs: str, payload: str = "") -> dict:
    """Compute JDCLOUD3-HMAC-SHA256 signed headers."""
    payload_hash = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    host = SERVICE_ENDPOINTS[service]

    canonical_uri = _canonical_path(path)
    canonical_qs_str = _canonical_qs(qs) if isinstance(qs, dict) else qs
    signed_headers_str = "content-type;host"
    canonical_headers = f"content-type:application/json\nhost:{host}\n"

    canonical_request = (
        f"GET\n{canonical_uri}\n{canonical_qs_str}\n"
        f"{canonical_headers}\n{signed_headers_str}\n{payload_hash}"
    )

    cred_scope_region = _resolve_cred_scope_region(canonical_uri, region)
    cred_scope = f"{date_stamp}/{cred_scope_region}/{service}/jdcloud3_request"
    string_to_sign = (
        f"JDCLOUD3-HMAC-SHA256\n{amz_date}\n{cred_scope}\n"
        f"{hashlib.sha256(canonical_request.encode('utf-8')).hexdigest()}"
    )

    signing_key = _signing_key(sk, date_stamp, cred_scope_region, service)
    signature = hmac.new(signing_key, string_to_sign.encode("utf-8"),
                         hashlib.sha256).hexdigest()

    authorization = (
        f"JDCLOUD3-HMAC-SHA256 Credential={ak}/{cred_scope}, "
        f"SignedHeaders={signed_headers_str}, Signature={signature}"
    )

    return {
        "Content-Type": "application/json",
        "Host": host,
        "Authorization": authorization,
        "x-jdcloud-date": amz_date,
        "x-jdcloud-content-sha256": payload_hash,
        "x-jdcloud-nonce": os.urandom(16).hex(),
        "User-Agent": "JdcLinkCruise/1.0",
    }

# ──────────────────────────────────────────────
#  Main client
# ──────────────────────────────────────────────

class JdcClient:
    """Unified JD Cloud API client with auto-pagination and retry."""

    MAX_RETRIES = 3
    RETRY_BACKOFF = [0, 2, 4]  # seconds

    def __init__(self, ak: str = None, sk: str = None, region: str = "cn-north-1"):
        self.ak, self.sk = resolve_credentials(ak, sk)
        self.region = region

    # ── Low-level: signed GET with retry ──

    def _get(self, service: str, path: str, params: dict = None,
             page_number: int = None, page_size: int = 100) -> dict:
        """Execute a signed GET; returns parsed JSON dict."""
        if params is None:
            params = {}
        if page_number is not None:
            params["pageNumber"] = page_number
            params["pageSize"] = page_size

        now = datetime.now(timezone.utc)
        date_stamp = now.strftime("%Y%m%d")
        amz_date = now.strftime("%Y%m%dT%H%M%SZ")

        headers = _signed_headers(
            self.ak, self.sk, self.region, service,
            date_stamp, amz_date, path, params,
        )
        qs = _canonical_qs(params)
        url = f"https://{SERVICE_ENDPOINTS[service]}{_canonical_path(path)}"
        if qs:
            url += f"?{qs}"

        last_err = None
        for attempt in range(self.MAX_RETRIES):
            try:
                if attempt > 0:
                    time.sleep(self.RETRY_BACKOFF[attempt])
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req, timeout=30) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                if "error" in data and data["error"]:
                    err = data["error"]
                    code = err.get("code", 0)
                    msg = err.get("message", str(err))
                    if 400 <= code < 500 and code != 429:
                        raise RuntimeError(f"API {code}: {msg}")
                    last_err = RuntimeError(f"API {code}: {msg} (attempt {attempt+1})")
                    continue
                return data
            except urllib.error.HTTPError as e:
                body = e.read().decode("utf-8", errors="replace")
                last_err = RuntimeError(f"HTTP {e.code}: {body[:200]}")
                if e.code < 500 and e.code != 429:
                    raise last_err
            except (urllib.error.URLError, OSError) as e:
                last_err = RuntimeError(f"Network: {e}")
        raise last_err or RuntimeError("Max retries")

    # ── Auto-pagination wrapper ──

    def _paginate(self, service: str, path: str, params: dict | None = None,
                  page_size: int = 100, result_path: str | None = None) -> list:
        """Auto-paginated GET. result_path is dot-separated e.g. 'instances'."""
        all_items, page = [], 1
        while True:
            data = self._get(service, path, params, page, page_size)
            result = data.get("result", {})

            if result_path:
                items = result
                for key in result_path.split("."):
                    items = items.get(key, []) if isinstance(items, dict) else []
            else:
                items = next((v for v in result.values() if isinstance(v, list)), [])

            if not items:
                break
            all_items.extend(items)
            total = result.get("totalCount", 0)
            if total > 0 and len(all_items) >= total:
                break
            if len(items) < page_size:
                break
            page += 1
        return all_items

    # ── Resource listing APIs ──

    def list_vms(self, region: str | None = None, tag_key: str | None = None,
                 tag_value: str | None = None) -> list:
        """List VMs. If tag_key/value provided, filter locally (more reliable)."""
        r = region or self.region
        vms = self._paginate("vm", f"/v1/regions/{r}/instances",
                              result_path="instances")
        if tag_key and tag_value:
            vms = [vm for vm in vms
                   if any(t.get("key") == tag_key and t.get("value") == tag_value
                          for t in vm.get("tags", []))]
        return vms

    def list_lbs(self, region: str | None = None) -> list:
        r = region or self.region
        return self._paginate("lb", f"/v1/regions/{r}/loadBalancers",
                               result_path="loadBalancers")

    def list_redis(self, region: str | None = None) -> list:
        r = region or self.region
        return self._paginate("redis", f"/v1/regions/{r}/cacheInstance",
                               result_path="cacheInstances")

    def list_rds(self, region: str | None = None) -> list:
        """List RDS MySQL instances."""
        r = region or self.region
        return self._paginate("rds", f"/v1/regions/{r}/instances",
                               result_path="dbInstances")

    def list_vpcs(self, region: str | None = None) -> list:
        r = region or self.region
        return self._paginate("vpc", f"/v1/regions/{r}/vpcs",
                               result_path="vpcs")

    def list_subnets(self, region: str | None = None) -> list:
        r = region or self.region
        return self._paginate("vpc", f"/v1/regions/{r}/subnets",
                               result_path="subnets")

    def list_security_groups(self, region: str | None = None) -> list:
        r = region or self.region
        return self._paginate("vpc", f"/v1/regions/{r}/securityGroups",
                               result_path="securityGroups")

    def list_clusters(self, region: str | None = None) -> list:
        r = region or self.region
        return self._paginate("kubernetes", f"/v1/regions/{r}/clusters",
                               result_path="clusters")

    def list_disks(self, region: str | None = None) -> list:
        r = region or self.region
        return self._paginate("disk", f"/v1/regions/{r}/disks",
                               result_path="disks")

    def list_es(self, region: str | None = None) -> list:
        r = region or self.region
        return self._paginate("es", f"/v1/regions/{r}/instances",
                               result_path="instances")

    def list_mongodb(self, region: str | None = None) -> list:
        """List MongoDB instances (read-only)."""
        r = region or self.region
        return self._paginate("mongodb", f"/v1/regions/{r}/instances",
                              result_path="instances")

    def list_eips(self, region: str | None = None) -> list:
        """List Elastic IPs (read-only)."""
        r = region or self.region
        return self._paginate("vpc", f"/v1/regions/{r}/elasticIps",
                              result_path="elasticIps")

    # ── Monitor / Metrics ──

    def get_metric(self, resource_id: str, metric: str,
                   hours: int = 6, aggr: str = "avg",
                   region: str | None = None, service_code: str = "vm") -> list:
        """Query metric for a resource. Returns [(ts_ms, value), ...].

        service_code is the JD Cloud Monitor service code of the target resource
        (for example: vm, lb, redis, eip, nat, es). It is intentionally explicit
        so non-VM analyzers do not accidentally query Monitor with serviceCode=vm.
        """
        r = region or self.region
        end = datetime.now(timezone.utc)
        start = end - timedelta(hours=hours)

        params = {
            "serviceCode": service_code,
            "resourceId": resource_id,
            "startTime": start.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "endTime": end.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "timeInterval": "1h",
            "aggrType": aggr,
        }

        path = f"/v2/regions/{r}/metrics/{metric}/metricData"
        data = self._get("monitor", path, params)
        md_list = data.get("result", {}).get("metricDatas", [])
        if not md_list:
            return []
        pts = md_list[0].get("data", [])
        return [(p["timestamp"], float(p["value"])) for p in pts]

    def get_metrics_batch(self, resource_id: str, metrics: list,
                           hours: int = 6, aggr: str = "avg",
                           region: str | None = None, service_code: str = "vm") -> dict:
        """Query multiple metrics. Returns {metric_name: [(ts, val)]}."""
        result = {}
        for m in metrics:
            try:
                pts = self.get_metric(resource_id, m, hours, aggr, region, service_code)
                if pts:
                    result[m] = pts
            except Exception:
                continue
        return result

    def get_alarm_history(self, resource_id: str, hours: int = 6,
                          region: str | None = None) -> list:
        """Query alarm history for a resource. Best-effort."""
        r = region or self.region
        end2 = datetime.now(timezone.utc)
        start2 = end2 - timedelta(hours=hours)
        params = {
            "resourceId": resource_id,
            "startTime": start2.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "endTime": end2.strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
        try:
            data = self._get("monitor", f"/v1/regions/{r}/alarmHistory", params)
            return data.get("result", {}).get("alarmHistoryList", [])
        except Exception:
            return []

# ──────────────────────────────────────────────
#  Utility functions
# ──────────────────────────────────────────────

def filter_by_tag(resources: list[dict], key: str, value: str) -> list[dict]:
    return [r for r in resources
            if any(t.get("key") == key and t.get("value") == value
                   for t in r.get("tags", []))]

def tag_dict(resource: dict) -> dict[str, str]:
    return {t["key"]: t["value"] for t in resource.get("tags", [])}

def get_tag(resource: dict, key: str) -> str | None:
    for t in resource.get("tags", []):
        if t.get("key") == key:
            return t.get("value")
    return None
