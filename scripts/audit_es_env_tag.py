#!/usr/bin/env python3
"""Elasticsearch 【环境】 tag audit across all regions."""

import os
import json
import sys
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root
load_dotenv(Path(__file__).resolve().parents[1] / ".env")

from jdcloud_sdk.core.credential import Credential
from jdcloud_sdk.services.es.client.EsClient import EsClient
from jdcloud_sdk.services.es.apis.DescribeInstancesRequest import (
    DescribeInstancesRequest,
    DescribeInstancesParameters,
)

# Valid ES regions (cn-south-2 is NOT supported by ES API)
REGIONS = ["cn-north-1", "cn-east-1", "cn-east-2", "cn-south-1"]
REQUIRED_TAG = "环境"

# Pre-flight: verify credentials
ak = os.environ.get("JDC_ACCESS_KEY")
sk = os.environ.get("JDC_SECRET_KEY")
if not ak or not sk:
    print("[FATAL] JDC_ACCESS_KEY / JDC_SECRET_KEY not set in .env", file=sys.stderr)
    sys.exit(1)
print(f"[OK] Credentials loaded. JDC_ACCESS_KEY={ak[:8]}...<masked>")

credential = Credential(ak, sk)
client = EsClient(credential)  # SDK-only: no region in constructor

all_instances = []
non_compliant = []
region_summary = {}

for region in REGIONS:
    try:
        params = DescribeInstancesParameters(regionId=region)
        params.setPageNumber(1)
        params.setPageSize(100)
        resp = client.send(DescribeInstancesRequest(parameters=params))

        instances = resp.result.get("instances") or []
        region_summary[region] = {
            "total": len(instances),
            "missing_env_tag": 0,
        }

        for inst in instances:
            tags = inst.get("tags") or []
            existing_keys = [t.get("key", "") for t in tags]

            record = {
                "region": region,
                "instanceId": inst.get("instanceId", ""),
                "instanceName": inst.get("instanceName", ""),
                "instanceVersion": inst.get("instanceVersion", ""),
                "instanceStatus": inst.get("instanceStatus", ""),
                "existingTagKeys": existing_keys,
                "existingTags": [
                    {"key": t.get("key", ""), "value": t.get("value", "")}
                    for t in tags
                ],
            }
            all_instances.append(record)

            if REQUIRED_TAG not in existing_keys:
                record["missingTag"] = REQUIRED_TAG
                non_compliant.append(record)
                region_summary[region]["missing_env_tag"] += 1

        print(f"[OK] {region}: {len(instances)} instances, {region_summary[region]['missing_env_tag']} missing 【环境】")

    except Exception as e:
        print(f"[ERROR] {region}: {type(e).__name__}: {str(e)[:200]}")
        region_summary[region] = {"total": 0, "missing_env_tag": 0, "error": str(e)[:200]}

total = len(all_instances)
compliant = total - len(non_compliant)
rate = round(compliant / total * 100, 2) if total > 0 else 0

report = {
    "metadata": {
        "generatedAt": datetime.now().isoformat(),
        "product": "Elasticsearch",
        "requiredTag": REQUIRED_TAG,
        "regions": REGIONS,
    },
    "summary": {
        "totalInstances": total,
        "compliant": compliant,
        "nonCompliant": len(non_compliant),
        "complianceRate": rate,
        "byRegion": region_summary,
    },
    "nonCompliantInstances": non_compliant,
    "allInstances": all_instances,
}

# Save raw report
out_dir = Path(__file__).resolve().parents[1] / "audit-results"
out_dir.mkdir(exist_ok=True)
ts = datetime.now().strftime("%Y%m%d_%H%M%S")
out_file = out_dir / f"es_env_tag_audit_{ts}.json"
with open(out_file, "w", encoding="utf-8") as f:
    json.dump(report, f, indent=2, ensure_ascii=False)

print("\n=== ES 【环境】 Tag Compliance Audit ===")
print(f"Total instances: {total}")
print(f"Compliant:       {compliant}")
print(f"Non-compliant:   {len(non_compliant)}")
print(f"Compliance rate: {rate}%")
print(f"Report saved:    {out_file}")
