# IAM Core Concepts

## Overview

JD Cloud IAM (Identity and Access Management, 访问控制) provides centralized identity management and resource access control. It enables enterprises to securely manage access to JD Cloud resources through sub-users, groups, roles, and fine-grained permission policies.

## Core Components

### Sub-user (子用户)

**Definition:** A sub-user is an identity created under a JD Cloud main account. Sub-users are not independent JD Cloud accounts; they belong to the main account and can only access resources within the main account's scope.

**Key Characteristics:**
- Belongs to the main account (not independent)
- Must be authorized by the main account before accessing console or API
- Supports console login (username/password) and API access (AK/SK)
- Can be assigned permissions directly or through groups
- Can enable MFA (Multi-Factor Authentication) for enhanced security

**States:**
- `active` — Normal operation, can access authorized resources
- `disabled` — Suspended, cannot login or call APIs

**Use Cases:**
- Different functional roles (developers, operators, finance, etc.)
- Temporary project collaborators
- Service accounts for automation scripts

### Group (用户组)

**Definition:** A group is a collection of sub-users with similar permission requirements. Groups simplify permission management by applying policies to all members.

**Key Characteristics:**
- Group is a logical container for sub-users
- Permissions assigned to a group apply to all members
- Sub-users can belong to multiple groups (permission union)
- Group permissions are additive; no "deny" override in group-level
- Cannot nest groups (no subgroup concept)

**Use Cases:**
- Organize users by function (DevOps team, Finance team)
- Apply common baseline permissions to all team members
- Simplify permission updates when team roles change

### Role (角色)

**Definition:** A role is a virtual identity with a set of permissions that can be "assumed" by trusted entities (sub-users, services, or external accounts). Roles enable cross-account access and service-to-service authorization.

**Key Characteristics:**
- No permanent credentials; requires "assume" operation to obtain temporary credentials
- Defined by an **Assume Role Policy** (who can assume this role)
- Permissions assigned via **Attach Policy** operations
- Three role types:
  1. **User Role** — Assumed by JD Cloud sub-users (within or across accounts)
  2. **Service Role** — Assumed by JD Cloud services (e.g., ECS accessing OSS)
  3. **Federated Role** — Assumed by external identity providers (SAML)

**Temporary Credentials:**
- When a role is assumed, temporary AK/SK + SessionToken are generated
- Temporary credentials have limited lifetime (configurable duration)
- Permissions are scoped to the role's attached policies

**Use Cases:**
- Cross-account resource access (Account A's user accessing Account B's resources)
- Service-to-service authorization (compute service accessing storage)
- SSO integration (enterprise IdP users assuming roles)

### Policy (策略)

**Definition:** A policy is a JSON document that defines permissions. It specifies what actions are allowed or denied on which resources under what conditions.

**Types:**
1. **JD Cloud Managed Policies** — Pre-defined policies maintained by JD Cloud (e.g., `AdministratorAccess`, `ReadOnlyAccess`)
2. **Custom Policies** — User-defined policies with specific permission requirements

**Policy Structure (JSON):**
```json
{
  "Version": "2018-10-01",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "vm:describeInstance",
        "vm:createInstance"
      ],
      "Resource": [
        "*"
      ],
      "Condition": {
        "IpAddress": {
          "jdcloud:SourceIp": ["192.168.1.0/24"]
        }
      }
    }
  ]
}
```

**Key Elements:**
- `Version` — Policy syntax version (currently `"2018-10-01"`)
- `Statement` — Array of permission statements
- `Effect` — `"Allow"` or `"Deny"` (Deny takes precedence over Allow)
- `Action` — API operation names (e.g., `"vm:describeInstance"`)
- `Resource` — Target resource scope (e.g., `"*"` for all, or specific resource IDs)
- `Condition` — Optional conditions for permission activation (e.g., IP range, time window)

**Permission Evaluation Logic:**
1. **Explicit Deny** → Always deny (highest priority)
2. **Explicit Allow** → Allow (unless denied elsewhere)
3. **No Statement** → Deny by default

**Use Cases:**
- Grant read-only access to specific resources
- Restrict actions to specific IP ranges or time windows
- Implement fine-grained permission control per resource

### Access Key (AK/SK)

