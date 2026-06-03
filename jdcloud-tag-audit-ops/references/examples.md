# Examples

## Example 1: Basic Audit

```bash
# Audit all products in all regions
./audit.sh --regions all --products all
```

**Output:**
```
## Tag Compliance Audit Report
### Summary
- Total resources scanned: 200
- Non-compliant resources: 35
- Compliance rate: 82.5%

### Non-compliant Resources by Product
| Product | Count |
|---------|-------|
| Redis | 8 |
| VM | 15 |
| RDS | 5 |
| CLB | 4 |
| EIP | 3 |
```

## Example 2: Targeted Audit

```bash
# Audit only Redis and CLB in specific regions
./audit.sh --regions cn-north-1,cn-east-2 --products redis,clb --tags "环境"
```

## Example 3: Create DOPS Ticket

```bash
# Audit and create DOPS ticket for non-compliant resources
./audit.sh --regions all --products all --create-ticket --operator zhoulu
```

## Example 4: JSON Output for Integration

```bash
# Get JSON output for further processing
./audit.sh --regions cn-north-1 --products vm --output json > audit_results.json
```

**JSON Output:**
```json
[
  {
    "product": "vm",
    "region": "cn-north-1",
    "id": "i-abc123",
    "name": "production-server-01",
    "missingTags": ["环境"]
  },
  {
    "product": "vm",
    "region": "cn-north-1",
    "id": "i-def456",
    "name": "test-server-01",
    "missingTags": ["环境", "客户"]
  }
]
```

## Example 5: Python Script Integration

```python
import json
from tag_audit import audit_all

# Run audit
results = audit_all(
    regions=["cn-north-1", "cn-east-2"],
    products=["redis", "vm", "clb", "eip"],
    required_tags=["环境", "客户"]
)

# Generate report
print(f"Total non-compliant resources: {len(results)}")

# Group by product
by_product = {}
for r in results:
    product = r["product"]
    by_product[product] = by_product.get(product, 0) + 1

for product, count in by_product.items():
    print(f"- {product}: {count}")

# Save to file
with open("audit_report.json", "w") as f:
    json.dump(results, f, indent=2, ensure_ascii=False)
```

## Example 6: CI/CD Integration

```yaml
# .github/workflows/tag-audit.yml
name: Tag Compliance Audit
on:
  schedule:
    - cron: '0 0 * * *'

jobs:
  audit:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v3
      
      - name: Install dependencies
        run: |
          pip install jdcloud_sdk
      
      - name: Run audit
        env:
          JDC_ACCESS_KEY: ${{ secrets.JDC_ACCESS_KEY }}
          JDC_SECRET_KEY: ${{ secrets.JDC_SECRET_KEY }}
        run: |
          python audit.py --regions all --products all
      
      - name: Create ticket if non-compliant
        if: env.NON_COMPLIANT_COUNT > 0
        run: |
          python create_ticket.py --count $NON_COMPLIANT_COUNT
```