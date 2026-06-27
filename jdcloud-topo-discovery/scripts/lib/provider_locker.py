"""Generate Terraform provider block for JD Cloud HCL export.

JD Cloud has no official Terraform Provider — generates placeholder blocks
marked "n/a" for documentation-only purposes.
"""
import re
from typing import Optional


DEFAULT_PROVIDER_VERSION = "n/a"
_PROVIDER_VERSION_RE = re.compile(r"^([0-9]+\.[0-9]+\.[0-9]+|n/a)$")
_FORBIDDEN_PATTERNS = [
    re.compile(r"JDC_[A-Z0-9]{16,}"),
    re.compile(r"jdcloud_[a-z0-9]{16,}"),
    re.compile(r'secret_key\s*=\s*"[^"]+"'),
    re.compile(r'access_key\s*=\s*"[^"]+"'),
]


def _validate_version(version: str) -> None:
    if not isinstance(version, str) or not _PROVIDER_VERSION_RE.match(version):
        raise ValueError(f"Invalid version '{version}': must be semver (e.g. '1.0.0') or 'n/a'")


def generate_provider_block(version: str = DEFAULT_PROVIDER_VERSION, region: str = "cn-north-1",
                            profile: Optional[str] = None) -> str:
    """Generate a Terraform provider block as a string."""
    _validate_version(version)
    lines = ["terraform {", "  required_providers {", '    jdcloud = {', '      source  = "jdcloud/jdcloud"', ]
    if version == "n/a":
        lines += [
            '      # NOTE: JD Cloud has NO official Terraform provider as of 2026-06.',
            "      # The HCL output by jdcloud-topo-discovery is DOCUMENTATION ONLY.",
            '      # `terraform apply` will fail with: Provider configuration not present.',
            '      # Track: https://github.com/jdcloud-api/jdcloud-terraform-provider for future releases.',
            '      version = ">= 0.0.0"  # placeholder',
        ]
    else:
        lines += [f'      version = "~> {version}"']
    lines += ["    }", "  }", "}", "", 'provider "jdcloud" {', f'  region  = "{region}"']
    if profile:
        lines.append(f'  profile = "{profile}"')
    lines += ["", "  # Credentials sourced from environment variables (NEVER hardcoded).",
              "  # Required: JDC_ACCESS_KEY, JDC_SECRET_KEY",
              "  # NOTE: jdc CLI reads from ~/.jdc/config INI file (not env vars).",
              "  #        For SDK-based providers, env vars are the source of truth.",
              "}", ""]
    block = "\n".join(lines)
    for pattern in _FORBIDDEN_PATTERNS:
        match = pattern.search(block)
        if match:
            raise ValueError(f"Security violation: generated provider block contains forbidden pattern '{match.group()}'")
    return block