**Definition:** An AccessKey (AK) and SecretKey (SK) pair is a security credential used for API/SDK authentication. AK/SK enables programmatic access to JD Cloud OpenAPI.

**Types:**
1. **Main Account AK/SK** — Created and managed by the main account
2. **Sub-user AK/SK** — Created for sub-users to enable API access

**Key Characteristics:**
- AK is public (like a username); SK is secret (like a password)
- Used to sign API requests for authentication
- Can be created, disabled, enabled, and deleted
- **Cannot be retrieved after creation** — must be stored securely

**Security Best Practices:**
- **Never share SK** — Treat it like a password
- **Rotate regularly** — Create new AK/SK, update applications, then delete old ones
- **Disable immediately** if compromised
- **Use different AK/SK** for different environments/applications

**States:**
- `active` — Enabled, can be used for API calls
- `disabled` — Suspended, API calls will be rejected

## Permission Model

### Authorization Flow

1. **Sub-user requests access** → Console login or API call
2. **IAM evaluates permissions** → Check all attached policies (user-level + group-level)
3. **Permission union** → Combine all "Allow" permissions from attached policies
4. **Deny override** → If any policy explicitly "Denies" the action, block access
5. **Decision** → Allow or Deny based on evaluation result

### Permission Inheritance

- **Direct Permission:** Policy attached directly to sub-user
- **Group Permission:** Policy attached to groups that sub-user belongs to
- **Role Permission:** Temporary permissions from assumed role

**Union Rule:** A sub-user's effective permissions = Union of all permissions from:
- Directly attached policies
- Policies attached to all groups the user belongs to
- Policies attached to assumed roles (temporary)

### Principal Types

IAM supports authorization for the following principals:
- **JD Cloud Sub-users** — Identities within the account
- **JD Cloud Services** — Service identities (e.g., ECS, OSS)
- **External Identities** — Federated users via SAML IdP

## Resource Limits

| Resource Type | Default Limit | Notes |
|---------------|---------------|-------|
| Sub-users | 1,000 per account | Contact support to increase |
| Groups | 100 per account | Contact support to increase |
| Roles | 100 per account | Contact support to increase |
| Custom Policies | 100 per account | Contact support to increase |
| AK/SK per sub-user | 2 | Security recommendation |

## Supported IAM-enabled Products

IAM permissions control access to JD Cloud products that have integrated with IAM. For a complete list, see:
- Official documentation: https://docs.jdcloud.com/cn/iam/support-services

## Related Concepts

### MFA (Multi-Factor Authentication)

**Definition:** An additional security layer requiring a second authentication factor beyond password/AK/SK.

**Types:**
- **Virtual MFA** — Time-based one-time password (TOTP) via mobile app
- **Operation Protection** — MFA required for sensitive operations (e.g., delete resources)

**Use Cases:**
- Protect administrative accounts
- Safeguard sensitive operations
- Comply with security regulations

### STS (Security Token Service)

**Definition:** A service that issues temporary credentials for assumed roles.

**Key Operations:**
- `assumeRole` — Assume a user role and get temporary credentials
- `assumeRoleWithSAML` — Assume a federated role via SAML assertion

**Temporary Credential Properties:**
- Limited lifetime (configurable, e.g., 1 hour)
- Scoped to role's permissions
- Includes SessionToken for identity verification

### SSO (Single Sign-On)

**Definition:** Integration with external identity providers (IdP) for unified authentication.

**Types:**
- **User SSO** — IdP users mapped to JD Cloud sub-users
- **Role SSO** — IdP users assume JD Cloud roles directly

**Use Cases:**
- Enterprise Active Directory integration
- Okta / Azure AD integration
- Centralized identity management across clouds

## Best Practices

1. **Least Privilege:** Grant minimum permissions required; avoid `*` actions/resources
2. **Group-based Management:** Use groups for bulk permission assignment
3. **Regular Review:** Audit permissions quarterly; remove unused policies and accounts
4. **AK/SK Rotation:** Rotate access keys every 90 days; delete old keys after rotation
5. **MFA Enablement:** Require MFA for administrative accounts and sensitive operations
6. **Role Usage:** Use roles for cross-account access; avoid sharing AK/SK across accounts
7. **Policy Naming:** Use descriptive names with environment/service prefixes (e.g., `dev-readonly-policy`)