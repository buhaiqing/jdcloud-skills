#!/usr/bin/env python3
"""OSS backend for baseline management.

Stores baselines as OSS objects under {prefix}/{YYYY-MM-DD}/.
Uses `jdc` CLI for OSS operations (no oss2 SDK dependency).
Falls back to env vars JDC_ACCESS_KEY / JDC_SECRET_KEY for auth.

> Mirrors alicloud-topo-discovery baseline_oss.py, adapted for JD Cloud.
"""
import json
import mimetypes
import os
import subprocess
from datetime import date
from pathlib import Path
from typing import List, Optional


class OSSBackend:
    """Manages baselines via JD Cloud OSS object storage.

    Relies on `jdc oss` CLI for OSS operations (no oss2 SDK dependency).
    Falls back to JDC_ACCESS_KEY/JDC_SECRET_KEY env vars.

    Bucket name format: arbitrary, but the bucket MUST already exist
    (no automatic bucket creation — that would be a write op).
    """

    def __init__(
        self,
        bucket: str,
        prefix: str = "baselines/",
        endpoint: Optional[str] = None,
        ak_id: Optional[str] = None,
        ak_secret: Optional[str] = None,
    ):
        if not bucket:
            raise ValueError("bucket must be non-empty")
        self.bucket = bucket
        self.prefix = prefix.rstrip("/") + "/"
        self.endpoint = endpoint or os.environ.get("OSS_ENDPOINT", "oss-cn-north-1.jdcloud-oss.com")
        self.ak_id = ak_id or os.environ.get("JDC_ACCESS_KEY", "")
        self.ak_secret = ak_secret or os.environ.get("JDC_SECRET_KEY", "")
        if not self.ak_id:
            raise ValueError("OSS AK ID not provided and not found in env vars")

    def write_baseline(self, snapshot: Path) -> str:
        """Upload snapshot files to OSS under {prefix}{YYYY-MM-DD}/.

        Returns the object key prefix.
        """
        today = date.today().isoformat()
        key_prefix = f"{self.prefix}{today}/"

        # Upload each file using jdc oss
        for fpath in sorted(snapshot.rglob("*")):
            if fpath.is_file():
                rel = fpath.relative_to(snapshot)
                object_key = f"{key_prefix}{rel}"
                self._upload_file(str(fpath), object_key)

        # Write manifest.json last (atomicity signal)
        manifest_path = snapshot / "manifest.json"
        if manifest_path.exists():
            self._upload_file(str(manifest_path), f"{key_prefix}manifest.json")

        return key_prefix

    def list_baselines(self) -> List[date]:
        """List baseline dates from OSS prefix."""
        if not self._bucket_exists():
            return []

        objects = self._list_objects(prefix=self.prefix, delimiter="/")
        dates = []
        for obj in objects:
            # Extract date from prefix: baselines/2026-06-08/ -> 2026-06-08
            rel = obj.replace(self.prefix, "").rstrip("/")
            try:
                dates.append(date.fromisoformat(rel))
            except (ValueError, TypeError):
                continue
        return sorted(dates)

    def _upload_file(self, local_path: str, object_key: str) -> None:
        """Upload a single file to OSS using `jdc oss`."""
        content_type, _ = mimetypes.guess_type(local_path)
        # jdc CLI reads creds from ~/.jdc/config — set HOME for sandbox
        cmd = [
            "jdc", "oss", "cp",
            local_path,
            f"oss://{self.bucket}/{object_key}",
            "--force",
        ]
        if content_type:
            cmd.extend(["--content-type", content_type])
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.returncode != 0:
            raise RuntimeError(f"OSS upload failed for {object_key}: {result.stderr}")

    def _list_objects(self, prefix: str, delimiter: str = "/") -> List[str]:
        """List OSS objects with given prefix, returning common prefixes."""
        result = subprocess.run(
            ["jdc", "oss", "ls", f"oss://{self.bucket}/{prefix}", "-d", delimiter],
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode != 0:
            return []
        # Parse jdc oss ls output: "<date> <time> <size> <url>"
        prefixes = []
        for line in result.stdout.strip().split("\n"):
            line = line.strip()
            if line and "oss://" in line:
                parts = line.split()
                if len(parts) >= 4:
                    prefixes.append(parts[-1].replace(f"oss://{self.bucket}/", ""))
        return prefixes

    def _bucket_exists(self) -> bool:
        result = subprocess.run(
            ["jdc", "oss", "ls", f"oss://{self.bucket}/"],
            capture_output=True, text=True, timeout=30,
        )
        return result.returncode == 0
