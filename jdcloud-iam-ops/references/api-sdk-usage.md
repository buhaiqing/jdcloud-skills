# IAM API & SDK Usage (Fallback Path)

## Overview

This document provides the **SDK/API fallback reference** for JD Cloud IAM. Use this path only when the `jdc` CLI fails after **3 consecutive retries** with exponential backoff.

## OpenAPI Specification

- **Base Path:** `https://iam.jdcloud-api.com/v1/`
- **API Reference:** https://docs.jdcloud.com/cn/iam/api/overview
- **Protocol:** HTTPS REST API
- **Authentication:** AK/SK signature in request headers

## Python SDK

### Installation

```bash
# Using uv (recommended)
uv pip install jdcloud_sdk

# Or using pip
pip install jdcloud_sdk
```

### Client Initialization

```python
import os
from jdcloud_sdk.core.credential import Credential
from jdcloud_sdk.services.iam.client.IamClient import IamClient

# Load credentials from environment
credential = Credential(
    os.environ["JDC_ACCESS_KEY"],
    os.environ["JDC_SECRET_KEY"]
)

# Initialize IAM client
client = IamClient(credential)
```

### STS Client Initialization

```python
from jdcloud_sdk.services.sts.client.StsClient import StsClient

sts_client = StsClient(credential)
```

## API Operations Map

### Sub-user Management APIs

| Operation | API Path | SDK Request Class |
|-----------|----------|-------------------|
| Create Sub-user | `POST /subUser` | `CreateSubUserRequest` |
| Describe Sub-user | `GET /subUser/{subUserName}` | `DescribeSubUserRequest` |
| Update Sub-user | `PATCH /subUser/{subUserName}` | `UpdateSubUserRequest` |
| Delete Sub-user | `DELETE /subUser/{subUserName}` | `DeleteSubUserRequest` |
| Attach Sub-user Policy | `POST /subUser/{subUserName}/policy` | `AttachSubUserPolicyRequest` |
| Detach Sub-user Policy | `DELETE /subUser/{subUserName}/policy/{policyName}` | `DetachSubUserPolicyRequest` |

### Group Management APIs

| Operation | API Path | SDK Request Class |
|-----------|----------|-------------------|
| Create Group | `POST /group` | `CreateGroupRequest` |
| Describe Group | `GET /group/{groupName}` | `DescribeGroupRequest` |
| Update Group | `PATCH /group/{groupName}` | `UpdateGroupRequest` |
| Delete Group | `DELETE /group/{groupName}` | `DeleteGroupRequest` |
| Add Sub-user to Group | `POST /group/{groupName}/subUser` | `AddSubUserToGroupRequest` |
| Remove Sub-user from Group | `DELETE /group/{groupName}/subUser/{subUserName}` | `RemoveSubUserFromGroupRequest` |
| Attach Group Policy | `POST /group/{groupName}/policy` | `AttachGroupPolicyRequest` |
| Detach Group Policy | `DELETE /group/{groupName}/policy/{policyName}` | `DetachGroupPolicyRequest` |

### Role Management APIs

| Operation | API Path | SDK Request Class |
|-----------|----------|-------------------|
| Create Role | `POST /role` | `CreateRoleRequest` |
| Describe Role | `GET /role/{roleName}` | `DescribeRoleRequest` |
| Update Assume Role Policy | `PUT /role/{roleName}/assumeRolePolicy` | `UpdateAssumeRolePolicyRequest` |
| Delete Role | `DELETE /role/{roleName}` | `DeleteRoleRequest` |
| Attach Role Policy | `POST /role/{roleName}/policy` | `AttachRolePolicyRequest` |
| Detach Role Policy | `DELETE /role/{roleName}/policy/{policyName}` | `DetachRolePolicyRequest` |

### Policy Management APIs

| Operation | API Path | SDK Request Class |
|-----------|----------|-------------------|
| Create Policy | `POST /policy` | `CreatePolicyRequest` |
| Describe Policy | `GET /policy/{policyName}` | `DescribePolicyRequest` |
| Update Policy Description | `PATCH /policy/{policyName}` | `UpdatePolicyDescriptionRequest` |
| Delete Policy | `DELETE /policy/{policyName}` | `DeletePolicyRequest` |

### Access Key Management APIs

| Operation | API Path | SDK Request Class |
|-----------|----------|-------------------|
| Create User AccessKey | `POST /userAccessKey` | `CreateUserAccessKeyRequest` |
| Describe User AccessKeys | `GET /userAccessKey` | `DescribeUserAccessKeysRequest` |
| Disable User AccessKey | `PUT /userAccessKey/{accessKeyId}/disable` | `DisabledUserAccessKeyRequest` |
| Enable User AccessKey | `PUT /userAccessKey/{accessKeyId}/enable` | `EnabledUserAccessKeyRequest` |
| Delete User AccessKey | `DELETE /userAccessKey/{accessKeyId}` | `DeleteUserAccessKeyRequest` |

### STS APIs

