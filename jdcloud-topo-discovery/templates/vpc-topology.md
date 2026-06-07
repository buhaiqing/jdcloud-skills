# VPC 网络拓扑模板

```text
VPC: {{project_name}} ({{vpc_id}})
CIDR: {{vpc_cidr}}
├─ 子网: {{subnet_name_1}} ({{subnet_cidr_1}}) ~ {{zone_1}}
│  ├─ {{resource_name}}: {{ip_or_conn}}
│  └─ (预留)
├─ 子网: {{subnet_name_2}} ({{subnet_cidr_2}}) ~ {{zone_2}}
│  ├─ {{resource_name}}: {{ip_or_conn}}
│  └─ {{resource_name}}: {{ip_or_conn}}
└─ 子网: {{subnet_name_3}} ({{subnet_cidr_3}}) ~ {{zone_3}}
   └─ (预留)
```

> 此模板用于生成树形 ASCII 视图。变量由 `topo-render.py` 替换。
> 京东云术语用"子网"(Subnet)替代阿里云的"交换机"(VSwitch)。
