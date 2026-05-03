# Idempotency Checklist — JD Cloud Load Balancer

## Overview

This document defines idempotency behavior for Load Balancer operations to support safe automation, retry logic, and CI/CD pipelines.

## Idempotency Definition

An operation is **idempotent** if executing it multiple times with the same parameters produces the same result as executing it once.

| Category | Behavior | Safe to Retry? |
|----------|----------|----------------|
| **Naturally Idempotent** | Same state → same outcome, no side effects | ✅ Yes |
| **Conditional Idempotent** | Idempotent only under certain conditions | ⚠️ Conditional |
| **Non-Idempotent** | Each execution creates new resource/state | ❌ No |

## Load Balancer Operations Idempotency Matrix

### Load Balancer Instance Operations

| Operation | Idempotency | Behavior on Retry | Automation Strategy |
|-----------|-------------|-------------------|---------------------|
| `createLoadBalancer` | ❌ Non-Idempotent | Creates new LB each call; duplicate name → `NameAlreadyExists` error | Use unique names with timestamp/UUID; check existence before create |
| `describeLoadBalancer` | ✅ Idempotent | Returns current state; no modification | Safe to retry on transient errors |
| `describeLoadBalancers` | ✅ Idempotent | Returns filtered list; no modification | Safe to retry |
| `updateLoadBalancer` | ✅ Idempotent | Same update → same final state; no duplicate changes | Safe to retry after validation |
| `deleteLoadBalancer` | ✅ Idempotent | 404 on non-existent LB; safe to re-delete already-deleted | Safe to retry; check 404 as success |
| `associateElasticIp` | ⚠️ Conditional | EIP already bound → error; different EIP → replaces | Check current binding before operation |
| `disassociateElasticIp` | ✅ Idempotent | EIP not bound → 404 or success; no error | Safe to retry |
| `associateSecurityGroup` | ⚠️ Conditional | SG already bound → no change; add new SG | Check current SG list |
| `disassociateSecurityGroup` | ✅ Idempotent | SG not bound → 404 or success | Safe to retry |

### Listener Operations

| Operation | Idempotency | Behavior on Retry | Automation Strategy |
|-----------|-------------|-------------------|---------------------|
| `createListener` | ❌ Non-Idempotent | New listener each call; port in use → `PortInUse` error | Check port availability; use unique name |
| `describeListener` | ✅ Idempotent | Returns current state | Safe to retry |
| `describeListeners` | ✅ Idempotent | Returns filtered list | Safe to retry |
| `updateListener` | ✅ Idempotent | Same config → same state | Safe to retry |
| `deleteListener` | ✅ Idempotent | 404 on non-existent; safe | Safe to retry |
| `addListenerCertificates` | ⚠️ Conditional | Certificate already added → no change or error | Check current cert list |
| `deleteListenerCertificates` | ✅ Idempotent | Cert not bound → 404 or success | Safe to retry |
| `updateListenerCertificates` | ✅ Idempotent | Same cert config → same state | Safe to retry |

### Target Group Operations

| Operation | Idempotency | Behavior on Retry | Automation Strategy |
|-----------|-------------|-------------------|---------------------|
| `createTargetGroup` | ❌ Non-Idempotent | New group each call; duplicate name → error | Check existence; unique names |
| `describeTargetGroup` | ✅ Idempotent | Returns current state | Safe to retry |
| `describeTargetGroups` | ✅ Idempotent | Returns filtered list | Safe to retry |
| `updateTargetGroup` | ✅ Idempotent | Same config → same state | Safe to retry |
| `deleteTargetGroup` | ✅ Idempotent | 404 on non-existent | Safe to retry |
| `registerTargets` | ⚠️ Conditional | Target already registered with same port/weight → no change; different weight → update | Check current registration |
| `deRegisterTargets` | ✅ Idempotent | Target not registered → 404 or success | Safe to retry |
| `updateTargets` | ✅ Idempotent | Same weight → no change | Safe to retry |
| `describeTargets` | ✅ Idempotent | Returns current targets | Safe to retry |

### Backend Service Operations

| Operation | Idempotency | Behavior on Retry | Automation Strategy |
|-----------|-------------|-------------------|---------------------|
| `createBackend` | ❌ Non-Idempotent | New backend each call | Check existence first |
| `describeBackend` | ✅ Idempotent | Returns current state | Safe to retry |
| `describeBackends` | ✅ Idempotent | Returns filtered list | Safe to retry |
| `updateBackend` | ✅ Idempotent | Same config → same state | Safe to retry |
| `deleteBackend` | ✅ Idempotent | 404 on non-existent | Safe to retry |
| `describeTargetHealth` | ✅ Idempotent | Returns health status | Safe to retry |

### Forwarding Rule Operations (ALB)

| Operation | Idempotency | Behavior on Retry | Automation Strategy |
|-----------|-------------|-------------------|---------------------|
| `createUrlMap` | ❌ Non-Idempotent | New UrlMap each call | Check existence first |
| `describeUrlMap` | ✅ Idempotent | Returns current state | Safe to retry |
| `describeUrlMaps` | ✅ Idempotent | Returns filtered list | Safe to retry |
| `updateUrlMap` | ✅ Idempotent | Same rules → same state | Safe to retry |
| `deleteUrlMap` | ✅ Idempotent | 404 on non-existent | Safe to retry |
| `addRules` | ⚠️ Conditional | Duplicate rule → error or skip | Check existing rules |
| `updateRules` | ✅ Idempotent | Same config → same state | Safe to retry |
| `deleteRules` | ✅ Idempotent | Rule not exists → 404 or success | Safe to retry |

