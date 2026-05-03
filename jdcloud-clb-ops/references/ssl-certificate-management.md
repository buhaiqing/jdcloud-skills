# SSL Certificate Management for JD Cloud Load Balancer

## Overview

SSL/TLS certificates are required for HTTPS and TLS listeners on Application Load Balancer (ALB). This document covers certificate binding, renewal, and multi-certificate (SNI) configurations.

## Certificate Sources

JD Cloud Load Balancer supports certificates from:

1. **JD Cloud SSL Certificate Service**: Certificates purchased or uploaded via JD Cloud SSL Certificate Management.
2. **External CA Certificates**: Upload external certificates (PEM format) to JD Cloud SSL service.

### Certificate Service Location

Certificates are managed in **JD Cloud SSL Certificate Service** (云安全-SSL数字证书), not directly in Load Balancer.

- Console: JD Cloud Console → 安全 → SSL数字证书
- API: SSL Certificate Service API (separate from LB API)

## Certificate Binding Workflow

### Step 1: Obtain or Upload Certificate

**Purchase Certificate (JD Cloud Console)**:
1. Navigate to SSL Certificate Service.
2. Purchase or request certificate for domain.
3. Wait for certificate issuance.

**Upload External Certificate**:
1. Prepare PEM-encoded certificate and private key.
2. Upload via SSL Certificate Service console or API.

### Step 2: Create HTTPS Listener with Certificate

```python
from jdcloud_sdk.services.alb.apis.CreateListenerRequest import (
    CreateListenerRequest,
    CreateListenerSpec,
    CertificateSpec
)

cert_spec = CertificateSpec(
    certificateId="cert-abc123",  # From SSL Certificate Service
    tlsSecurityPolicyId="tls-2022-policy"
)

listener_spec = CreateListenerSpec(
    loadBalancerId="lb-prod",
    protocol="https",
    port=443,
    certificateSpec=cert_spec
)

req = CreateListenerRequest(regionId="cn-north-1", spec=listener_spec)
resp = client.createListener(req)
```

### Step 3: Verify Certificate Binding

```python
from jdcloud_sdk.services.alb.apis.DescribeListenerRequest import DescribeListenerRequest

req = DescribeListenerRequest(
    regionId="cn-north-1",
    loadBalancerId="lb-prod",
    listenerId="listener-https"
)

resp = client.describeListener(req)
cert_id = resp.result.listener.certificateSpec.certificateId
print(f"Bound certificate: {cert_id}")
```

## Multi-Certificate Support (SNI)

### SNI Overview

Server Name Indication (SNI) allows a single HTTPS listener to serve multiple domains with different certificates. ALB selects the appropriate certificate based on the TLS handshake hostname.

### SNI Configuration

```python
from jdcloud_sdk.services.alb.apis.AddListenerCertificatesRequest import (
    AddListenerCertificatesRequest,
    CertificateSpec
)

# Add additional certificates for SNI
sni_certs = [
    CertificateSpec(certificateId="cert-api-example-com"),
    CertificateSpec(certificateId="cert-www-example-com"),
]

req = AddListenerCertificatesRequest(
    regionId="cn-north-1",
    loadBalancerId="lb-prod",
    listenerId="listener-https",
    certificates=sni_certs
)

resp = client.addListenerCertificates(req)
```

### SNI Domain Mapping

Each certificate is associated with its domain(s) in SSL Certificate Service. ALB automatically matches:

| Certificate | Domain(s) |
|-------------|-----------|
| cert-default | *.example.com (fallback) |
| cert-api | api.example.com |
| cert-www | www.example.com, example.com |

## Certificate Update/Renewal

### Renewal Workflow

1. **Renew certificate** in SSL Certificate Service before expiration.
2. **Update listener certificate** binding to use renewed certificate.

```python
from jdcloud_sdk.services.alb.apis.UpdateListenerCertificatesRequest import (
    UpdateListenerCertificatesRequest,
    CertificateSpec
)

# Update to renewed certificate
new_cert_spec = CertificateSpec(
    certificateId="cert-renewed-abc123",
    tlsSecurityPolicyId="tls-2022-policy"
)

req = UpdateListenerCertificatesRequest(
    regionId="cn-north-1",
    loadBalancerId="lb-prod",
    listenerId="listener-https",
    certificateSpec=new_cert_spec
)

resp = client.updateListenerCertificates(req)
```

### Certificate Expiration Monitoring

Monitor certificate expiration via:

1. **SSL Certificate Service alerts**: Configure expiration alerts in certificate service.
2. **Custom monitoring**: Track certificate validity days.

Recommended threshold: Alert when certificate expires in < 30 days.

## TLS Security Policies

### Predefined Policies

JD Cloud provides predefined TLS security policies:

| Policy ID | Description |
|-----------|-------------|
| tls-2022-policy | TLS 1.2+ with modern ciphers (recommended) |
| tls-2020-policy | TLS 1.2+ with broader compatibility |
| tls-compat-policy | TLS 1.0+ for legacy clients |

### Custom TLS Policy

