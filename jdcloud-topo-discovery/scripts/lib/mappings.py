"""MappingSpec registry for all supported JD Cloud resource types.

This module exports MAPPINGS: a dict from resource_type string to
MappingSpec instance. Used by export-hcl.py to know how to convert
each `jdc --output json` response into HCL resource blocks.

> **Important**: `terraform_type` fields are **placeholder names** (e.g. `jdcloud_vpc`)
> because JD Cloud has **no official Terraform provider**. The generated HCL is
> documentation-only; `terraform apply` will fail with "Provider configuration not present".

Phase 1 covers Top-9 resource types:
  vpc, subnet, vm, mysql, redis, clb, eip, sg, kms, iam

Phase 2 adds: postgresql, mongodb, ag, nics
Phase 3 adds: es (via jdcloud-elasticsearch-ops), nat, route-table, acl
"""
from scripts.lib.field_mapper import MappingSpec, MappingRule


MAPPINGS = {
    "vpc": MappingSpec(
        resource_type="vpc",
        terraform_type="jdcloud_vpc",
        rules=[
            MappingRule(hcl_attr="vpc_name", path="vpcName"),
            MappingRule(hcl_attr="cidr_block", path="addressPrefix"),
            MappingRule(hcl_attr="description", path="description", required=False),
            MappingRule(hcl_attr="az_type", path="azType", required=False),
        ],
    ),
    "subnet": MappingSpec(
        resource_type="subnet",
        terraform_type="jdcloud_subnet",
        parent_ref="vpcId",
        rules=[
            MappingRule(hcl_attr="subnet_name", path="subnetName"),
            MappingRule(hcl_attr="cidr_block", path="addressPrefix"),
            MappingRule(hcl_attr="availability_zone", path="az"),
            MappingRule(hcl_attr="route_table_id", path="routeTableId", required=False),
            MappingRule(hcl_attr="description", path="description", required=False),
            # vpc_id is set via parent_ref (dependency inference)
        ],
    ),
    "vm": MappingSpec(
        resource_type="vm",
        terraform_type="jdcloud_instance",
        parent_ref="subnetId",
        rules=[
            MappingRule(hcl_attr="instance_name", path="instanceName"),
            MappingRule(hcl_attr="instance_type", path="instanceType"),
            MappingRule(hcl_attr="image_id", path="imageId"),
            MappingRule(hcl_attr="host_name", path="hostName", required=False),
            MappingRule(hcl_attr="private_ip", path="privateIpAddress", required=False),
            MappingRule(hcl_attr="az", path="az", required=False),
            MappingRule(hcl_attr="security_group_ids", path="networkSecurityGroupIds", type="list", required=False),
            # subnet_id via parent_ref
        ],
    ),
    "mysql": MappingSpec(
        resource_type="mysql",
        terraform_type="jdcloud_rds_instance",
        parent_ref="subnetId",
        rules=[
            MappingRule(hcl_attr="instance_name", path="instanceName"),
            MappingRule(hcl_attr="engine", path="engine"),
            MappingRule(hcl_attr="engine_version", path="engineVersion"),
            MappingRule(hcl_attr="instance_class", path="instanceClass"),
            MappingRule(hcl_attr="instance_storage_gb", path="instanceStorageGB", type="int", required=False),
            MappingRule(hcl_attr="az", path="az", required=False),
            MappingRule(hcl_attr="ha_mode", path="haMode", required=False),
            # Note: accountPassword NOT in describe response, but create-time sensitive
            MappingRule(hcl_attr="account_password", path="accountPassword", sensitive=True, required=False, default="${var.mysql_password}"),
        ],
    ),
    "postgresql": MappingSpec(
        resource_type="postgresql",
        terraform_type="jdcloud_rds_instance",
        parent_ref="subnetId",
        rules=[
            MappingRule(hcl_attr="instance_name", path="instanceName"),
            MappingRule(hcl_attr="engine", path="engine"),
            MappingRule(hcl_attr="engine_version", path="engineVersion"),
            MappingRule(hcl_attr="instance_class", path="instanceClass"),
            MappingRule(hcl_attr="instance_storage_gb", path="instanceStorageGB", type="int", required=False),
            MappingRule(hcl_attr="az", path="az", required=False),
        ],
    ),
    "mongodb": MappingSpec(
        resource_type="mongodb",
        terraform_type="jdcloud_mongodb_instance",
        parent_ref="subnetId",
        rules=[
            MappingRule(hcl_attr="instance_name", path="instanceName"),
            MappingRule(hcl_attr="engine_version", path="engineVersion"),
            MappingRule(hcl_attr="instance_class", path="instanceClass"),
            MappingRule(hcl_attr="az", path="az", required=False),
        ],
    ),
    "redis": MappingSpec(
        resource_type="redis",
        terraform_type="jdcloud_cache_instance",
        parent_ref="subnetId",
        rules=[
            MappingRule(hcl_attr="instance_name", path="cacheInstanceName"),
            MappingRule(hcl_attr="instance_class", path="instanceClass"),
            MappingRule(hcl_attr="instance_type", path="instanceType", required=False),
            MappingRule(hcl_attr="engine_version", path="engineVersion", required=False),
            MappingRule(hcl_attr="az", path="az", required=False),
            MappingRule(hcl_attr="port", path="port", type="int", required=False),
            MappingRule(hcl_attr="connection_domain", path="connectionDomain", required=False),
        ],
    ),
    "clb": MappingSpec(
        resource_type="clb",
        terraform_type="jdcloud_lb",
        parent_ref="subnetId",
        rules=[
            MappingRule(hcl_attr="load_balancer_name", path="loadBalancerName"),
            MappingRule(hcl_attr="load_balancer_type", path="loadBalancerType"),
            MappingRule(hcl_attr="private_ip", path="privateIp", required=False),
            MappingRule(hcl_attr="elastic_ip_id", path="elasticIpId", required=False),
            MappingRule(hcl_attr="elastic_ip_address", path="elasticIpAddress", required=False),
            MappingRule(hcl_attr="internet_charge_type", path="internetChargeType", required=False),
            MappingRule(hcl_attr="bandwidth_mbps", path="bandwidthMbps", type="int", required=False),
            MappingRule(hcl_attr="az", path="az", required=False),
        ],
    ),
    "eip": MappingSpec(
        resource_type="eip",
        terraform_type="jdcloud_eip",
        rules=[
            MappingRule(hcl_attr="name", path="name", required=False),
            MappingRule(hcl_attr="bandwidth_mbps", path="bandwidthMbps", type="int"),
            MappingRule(hcl_attr="charge_type", path="chargeType", required=False),
            MappingRule(hcl_attr="instance_type", path="instanceType", required=False),
            MappingRule(hcl_attr="instance_id", path="instanceId", required=False),
        ],
    ),
    "sg": MappingSpec(
        resource_type="sg",
        terraform_type="jdcloud_security_group",
        parent_ref="vpcId",
        rules=[
            MappingRule(hcl_attr="security_group_name", path="networkSecurityGroupName"),
            MappingRule(hcl_attr="description", path="description", required=False),
            MappingRule(hcl_attr="security_group_type", path="networkSecurityGroupType", required=False),
        ],
    ),
    "kms": MappingSpec(
        resource_type="kms",
        terraform_type="jdcloud_kms_key",
        rules=[
            MappingRule(hcl_attr="key_name", path="keyName", required=False),
            MappingRule(hcl_attr="description", path="description", required=False),
            MappingRule(hcl_attr="key_spec", path="keySpec", required=False),
            MappingRule(hcl_attr="key_usage", path="keyUsage", required=False),
            MappingRule(hcl_attr="origin", path="origin", required=False),
            MappingRule(hcl_attr="rotation_enabled", path="rotationEnabled", type="bool", required=False),
        ],
    ),
    "iam": MappingSpec(
        resource_type="iam",
        terraform_type="jdcloud_iam_sub_user",
        rules=[
            MappingRule(hcl_attr="user_name", path="subUserName"),
            MappingRule(hcl_attr="description", path="description", required=False),
            MappingRule(hcl_attr="status", path="status", required=False),
            # AccessKey 是 sensitive,但仅 AccessKeyId 暴露(SecretAccessKey 永不返回)
            MappingRule(hcl_attr="access_key_id", path="accessKeyId", sensitive=True, required=False),
        ],
    ),
    "ag": MappingSpec(
        resource_type="ag",
        terraform_type="jdcloud_ag",
        rules=[
            MappingRule(hcl_attr="ag_name", path="name"),
            MappingRule(hcl_attr="description", path="description", required=False),
            MappingRule(hcl_attr="vpc_id", path="vpcId", required=False),
            MappingRule(hcl_attr="az", path="az", required=False),
        ],
    ),
    "nics": MappingSpec(
        resource_type="nics",
        terraform_type="jdcloud_network_interface",
        parent_ref="subnetId",
        rules=[
            MappingRule(hcl_attr="nic_name", path="networkInterfaceName"),
            MappingRule(hcl_attr="private_ip", path="privateIpAddress", required=False),
            MappingRule(hcl_attr="mac_address", path="macAddress", required=False),
            MappingRule(hcl_attr="az", path="az", required=False),
        ],
    ),
    "es": MappingSpec(
        resource_type="es",
        terraform_type="jdcloud_es_instance",
        rules=[
            MappingRule(hcl_attr="instance_name", path="instanceName"),
            MappingRule(hcl_attr="engine_version", path="engineVersion", required=False),
        ],
    ),
}
