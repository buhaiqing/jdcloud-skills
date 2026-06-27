"""JSON → HCL conversion engine for JD Cloud resource exports.

Consumes raw `jdc --output json` responses and produces HCL `resource` blocks
using MappingSpec definitions. Integrates with SensitiveMasker for secure
handling of password/key fields.

> **Note**: JD Cloud has no official Terraform provider. The generated HCL
> is **documentation only** and cannot be applied with `terraform apply`.

Architecture:
    MappingSpec(resource_type, terraform_type, rules, parent_ref=None)
    MappingRule(hcl_attr, path, type, sensitive, required, default)
    FieldMapper.map_resource(resource_type, resource_data, spec, block_name) -> str
"""
from dataclasses import dataclass, field
from typing import Any, Optional

from scripts.lib.sensitive_masker import mask_field


@dataclass
class MappingRule:
    """Defines how a single JSON field maps to an HCL attribute."""
    hcl_attr: str
    path: str
    type: str = "string"
    sensitive: bool = False
    required: bool = True
    default: Any = None


@dataclass
class MappingSpec:
    """Defines a complete resource type mapping."""
    resource_type: str
    terraform_type: str
    rules: list = field(default_factory=list)
    parent_ref: Optional[str] = None


class FieldMapper:
    """Converts JD Cloud `describe-*` API JSON responses into HCL resource blocks.

    Usage:
        mapper = FieldMapper()
        hcl = mapper.map_resource(
            resource_type="vpc",
            resource_data={"vpcName": "prod", "addressPrefix": "10.0.0.0/16"},
            spec=MappingSpec("vpc", "jdcloud_vpc", rules=[...]),
            block_name="prod_vpc"
        )
    """

    def map_resource(
        self,
        resource_type: str,
        resource_data: dict,
        spec: MappingSpec,
        block_name: str,
    ) -> str:
        """Map a single resource's JSON data to an HCL resource block.

        Returns a string like:
            resource "jdcloud_vpc" "prod_vpc" {
              vpc_name = "prod"
              cidr_block = "10.0.0.0/16"
            }
        """
        lines = [f'resource "{spec.terraform_type}" "{block_name}" {{']

        for rule in spec.rules:
            raw_value = self._resolve_path(resource_data, rule.path)
            if raw_value is None:
                if rule.default is not None:
                    raw_value = rule.default
                elif rule.required:
                    # Skip missing required fields (caller reviews output)
                    continue
                else:
                    continue

            if rule.sensitive:
                api_field_name = rule.path.split(".")[-1]
                var_ref = mask_field(resource_type, api_field_name, raw_value)[0]
                hcl_value = var_ref if isinstance(var_ref, str) else self._format_value(var_ref, rule.type)
                lines.append(f"  {rule.hcl_attr} = {hcl_value}")
                lines.append("  sensitive = true")
            else:
                hcl_value = self._format_value(raw_value, rule.type)
                lines.append(f"  {rule.hcl_attr} = {hcl_value}")

        lines.append("}")
        return "\n".join(lines)

    @staticmethod
    def _resolve_path(data: dict, path: str) -> Any:
        """Resolve a dotted JSON path like 'vpcName' or 'securityGroupRules[*].ruleId'.

        Simple dot notation only (no wildcards in Phase 1).
        Returns None if any intermediate key is missing.
        """
        parts = path.split(".")
        current = data
        for part in parts:
            if current is None:
                return None
            if isinstance(current, dict):
                current = current.get(part)
            elif isinstance(current, list):
                # Handle list-of-dicts: collect values
                try:
                    current = [item.get(part) if isinstance(item, dict) else None for item in current]
                    current = [v for v in current if v is not None]
                    if not current:
                        return None
                    return current[0] if len(current) == 1 else current
                except (AttributeError, IndexError):
                    return None
            else:
                return None
        return current

    @staticmethod
    def _format_value(value: Any, type_hint: str) -> str:
        """Format a Python value as an HCL literal."""
        if value is None:
            return "null"
        if type_hint == "bool":
            return "true" if value else "false"
        if type_hint == "int":
            return str(int(value))
        if type_hint == "list":
            if isinstance(value, (list, tuple)):
                items = ", ".join(f'"{str(v)}"' for v in value)
                return f"[{items}]"
            return f'["{value}"]'
        if type_hint == "dict" and isinstance(value, dict):
            items = ", ".join(f'{k} = "{v}"' for k, v in value.items())
            return "{ " + items + " }"
        # Default: string (with quote escaping)
        escaped = str(value).replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}"'

    @staticmethod
    def generate_block_name(terraform_type: str, resource_data: dict, spec: MappingSpec) -> str:
        """Generate a stable, human-readable block name from resource data.

        Examples:
            jdcloud_vpc + {vpcName: "prod"} -> "prod"
            jdcloud_subnet + {subnetName: "app-subnet"} -> "app_subnet"
            jdcloud_instance + {instanceName: "web-01"} -> "web_01"

        Uses resource type-specific logic from MappingSpec.
        If no name field exists, falls back to ID-based slug.
        """
        name_field = _NAME_FIELDS.get(spec.resource_type, "name")
        name = resource_data.get(name_field)
        if not name:
            id_field = _ID_FIELDS.get(spec.resource_type)
            if id_field and id_field in resource_data:
                name = resource_data[id_field]
        if not name:
            name = terraform_type

        slug = _slugify(str(name))
        return slug


def _slugify(name: str) -> str:
    """Convert a resource name to a valid HCL identifier slug.

    Rules:
    - Replace non-alphanumeric with underscore
    - Collapse multiple underscores
    - Must not start with a number (prefix with 'r_' if needed)
    """
    slug = ""
    for ch in name:
        if ch.isalnum():
            slug += ch.lower()
        else:
            slug += "_"
    slug = "_".join(filter(None, slug.split("_")))
    if slug and slug[0].isdigit():
        slug = "r_" + slug
    return slug or "unnamed"


# Resource-type-specific name field mapping (describe-* API → HCL block name)
_NAME_FIELDS = {
    "vpc": "vpcName",
    "subnet": "subnetName",
    "vm": "instanceName",
    "mysql": "instanceName",
    "postgresql": "instanceName",
    "mongodb": "instanceName",
    "redis": "cacheInstanceName",
    "clb": "loadBalancerName",
    "eip": "name",
    "sg": "networkSecurityGroupName",
    "kms": "keyName",
    "iam": "subUserName",
    "ag": "name",
    "nics": "networkInterfaceName",
    "es": "instanceName",
}

# Resource-type-specific ID field mapping (describe-* API → fallback block name)
_ID_FIELDS = {
    "vpc": "vpcId",
    "subnet": "subnetId",
    "vm": "instanceId",
    "mysql": "instanceId",
    "postgresql": "instanceId",
    "mongodb": "instanceId",
    "redis": "cacheInstanceId",
    "clb": "loadBalancerId",
    "eip": "elasticIpId",
    "sg": "networkSecurityGroupId",
    "kms": "keyId",
    "iam": "subUserName",  # IAM uses name as primary ID
    "ag": "agId",
    "nics": "networkInterfaceId",
    "es": "instanceId",
}
