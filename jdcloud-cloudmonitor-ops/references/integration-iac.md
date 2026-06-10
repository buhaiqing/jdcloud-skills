# 集成指南 — Terraform & CI/CD

> 本文档从 `integration.md` 提取。

## Terraform 集成

### 配置 Provider

```hcl
provider "jdcloud" {
  access_key = var.access_key
  secret_key = var.secret_key
  region     = "cn-north-1"
}
```

### 创建告警规则

```hcl
resource "jdcloud_monitor_alarm" "high_cpu" {
  region_id           = "cn-north-1"
  alarm_name          = "HighCPUAlarm"
  service_code        = "vm"
  resource_id         = "i-xxx"
  metric_name         = "vm.cpu.util"
  comparison_operator = "gt"
  threshold           = 80
  period              = 300
  evaluation_periods  = 2
  contact_group_id    = 1
  notice_type         = "sms,email"
}
```

## CI/CD 集成

### GitHub Actions 示例

```yaml
name: Monitor Deployment

on:
  deployment:
    environments: [production]

jobs:
  monitor:
    runs-on: ubuntu-latest
    steps:
      - name: Setup JDCloud CLI
        run: |
          pip install jdcloud_cli
          jdc config init --access-key ${{ secrets.JDC_ACCESS_KEY }} --secret-key ${{ secrets.JDC_SECRET_KEY }} --region cn-north-1
      
      - name: Check Resource Status
        run: |
          jdc monitor last-downsample \
            --region-id cn-north-1 \
            --service-code vm \
            --resource-id ${{ secrets.VM_RESOURCE_ID }} \
            --metrics '["vm.cpu.util","vm.memory.util"]'
      
      - name: Create Temporary Alarm
        run: |
          jdc monitor create-alarm \
            --region-id cn-north-1 \
            --alarm-name "Deploy-Monitor-${{ github.run_id }}" \
            --service-code vm \
            --resource-id ${{ secrets.VM_RESOURCE_ID }} \
            --metric-name "vm.cpu.util" \
            --comparison-operator "gt" \
            --threshold 70 \
            --period 60 \
            --evaluation-periods 1 \
            --notice-type "callback" \
            --callback-url "${{ secrets.WEBHOOK_URL }}"
```

### Jenkins Pipeline 示例

```groovy
pipeline {
    agent any
    
    environment {
        JDC_ACCESS_KEY = credentials('jdc-access-key')
        JDC_SECRET_KEY = credentials('jdc-secret-key')
    }
    
    stages {
        stage('Monitor Check') {
            steps {
                script {
                    sh '''
                        pip install jdcloud_cli
                        export JDC_ACCESS_KEY=$JDC_ACCESS_KEY
                        export JDC_SECRET_KEY=$JDC_SECRET_KEY
                        
                        jdc monitor describe-metric-data \
                            --region-id cn-north-1 \
                            --metric vm.cpu.util \
                            --service-code vm \
                            --resource-id i-xxx \
                            --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%SZ) \
                            --end-time $(date -u +%Y-%m-%dT%H:%M:%SZ)
                    '''
                }
            }
        }
    }
}
```
