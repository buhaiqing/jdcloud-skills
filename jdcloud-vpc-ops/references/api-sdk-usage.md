# API & SDK Usage — jdcloud-vpc-ops

> **SDK**: `jdcloud_sdk>=1.6.26` | **Python**: 3.10 (NOT 3.12)

## SDK 初始化

```python
from jdcloud_sdk.services.vpc.client.VpcClient import VpcClient
from jdcloud_sdk.core.credential import Credential
from jdcloud_sdk.core.config import Config
from jdcloud_sdk.core.logger import Logger

# 凭证
credential = Credential(
    access_key="JDC_ACCESS_KEY",       # 从 env 读取
    secret_access_key="JDC_SECRET_KEY"  # 从 env 读取,NEVER hardcode
)

# 客户端 (region 可指定)
config = Config("cn-north-1")

# 日志
logger = Logger(level="info")

# VPC 客户端
client = VpcClient(credential, config=config, logger=logger)
```

## 核心 API 示例

### 1. 创建 VPC

```python
from jdcloud_sdk.services.vpc.apis.CreateVpcRequest import CreateVpcRequest

request = CreateVpcRequest(
    region_id="cn-north-1",
    vpc_name="sdk-create-vpc",
    address_prefix="10.0.0.0/16",
    description="Created via Python SDK",
)
try:
    response = client.send(request)
    if response.error:
        print(f"Error: {response.error.code} - {response.error.message}")
    else:
        vpc_id = response.result.vpc_id
        print(f"Created VPC: {vpc_id}")
except Exception as e:
    print(f"SDK error: {e}")
```

### 2. 查询 VPC 列表

```python
from jdcloud_sdk.services.vpc.apis.DescribeVpcsRequest import DescribeVpcsRequest

request = DescribeVpcsRequest(
    region_id="cn-north-1",
    page_number=1,
    page_size=100,
)
response = client.send(request)
if response.result:
    for vpc in response.result.vpcs:
        print(f"  {vpc.vpc_id}: {vpc.vpc_name} ({vpc.address_prefix})")
```

### 3. 创建子网

```python
from jdcloud_sdk.services.vpc.apis.CreateSubnetRequest import CreateSubnetRequest

request = CreateSubnetRequest(
    region_id="cn-north-1",
    vpc_id="vpc-xxx",
    subnet_name="sdk-subnet",
    address_prefix="10.0.1.0/24",
    az="cn-north-1a",
)
response = client.send(request)
if response.result:
    subnet_id = response.result.subnet_id
```

### 4. 添加安全组规则

```python
from jdcloud_sdk.services.vpc.apis.AddNetworkSecurityGroupRulesRequest import \
    AddNetworkSecurityGroupRulesRequest
from jdcloud_sdk.services.vpc.models.AddSecurityGroupRules import AddSecurityGroupRules

rule = AddSecurityGroupRules(
    protocol=6,            # 300=All, 6=TCP, 17=UDP, 1=ICMP
    direction=0,           # 0=inbound, 1=outbound
    address_prefix="0.0.0.0/0",
    from_port=80,
    to_port=80,
    description="HTTP inbound",
)
request = AddNetworkSecurityGroupRulesRequest(
    region_id="cn-north-1",
    network_security_group_id="sg-xxx",
    network_security_group_rule_specs=[rule],
)
response = client.send(request)
if response.result:
    rule_ids = response.result.network_security_group_rule_ids
    print(f"Added rules: {rule_ids}")
```

### 5. 删除 VPC

```python
from jdcloud_sdk.services.vpc.apis.DeleteVpcRequest import DeleteVpcRequest

request = DeleteVpcRequest(
    region_id="cn-north-1",
    vpc_id="vpc-xxx",
)
response = client.send(request)
if response.error:
    print(f"Delete failed: {response.error.message}")
else:
    print("VPC deleted")
```

## 错误处理

```python
from jdcloud_sdk.core.exception import JdCloudAPIException, JdCloudSDKException

try:
    response = client.send(request)
    if response.error:
        # API 层错误
        code = response.error.code       # e.g. "InvalidVpc.NotFound"
        message = response.error.message # e.g. "VPC not found"
except JdCloudAPIException as e:
    # API 异常 (网络错误/超时)
    print(f"API Error: {e}")
except JdCloudSDKException as e:
    # SDK 内部异常(通常非 SDK 错误)
    print(f"SDK Error: {e}")
```

## 重试策略

```python
import time
from functools import wraps

def retry_sdk(max_retries=3, backoff=2):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except (JdCloudAPIException, JdCloudSDKException) as e:
                    if attempt == max_retries - 1:
                        raise
                    wait = backoff ** attempt
                    print(f"Retry {attempt+1}/{max_retries}: waiting {wait}s")
                    time.sleep(wait)
            return None
        return wrapper
    return decorator
```

## SDK 可用 API 列表 (VPC)

```python
# 关键 API — 对应 CLI 子命令
CreateVpcRequest            # create-vpc
DescribeVpcsRequest         # describe-vpcs
DescribeVpcRequest          # describe-vpc
DeleteVpcRequest            # delete-vpc

CreateSubnetRequest         # create-subnet
DescribeSubnetsRequest      # describe-subnets
DescribeSubnetRequest       # describe-subnet
DeleteSubnetRequest         # delete-subnet

CreateNetworkSecurityGroupRequest               # create-network-security-group
DescribeNetworkSecurityGroupsRequest            # describe-network-security-groups
DescribeNetworkSecurityGroupRequest             # describe-network-security-group
DeleteNetworkSecurityGroupRequest               # delete-network-security-group
AddNetworkSecurityGroupRulesRequest             # add-network-security-group-rules
RemoveNetworkSecurityGroupRulesRequest          # remove-network-security-group-rules
ModifyNetworkSecurityGroupRequest               # modify-network-security-group

CreateRouteTableRequest         # create-route-table
DescribeRouteTablesRequest      # describe-route-tables
DescribeRouteTableRequest       # describe-route-table
DeleteRouteTableRequest         # delete-route-table
AddRouteTableRulesRequest       # add-route-table-rules
RemoveRouteTableRulesRequest    # remove-route-table-rules

CreateNetworkAclRequest         # create-network-acl
DescribeNetworkAclsRequest      # describe-network-acls
DeleteNetworkAclRequest         # delete-network-acl
AssociateNetworkAclRequest      # associate-network-acl
DisassociateNetworkAclRequest   # disassociate-network-acl

CreateVpcPeeringRequest         # create-vpc-peering
DescribeVpcPeeringsRequest      # describe-vpc-peerings
DeleteVpcPeeringRequest         # delete-vpc-peering
```

## Python 版本陷阱

`jdcloud_cli==1.2.12` 中的 `SafeConfigParser` 在 **Python 3.12** 中被移除:

```python
# Python 3.10 ✓ — 正常工作
from configparser import SafeConfigParser

# Python 3.12 ✗ — ImportError
# from configparser import SafeConfigParser  # ImportError: cannot import name
# 必须用 from configparser import ConfigParser
```

> **必须使用 Python 3.10 虚拟环境**: `uv venv --python 3.10`