| Operation | API Path | SDK Request Class |
|-----------|----------|-------------------|
| Assume Role | `POST /assumeRole` | `AssumeRoleRequest` (in STS module) |
| Assume Role with SAML | `POST /assumeRoleWithSAML` | `AssumeRoleWithSAMLRequest` (in STS module) |

## SDK Usage Examples

### Create Sub-user

```python
from jdcloud_sdk.services.iam.apis.CreateSubUserRequest import (
    CreateSubUserRequest,
    CreateSubUserParameters
)

params = CreateSubUserParameters(
    subUserName="dev-user-01",
    description="Developer account for project X"
)
req = CreateSubUserRequest(parameters=params)
resp = client.send(req)

# Parse response
subuser_id = resp.result["subUser"]["subUserId"]
subuser_name = resp.result["subUser"]["subUserName"]
print(f"Created sub-user: {subuser_name} (ID: {subuser_id})")
```

### Describe Sub-user

```python
from jdcloud_sdk.services.iam.apis.DescribeSubUserRequest import (
    DescribeSubUserRequest,
    DescribeSubUserParameters
)

params = DescribeSubUserParameters(subUserName="dev-user-01")
req = DescribeSubUserRequest(parameters=params)
resp = client.send(req)

# Access fields
status = resp.result["subUser"]["status"]
description = resp.result["subUser"]["description"]
```

### List Sub-users (Pagination)

```python
from jdcloud_sdk.services.iam.apis.DescribeSubUsersRequest import (
    DescribeSubUsersRequest,
    DescribeSubUsersParameters
)

params = DescribeSubUsersParameters()
params.setPageNumber(1)
params.setPageSize(50)
req = DescribeSubUsersRequest(parameters=params)
resp = client.send(req)

# Iterate results
for subuser in resp.result["subUsers"]:
    print(f"{subuser['subUserName']} - {subuser['status']}")
```

### Create Group

```python
from jdcloud_sdk.services.iam.apis.CreateGroupRequest import (
    CreateGroupRequest,
    CreateGroupParameters
)

params = CreateGroupParameters(
    groupName="devops-team",
    description="DevOps team group"
)
req = CreateGroupRequest(parameters=params)
resp = client.send(req)
group_id = resp.result["group"]["groupId"]
```

### Create Role

```python
from jdcloud_sdk.services.iam.apis.CreateRoleRequest import (
    CreateRoleRequest,
    CreateRoleParameters
)

assume_role_policy = {
    "version": "2018-10-01",
    "statement": [
        {
            "effect": "Allow",
            "principal": {
                "jdcloud": ["arn:jdcloud:iam::ACCOUNT_ID:user/*"]
            },
            "action": ["iam:assumeRole"]
        }
    ]
}

params = CreateRoleParameters(
    roleName="cross-account-role",
    description="Cross-account access role",
    assumeRolePolicyDocument=json.dumps(assume_role_policy)
)
req = CreateRoleRequest(parameters=params)
resp = client.send(req)
role_id = resp.result["role"]["roleId"]
```

### Create Policy

```python
from jdcloud_sdk.services.iam.apis.CreatePolicyRequest import (
    CreatePolicyRequest,
    CreatePolicyParameters
)

policy_doc = {
    "version": "2018-10-01",
    "statement": [
        {
            "effect": "Allow",
            "action": ["vm:describe*"],
            "resource": ["*"]
        }
    ]
}

params = CreatePolicyParameters(
    policyName="vm-readonly-policy",
    description="Read-only access to VM instances",
    policyDocument=json.dumps(policy_doc)
)
req = CreatePolicyRequest(parameters=params)
resp = client.send(req)
policy_id = resp.result["policy"]["policyId"]
```

### Attach Policy to Sub-user

```python
from jdcloud_sdk.services.iam.apis.AttachSubUserPolicyRequest import (
    AttachSubUserPolicyRequest,
    AttachSubUserPolicyParameters
)

params = AttachSubUserPolicyParameters(
    subUserName="dev-user-01",
    policyName="vm-readonly-policy"
)
req = AttachSubUserPolicyRequest(parameters=params)
resp = client.send(req)
# No result on success; check requestId for confirmation
```

### Create AccessKey

```python
from jdcloud_sdk.services.iam.apis.CreateUserAccessKeyRequest import (
    CreateUserAccessKeyRequest,
    CreateUserAccessKeyParameters
)

params = CreateUserAccessKeyParameters()
req = CreateUserAccessKeyRequest(parameters=params)
resp = client.send(req)

# ⚠️ CRITICAL: Save secretKey immediately (only returned once)
# SECURITY: NEVER log or print the actual secretKey value
access_key_id = resp.result["accessKey"]["accessKeyId"]
secret_key = resp.result["accessKey"]["secretKey"]

# Store securely (e.g., environment variable, secret manager) - NEVER print
# Example: os.environ["MY_SECRET_KEY"] = secret_key
print(f"AccessKey created: {access_key_id}")
print(f"SecretKey: <masked> (SAVE SECURELY - only returned once)")
```

