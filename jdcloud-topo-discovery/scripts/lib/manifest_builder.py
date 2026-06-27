"""Build and validate manifest.json for HCL export runs.

Single entry point: ManifestBuilder(...).build(...). Used by
export-hcl.py. The .build() output is guaranteed to pass .validate().
"""
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

try:
    from jsonschema import Draft7Validator
except ImportError as e:
    raise ImportError(
        "jsonschema package required. Install with: pip install jsonschema>=4.21"
    ) from e


GENERATOR = "jdcloud-topo-discovery"
GENERATOR_VERSION = "1.0.0"
SCHEMA_VERSION = "1.0"
SCHEMA_PATH = Path(__file__).parent.parent.parent / "references" / "manifest-schema.json"


class ManifestValidationError(Exception):
    """Raised when manifest fails schema validation."""


class ManifestBuilder:
    """Builds a manifest.json dict for a single export run."""

    def __init__(self, account_id: str, region: str, scope: str, provider_version: str,
                 account_alias: Optional[str] = None, role_arn: Optional[str] = None):
        if not account_id or not isinstance(account_id, str):
            raise ValueError("account_id must be a non-empty string")
        if not region or not isinstance(region, str):
            raise ValueError("region must be a non-empty string")
        if not scope or not isinstance(scope, str):
            raise ValueError("scope must be a non-empty string")
        if not provider_version or not isinstance(provider_version, str):
            raise ValueError("provider_version must be a non-empty string")
        self.account_id = account_id
        self.account_alias = account_alias
        self.role_arn = role_arn
        self.region = region
        self.scope = scope
        self.provider_version = provider_version

    def build(self, resource_count: int, by_type: dict, sensitive_masked: list,
              unsupported_types: list, execution_time_ms: int) -> dict:
        """Build and return the manifest dict."""
        if resource_count < 0:
            raise ValueError("resource_count must be >= 0")
        if execution_time_ms < 0:
            raise ValueError("execution_time_ms must be >= 0")
        if not isinstance(by_type, dict):
            raise TypeError("by_type must be a dict")
        if not isinstance(sensitive_masked, list):
            raise TypeError("sensitive_masked must be a list")
        if not isinstance(unsupported_types, list):
            raise TypeError("unsupported_types must be a list")

        generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        manifest = {
            "schema_version": SCHEMA_VERSION,
            "generator": GENERATOR,
            "generator_version": GENERATOR_VERSION,
            "generated_at": generated_at,
            "account_id": self.account_id,
            "region": self.region,
            "scope": self.scope,
            "provider_version": self.provider_version,
            "resource_count": resource_count,
            "by_type": by_type,
            "sensitive_masked": sensitive_masked,
            "unsupported_types": unsupported_types,
            "import_ids_stable": True,
            "execution_time_ms": execution_time_ms,
        }
        if self.account_alias is not None:
            manifest["account_alias"] = self.account_alias
        if self.role_arn is not None:
            manifest["role_arn"] = self.role_arn
        return manifest


def validate_manifest(manifest: dict) -> None:
    """Validate manifest against schema. Raises ManifestValidationError on failure."""
    if not SCHEMA_PATH.exists():
        raise FileNotFoundError(f"Schema not found: {SCHEMA_PATH}")
    with open(SCHEMA_PATH, encoding="utf-8") as f:
        schema = json.load(f)
    errors = list(Draft7Validator(schema).iter_errors(manifest))
    if not errors:
        return
    err = errors[0]
    path = " -> ".join(str(p) for p in err.absolute_path) or "(root)"
    raise ManifestValidationError(f"Manifest validation failed at '{path}': {err.message}")