```python
from jdcloud_sdk.services.alb.apis.CreateSecurityPolicyRequest import (
    CreateSecurityPolicyRequest,
    SecurityPolicySpec
)

policy_spec = SecurityPolicySpec(
    name="tls-custom-secure",
    minTlsVersion="TLS_1_2",
    ciphers=[
        "ECDHE-RSA-AES256-GCM-SHA384",
        "ECDHE-RSA-AES128-GCM-SHA256",
        "AES256-GCM-SHA384",
        "AES128-GCM-SHA256"
    ]
)

req = CreateSecurityPolicyRequest(regionId="cn-north-1", spec=policy_spec)
resp = client.createSecurityPolicy(req)

policy_id = resp.result.securityPolicyId
print(f"Created TLS policy: {policy_id}")
```

### Cipher Suite Reference

| Cipher Suite | Security Level | Recommendation |
|--------------|----------------|----------------|
| ECDHE-RSA-AES256-GCM-SHA384 | Strong | Recommended |
| ECDHE-RSA-CHACHA20-POLY1305 | Strong | Recommended |
| ECDHE-RSA-AES128-GCM-SHA256 | Strong | Recommended |
| AES256-GCM-SHA384 | Moderate | Acceptable |
| AES128-GCM-SHA256 | Moderate | Acceptable |
| RSA-AES256-CBC-SHA | Weak | Avoid (CBC mode) |
| RSA-AES128-CBC-SHA | Weak | Avoid |

## Certificate Removal

### Remove Certificate from Listener

```python
from jdcloud_sdk.services.alb.apis.DeleteListenerCertificatesRequest import DeleteListenerCertificatesRequest

req = DeleteListenerCertificatesRequest(
    regionId="cn-north-1",
    loadBalancerId="lb-prod",
    listenerId="listener-https",
    certificateIds=["cert-old-123"]
)

resp = client.deleteListenerCertificates(req)
```

**Note**: Removing the default certificate (the one set during listener creation) requires updating the listener with a new default certificate.

## Certificate Troubleshooting

### Common Issues

| Issue | Symptoms | Resolution |
|-------|----------|------------|
| Certificate not found | 404 on create listener | Upload certificate to SSL service first |
| Certificate domain mismatch | Client certificate error | Ensure certificate domain matches request host |
| Certificate expired | TLS handshake failure | Renew certificate and update binding |
| Weak cipher suite | Browser security warning | Update TLS policy to stronger ciphers |
| SNI not working | Wrong certificate returned | Verify domain mapping in certificate metadata |

### Certificate Validation

```python
# Check certificate validity via SSL service (if API available)
# Or verify TLS handshake externally
import ssl
import socket

def check_certificate(hostname, port=443):
    context = ssl.create_default_context()
    with socket.create_connection((hostname, port)) as sock:
        with context.wrap_socket(sock, server_hostname=hostname) as ssock:
            cert = ssock.getpeercert()
            print(f"Subject: {cert['subject']}")
            print(f"Issuer: {cert['issuer']}")
            print(f"Expires: {cert['notAfter']}")
```

## Best Practices

1. **Use TLS 1.2+ minimum**: Configure TLS policy with minimum version 1.2.
2. **Prefer ECDHE cipher suites**: Forward secrecy for enhanced security.
3. **Enable SNI for multi-domain**: Use SNI for multiple domains on single listener.
4. **Monitor expiration**: Set alerts for certificates expiring within 30 days.
5. **Automate renewal**: Use certificate service auto-renewal or scripted renewal workflow.
6. **Separate certificates per domain**: Avoid wildcard certificates for high-security applications.

## Integration with ssl-certificate Skill

For certificate issuance, upload, and renewal workflows, delegate to the `ssl-certificate` skill:

| Task | Skill |
|------|-------|
| Purchase/request certificate | `ssl-certificate` |
| Upload external certificate | `ssl-certificate` |
| Configure expiration alerts | `ssl-certificate` |
| Renew certificate | `ssl-certificate` |
| Bind certificate to LB listener | `jdcloud-clb-ops` (this skill) |
| Update LB listener certificate | `jdcloud-clb-ops` |

## API Operations Summary

| Operation | API | Purpose |
|-----------|-----|---------|
| Create listener with cert | `createListener` | Initial binding |
| Add SNI certificates | `addListenerCertificates` | Multi-domain support |
| Update listener cert | `updateListenerCertificates` | Renewal/replacement |
| Delete listener cert | `deleteListenerCertificates` | Remove unused cert |
| Describe listener cert | `describeListener` | Verify binding |
| Create TLS policy | `createSecurityPolicy` | Custom cipher config |
| Describe TLS policies | `describeSecurityPolicies` | List available policies |

## See Also

- [JD Cloud SSL Certificate Service](https://docs.jdcloud.com/cn/ssl-certificate/)
- [ALB HTTPS Listener Configuration](https://docs.jdcloud.com/cn/application-load-balancer/create-listener)
- [TLS Security Policy Reference](https://docs.jdcloud.com/cn/application-load-balancer/tls-security-policy)