"""Mask sensitive fields in resource JSON before HCL generation.

Phase 1 covers: MySQL AccountPassword, IAM AccessKey
(only fields that appear in `describe-*` responses for Top-10 types).

For each sensitive field:
- Replace value with `${var.<field_name>}` variable reference
- Track field path in returned tuple (for manifest logging)
- In HCL output, append `sensitive = true` directive

Security principle: NEVER log or return the original sensitive value.
"""
from typing import Optional, Tuple


# Resource type -> field name (lowercase) -> HCL variable name
SENSITIVE_FIELDS: dict = {
    "mysql": {"accountpassword": "mysql_password"},
    "postgresql": {"accountpassword": "postgresql_password"},
    "mongodb": {"accountpassword": "mongodb_password"},
    "redis": {"password": "redis_password"},
    "iam": {"accesskeyid": "iam_access_key_id", "accesskey": "iam_access_key_id"},
}


def mask_field(resource_type: str, field_name: str, value) -> Tuple[object, Optional[str]]:
    """Mask a single field value if it's sensitive.

    Returns (masked_value, field_path_or_None).
    If sensitive: (var_ref_string, dotted_path); else: (original_value, None).
    """
    rt_fields = SENSITIVE_FIELDS.get(resource_type.lower(), {})
    var_name = rt_fields.get(field_name.lower())
    if var_name is None:
        return value, None
    return f"${{var.{var_name}}}", _field_path(resource_type, field_name)


def _field_path(resource_type: str, field_name: str) -> str:
    snake = "".join("_" + c.lower() if c.isupper() else c.lower() for c in field_name).lstrip("_")
    return f"{resource_type.lower()}.{snake}"