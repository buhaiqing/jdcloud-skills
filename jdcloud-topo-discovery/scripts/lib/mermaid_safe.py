"""Mermaid safe rendering utilities.

Provides escape functions, type-safe field extraction, and ID sanitization
for generating Mermaid diagrams from cloud resource data.

Design principles:
  R1: Type assertion — all label fields must be str; nested dicts must be
      explicitly extracted.
  R2: Character escaping — `()[]{}|"` must be escaped to HTML entities.
  R3: Line breaks — use `<br/>` not `\n` inside `[...]` labels.
  R4: Length limit — single-node labels ≤ 200 chars, truncate with "...".
  R5: ID safety — node IDs only allow `[a-zA-Z0-9_-]`, replace others.

Usage:
  from lib.mermaid_safe import mermaid_escape, mermaid_safe_label, mermaid_extract_str

  label = mermaid_safe_label(f"{name}<br/>{ip}", max_len=200)
  node_id = mermaid_safe_id(f"res_{instance_id}")
  ip = mermaid_extract_str(data, "privateIp.privateIpAddress")
"""

import re

# ── Character escape table ──
_ESCAPE_TABLE = {
    "(": "&#40;",
    ")": "&#41;",
    "[": "&#91;",
    "]": "&#93;",
    "{": "&#123;",
    "}": "&#125;",
    "|": "&#124;",
    '"': "&quot;",
}

# ── Node ID safety regex ──
_ID_SAFE_RE = re.compile(r"[^a-zA-Z0-9_-]")


def mermaid_escape(text: str) -> str:
    """Escape special characters in Mermaid node/subgraph labels.

    Characters that break Mermaid syntax inside `[...]` or `(...)` labels:
      ( ) — parsed as round node shape
      [ ] — parsed as square node shape
      { } — parsed as brace node shape
      |   — parsed as pipe/separator token
      "   — breaks quoted labels

    Also replaces literal `\\n` with `<br/>` for line breaks.

    Args:
        text: Raw label text, may contain special characters.

    Returns:
        Escaped text safe for use in Mermaid labels.

    Examples:
        >>> mermaid_escape("丹东鹏飞 (vpc-xxx)")
        '丹东鹏飞 &#40;vpc-xxx&#41;'
        >>> mermaid_escape("App | 10.0.0.0/24")
        'App &#124; 10.0.0.0/24'
    """
    text = str(text)
    text = text.replace("\\n", "<br/>")
    for char, entity in _ESCAPE_TABLE.items():
        text = text.replace(char, entity)
    return text


def mermaid_safe_id(text: str) -> str:
    """Generate a safe Mermaid node ID.

    Only allows `[a-zA-Z0-9_-]`; all other characters are replaced with `_`.

    Args:
        text: Raw ID text (e.g., instance ID, subnet ID).

    Returns:
        Safe node ID string.

    Examples:
        >>> mermaid_safe_id("res_alb-z5aeeqhdtj")
        'res_alb-z5aeeqhdtj'
        >>> mermaid_safe_id("res_redis-jq8j5c6slnfd")
        'res_redis-jq8j5c6slnfd'
    """
    return _ID_SAFE_RE.sub("_", str(text))


def mermaid_safe_label(text: str, max_len: int = 200) -> str:
    """Generate a safe Mermaid node label.

    Escapes special characters and truncates to max_len if needed.
    Appends "..." when truncated.

    Args:
        text: Raw label text.
        max_len: Maximum label length in characters (default 200).

    Returns:
        Safe label string.

    Examples:
        >>> mermaid_safe_label("✅ my-app<br/>10.0.0.1")
        '✅ my-app<br/>10.0.0.1'
    """
    escaped = mermaid_escape(text)
    if len(escaped) > max_len:
        escaped = escaped[: max_len - 3] + "..."
    return escaped


def mermaid_extract_str(data, field_path: str, default: str = "") -> str:
    """Safely extract a string value from a potentially nested dict.

    Handles the common case where JD Cloud API responses return nested
    objects (e.g., ``privateIp: {privateIpAddress: "..."}``) instead of
    flat strings.

    Args:
        data: Source dict (may contain nested dicts).
        field_path: Dot-separated path, e.g. "privateIp.privateIpAddress".
        default: Fallback value if path not found or value is not a string.

    Returns:
        Extracted string value or default.

    Examples:
        >>> mermaid_extract_str({"privateIp": {"privateIpAddress": "10.0.0.1"}}, "privateIp.privateIpAddress")
        '10.0.0.1'
        >>> mermaid_extract_str({"privateIp": {"privateIpAddress": "10.0.0.1"}}, "privateIp")
        ''
        >>> mermaid_extract_str({}, "missing.field", "N/A")
        'N/A'
    """
    keys = field_path.split(".")
    value = data
    for key in keys:
        if isinstance(value, dict):
            value = value.get(key)
        else:
            return default
    if isinstance(value, str):
        return value
    return default


def mermaid_safe_subgraph_label(name: str, cidr: str = "", az: str = "") -> str:
    """Generate a safe subgraph label from subnet metadata.

    Format: ``name | cidr`` or ``name | cidr ~ az``.

    Args:
        name: Subnet name.
        cidr: Subnet CIDR block (optional).
        az: Availability zone (optional).

    Returns:
        Safe subgraph label string.

    Examples:
        >>> mermaid_safe_subgraph_label("鹏飞-应用生产", "172.21.14.32/27")
        '鹏飞-应用生产 &#124; 172.21.14.32/27'
    """
    parts = [name]
    if cidr:
        parts.append(cidr)
    if az:
        parts.append(f"~ {az}")
    return mermaid_escape(" | ".join(parts))


def mermaid_safe_vpc_label(vpc_name: str, vpc_id: str) -> str:
    """Generate a safe VPC subgraph label.

    Format: ``vpc_name (vpc_id)``

    Args:
        vpc_name: VPC display name.
        vpc_id: VPC resource ID.

    Returns:
        Safe VPC label string.

    Examples:
        >>> mermaid_safe_vpc_label("丹东鹏飞", "vpc-24lk5go6oj")
        '丹东鹏飞 &#40;vpc-24lk5go6oj&#41;'
    """
    return mermaid_escape(f"{vpc_name} ({vpc_id})")
