# Core Concepts — JD Cloud SSL Certificate

## Architecture Overview

JD Cloud SSL Certificate Service provides digital certificate management including upload, storage, download, and lifecycle management of SSL/TLS certificates.

### Key Components

| Component | Description |
|-----------|-------------|
| **Certificate** | X.509 digital certificate for TLS/SSL encryption |
| **Private Key** | Secret key paired with the certificate (never exposed) |
| **Certificate Chain** | Intermediate CA certificates for trust validation |
| **CSR** | Certificate Signing Request for new certificate issuance |

## Certificate Types

| Type | Description | Validation |
|------|-------------|------------|
| **DV (Domain Validated)** | Basic domain ownership verification | Email/DNS |
| **OV (Organization Validated)** | Organization identity verification | Business docs |
| **EV (Extended Validation)** | Highest level of identity verification | Extensive docs |

## Certificate Formats

| Format | Extension | Description |
|--------|-----------|-------------|
| **PEM** | `.pem`, `.crt` | Base64-encoded, most common |
| **DER** | `.der`, `.cer` | Binary format |
| **PKCS#12** | `.pfx`, `.p12` | Binary, includes private key |

## Server Types (for Download)

| Type | Description |
|------|-------------|
| **Nginx** | Nginx web server format |
| **Apache** | Apache HTTP Server format |
| **Tomcat** | Apache Tomcat (Java keystore) format |
| **IIS** | Microsoft IIS format |
| **Other** | Generic PEM format |

## Certificate Lifecycle

| State | Description |
|-------|-------------|
| `available` | Certificate is active and valid |
| `expiring` | Certificate approaching expiry (within 30 days) |
| `expired` | Certificate has passed its end date |
| `deleted` | Certificate has been removed |

## Key Security

1. **Private keys** must never be logged, printed, or stored in plaintext
2. Use SHA-256 fingerprint for certificate identification in logs
3. MFA is required for download and update operations
4. Delete operations should verify no active bindings exist

## Limits and Quotas

| Resource | Default Limit | Adjustable |
|----------|---------------|------------|
| Certificates per Account | Varies | Yes |

## Integration with Other Services

| Service | Integration |
|---------|-------------|
| **CLB** | HTTPS listeners bind certificates for TLS termination |
| **CDN** | CDN domains use certificates for HTTPS delivery |
| **WAF** | WAF instances may reference certificates |
| **DNS** | DNS validation records for domain ownership |

## Pricing Model

- **Uploaded certificates**: Free (bring your own cert)
- **Purchased certificates**: Based on type (DV/OV/EV) and validity period