### Assume Role (STS)

```python
from jdcloud_sdk.services.sts.client.StsClient import StsClient
from jdcloud_sdk.services.sts.apis.AssumeRoleRequest import (
    AssumeRoleRequest,
    AssumeRoleParameters
)

sts_client = StsClient(credential)
params = AssumeRoleParameters(
    roleName="cross-account-role",
    durationSeconds=3600  # 1 hour
)
req = AssumeRoleRequest(parameters=params)
resp = sts_client.send(req)

# Temporary credentials
# SECURITY: NEVER log or print the actual secretKey value
temp_ak = resp.result["credentials"]["accessKeyId"]
temp_sk = resp.result["credentials"]["secretKey"]  # Store securely, NEVER print
session_token = resp.result["credentials"]["sessionToken"]  # Store securely, NEVER print
expiration = resp.result["credentials"]["expiration"]

print(f"Temporary AK: {temp_ak}")
print(f"SecretKey: <masked> (store securely)")
print(f"SessionToken: <masked> (store securely)")
print(f"Expires: {expiration}")
```

### Delete Sub-user (with Safety Gate)

```python
from jdcloud_sdk.services.iam.apis.DeleteSubUserRequest import (
    DeleteSubUserRequest,
    DeleteSubUserParameters
)

# ⚠️ Safety Gate: MUST obtain explicit user confirmation
# Ask: "Are you sure you want to delete dev-user-01? This is IRREVERSIBLE."
# Proceed only after explicit "yes" / "confirm" response

params = DeleteSubUserParameters(subUserName="dev-user-01")
req = DeleteSubUserRequest(parameters=params)
resp = client.send(req)
```

## Error Handling

### Common Error Patterns

| HTTP Status | Error Code | Meaning | Agent Action |
|-------------|------------|---------|--------------|
| 400 | `InvalidParameter` | Request validation failed | Fix parameters per OpenAPI; retry once |
| 400 | `SubUserAlreadyExists` | Duplicate sub-user name | Ask user: reuse existing or new name? |
| 400 | `GroupAlreadyExists` | Duplicate group name | Ask user: reuse existing or new name? |
| 400 | `RoleAlreadyExists` | Duplicate role name | Ask user: reuse existing or new name? |
| 400 | `PolicyAlreadyExists` | Duplicate policy name | Ask user: reuse existing or new name? |
| 403 | `PermissionDenied` | Caller lacks permission | HALT; user adjusts caller's permissions |
| 403 | `InvalidAccessKey` | AK/SK invalid or disabled | HALT; user checks credentials |
| 404 | `SubUserNotFound` | Sub-user does not exist | HALT; verify sub-user name |
| 404 | `GroupNotFound` | Group does not exist | HALT; verify group name |
| 404 | `RoleNotFound` | Role does not exist | HALT; verify role name |
| 404 | `PolicyNotFound` | Policy does not exist | HALT; verify policy name |
| 409 | `QuotaExceeded` | Resource limit reached | HALT; user requests quota increase |
| 429 | `Throttling` | Rate limit exceeded | Retry with exponential backoff |
| 500 | `InternalError` | Server error | Retry 3 times; HALT with requestId |

### Retry Strategy

```python
import time
from jdcloud_sdk.exception import JdcloudSDKException

def retry_with_backoff(client, request, max_retries=3):
    for attempt in range(max_retries):
        try:
            return client.send(request)
        except JdcloudSDKException as e:
            if e.status_code in [400]:  # Non-retryable
                raise
            if e.status_code in [500, 502, 503, 504]:  # Retryable
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # 2s, 4s, 8s
                    continue
            raise
    raise RuntimeError(f"Max retries exceeded for request: {request}")
```

## Request/Response Notes

### Required Fields

| Operation | Required Fields |
|-----------|----------------|
| Create Sub-user | `subUserName` |
| Create Group | `groupName` |
| Create Role | `roleName`, `assumeRolePolicyDocument` |
| Create Policy | `policyName`, `policyDocument` |
| Attach Policy | `policyName`, target principal name |

### Pagination

List operations (`describeSubUsers`, `describeGroups`, `describeRoles`, `describePolicies`) support pagination:
- `pageNumber` — Page number (1-based, default: 1)
- `pageSize` — Records per page (default: 20, max varies)

Response pagination fields:
- `totalCount` — Total records
- `pageNumber` — Current page
- `pageSize` — Page size

## Security Best Practices

1. **Never log or print secretKey** — It is returned only once; save securely
2. **Use temporary credentials** — Prefer STS for cross-account access
3. **Rotate AK/SK regularly** — Create new, update applications, delete old
4. **Validate input** — Ensure sub-user/group/role/policy names match constraints
5. **Handle 403 PermissionDenied** — Caller lacks IAM permission; HALT and inform user

## See Also

- [CLI Usage](cli-usage.md) — Primary execution path (use before SDK)
- [Core Concepts](core-concepts.md) — IAM fundamentals
- [Integration](integration.md) — Environment setup with uv