### TLS Security Policy Operations

| Operation | Idempotency | Behavior on Retry | Automation Strategy |
|-----------|-------------|-------------------|---------------------|
| `createSecurityPolicy` | ❌ Non-Idempotent | New policy each call; duplicate name → error | Check existence; unique names |
| `describeSecurityPolicy` | ✅ Idempotent | Returns current state | Safe to retry |
| `describeSecurityPolicies` | ✅ Idempotent | Returns filtered list | Safe to retry |
| `updateSecurityPolicy` | ✅ Idempotent | Same ciphers → same state | Safe to retry |
| `deleteSecurityPolicy` | ✅ Idempotent | 404 on non-existent | Safe to retry |
| `describeSupportedCiphers` | ✅ Idempotent | Returns static cipher list | Safe to retry |

## Automation Best Practices

### Pre-Check Pattern for Non-Idempotent Operations

Before executing non-idempotent operations, check resource existence:

```python
# Idempotent create pattern
def idempotent_create_lb(client, name, vpc_id, region):
    # Step 1: Check if LB already exists
    existing = find_lb_by_name(client, name, region)
    if existing:
        print(f"LB '{name}' already exists: {existing.loadBalancerId}")
        return existing.loadBalancerId
    
    # Step 2: Create if not exists
    spec = CreateLoadBalancerSpec(name=name, vpcId=vpc_id, type="application")
    req = CreateLoadBalancerRequest(regionId=region, spec=spec)
    resp = client.createLoadBalancer(req)
    
    return resp.result.loadBalancerId

def find_lb_by_name(client, name, region):
    req = DescribeLoadBalancersRequest(regionId=region, pageNumber=1, pageSize=100)
    resp = client.describeLoadBalancers(req)
    for lb in resp.result.loadBalancers:
        if lb.name == name:
            return lb
    return None
```

### Safe Delete Pattern

```python
# Idempotent delete pattern
def idempotent_delete_lb(client, lb_id, region):
    try:
        req = DeleteLoadBalancerRequest(regionId=region, loadBalancerId=lb_id)
        client.deleteLoadBalancer(req)
        print(f"LB {lb_id} deleted")
        return True
    except Exception as e:
        if "NotFound" in str(e) or "404" in str(e):
            print(f"LB {lb_id} already deleted or not found")
            return True  # Treat as success
        raise  # Re-raise other errors
```

### Target Registration Pattern

```python
# Idempotent register targets pattern
def idempotent_register_targets(client, target_group_id, targets, region):
    # Step 1: Get current targets
    req = DescribeTargetsRequest(regionId=region, targetGroupId=target_group_id)
    resp = client.describeTargets(req)
    current = {t.targetId: (t.port, t.weight) for t in resp.result.targets}
    
    # Step 2: Filter out already-registered with same config
    to_register = []
    for t in targets:
        if t.targetId not in current:
            to_register.append(t)
        elif current[t.targetId] != (t.port, t.weight):
            # Target exists but config differs - update instead
            to_register.append(t)
    
    if not to_register:
        print("All targets already registered with correct config")
        return True
    
    # Step 3: Register only new/different targets
    req = RegisterTargetsRequest(regionId=region, targetGroupId=target_group_id, targets=to_register)
    client.registerTargets(req)
    return True
```

## Error Classification for Retry Logic

| Error Type | Retry Safe? | Reason |
|------------|-------------|--------|
| `NotFound` / 404 | ✅ Yes (delete ops) | Resource already gone — success for delete |
| `NotFound` / 404 | ❌ No (read/update ops) | Resource missing — fix upstream |
| `NameAlreadyExists` | ❌ No | Duplicate name — change name |
| `PortInUse` | ❌ No | Conflict — change port or delete existing listener |
| `InvalidParameter` | ❌ No | Client error — fix request |
| `QuotaExceeded` | ❌ No | Business limit — request increase |
| `InsufficientBalance` | ❌ No | Account issue — top up |
| `Throttling` / 429 | ✅ Yes | Rate limit — back off and retry |
| `InternalError` / 500 | ✅ Yes | Server error — retry with backoff |
| `DependencyError` | ⚠️ Conditional | Check dependent resource first |

## Retry Strategy Matrix

| Operation Category | Retry Policy | Max Retries | Backoff |
|--------------------|--------------|-------------|---------|
| Read (describe/list) | Retry on 429/500 | 3 | Exponential (2s, 4s, 8s) |
| Write (create) | No retry on 400/409 | 0 | — |
| Write (update) | Retry on 429/500 | 3 | Exponential |
| Delete | Retry on 429/500; accept 404 | 3 | Exponential |
| Binding (associate) | Conditional: check first | 0-1 | — |

## CI/CD Integration Checklist

Before running LB automation in CI/CD:

- [ ] Use unique resource names (include build ID, timestamp, or UUID)
- [ ] Implement pre-check for existence on create operations
- [ ] Handle 404 as success for delete operations
- [ ] Filter duplicate registrations on target operations
- [ ] Capture and compare current state before update
- [ ] Implement exponential backoff for throttling/server errors
- [ ] Add cleanup step for failed/partial deployments
- [ ] Use `--dry-run` or validation API if available

## See Also

- [API & SDK Usage](api-sdk-usage.md) for operation details
- [Troubleshooting](troubleshooting.md) for error handling
- [Integration](integration.md) for SDK setup