# JD Cloud CLB SSL Certificate Management Best Practices

## Overview
This guide provides comprehensive best practices for managing SSL/TLS certificates with JD Cloud CLB, including security recommendations, automation strategies, and compliance guidelines.

## Certificate Lifecycle Management

### 1. Certificate Acquisition
- **Use Trusted CAs**: Obtain certificates from reputable Certificate Authorities (Let's Encrypt, DigiCert, GlobalSign, etc.)
- **Certificate Type Selection**:
  - **Domain Validation (DV)**: For basic encryption needs
  - **Organization Validation (OV)**: For business websites requiring identity verification
  - **Extended Validation (EV)**: For high-security applications requiring maximum trust
- **Wildcard Certificates**: Use `*.example.com` for multiple subdomains (cost-effective but higher risk if compromised)

### 2. Certificate Upload Process

#### Pre-upload Validation Checklist
```bash
# 1. Verify certificate format (PEM)
openssl x509 -in cert.pem -text -noout

# 2. Check expiration date
openssl x509 -in cert.pem -noout -dates

# 3. Verify domain coverage
openssl x509 -in cert.pem -noout -subject -ext subjectAltName

# 4. Validate private key matches certificate
CERT_MODULUS=$(openssl x509 -noout -modulus -in cert.pem | openssl md5)
KEY_MODULUS=$(openssl rsa -noout -modulus -in key.pem | openssl md5)
[ "$CERT_MODULUS" = "$KEY_MODULUS" ] && echo "Match" || echo "Mismatch"

# 5. Check certificate chain completeness
openssl verify -CAfile ca-bundle.crt cert.pem
```

#### Secure File Handling
- Store certificate files with restricted permissions: `chmod 600 *.pem`
- Never commit certificates to version control systems
- Use encrypted storage for certificate backups
- Implement secure deletion after upload (`shred` command)

### 3. Certificate Rotation Strategy

#### Automated Rotation Workflow
1. **Proactive Monitoring**: Set alerts at 30, 14, and 7 days before expiration
2. **Preparation Phase** (30 days before):
   - Request new certificate from CA
   - Validate new certificate locally
   - Upload to JD Cloud CLB with different name
3. **Testing Phase** (14 days before):
   - Test new certificate on staging environment
   - Verify all domains and SANs work correctly
   - Test with various client types (browsers, mobile apps, APIs)
4. **Deployment Phase** (7 days before):
   - Schedule maintenance window
   - Update HTTPS listener with new certificate
   - Monitor for errors during transition
5. **Cleanup Phase** (after successful rotation):
   - Verify old certificate is no longer in use
   - Delete old certificate from CLB
   - Archive old certificate securely for audit trail

#### Zero-Downtime Rotation
```bash
# Step 1: Upload new certificate
jdc clb upload-certificate \
  --region cn-north-1 \
  --certificate-name "prod-cert-2026-v2" \
  --certificate-content "$(cat new-cert.pem)" \
  --private-key "$(cat new-key.pem)" \
  --output json

# Step 2: Update listener (atomic operation)
jdc clb modify-listener \
  --clb-id clb-xxxxx \
  --listener-id listener-xxxxx \
  --region cn-north-1 \
  --certificate-id cert-yyyyy \
  --output json

# Step 3: Verify immediately
curl -I https://your-domain.com --resolve your-domain.com:443:<clb-ip>
```

## Security Best Practices

### 1. TLS Protocol Configuration
- **Recommended SSL Policy**: `tls-1-2` or `tls-1-3`
- **Deprecated Protocols**: Disable TLS 1.0 and 1.1 (PCI DSS compliance)
- **Cipher Suite Selection**:
  - Prioritize ECDHE and AES-GCM ciphers
  - Avoid RC4, DES, 3DES, MD5
  - Enable Perfect Forward Secrecy (PFS)

#### Recommended Cipher Suites (TLS 1.2)
```
ECDHE-ECDSA-AES256-GCM-SHA384
ECDHE-RSA-AES256-GCM-SHA384
ECDHE-ECDSA-CHACHA20-POLY1305
ECDHE-RSA-CHACHA20-POLY1305
ECDHE-ECDSA-AES128-GCM-SHA256
ECDHE-RSA-AES128-GCM-SHA256
```

### 2. Certificate Chain Management
- **Include Intermediate Certificates**: Upload full chain (server + intermediate CAs)
- **Chain Order**: Server cert → Intermediate CA(s) → Root CA (optional)
- **Validate Chain**: Ensure clients can build complete trust chain

```bash
# Create certificate bundle
cat server.crt intermediate-ca.crt > full-chain.pem

# Verify chain
openssl verify -CAfile root-ca.crt -untrusted intermediate-ca.crt server.crt
```

### 3. HSTS Implementation
- Enable HTTP Strict Transport Security (HSTS) on backend servers
- Recommended header: `Strict-Transport-Security: max-age=31536000; includeSubDomains; preload`
- Ensures browsers always use HTTPS

### 4. OCSP Stapling
- Enable OCSP stapling on CLB if supported
- Improves SSL handshake performance
- Reduces latency for certificate validation

## Monitoring and Alerting

### 1. Certificate Expiration Monitoring

#### CLI-based Check
```bash
#!/bin/bash
# Check certificate expiration
CERT_ID="cert-xxxxx"
EXPIRY_DATE=$(jdc clb describe-certificate \
  --certificate-id $CERT_ID \
  --region cn-north-1 \
  --output json | jq -r '.data.expireTime')

EXPIRY_EPOCH=$(date -d "$EXPIRY_DATE" +%s)
CURRENT_EPOCH=$(date +%s)
DAYS_REMAINING=$(( (EXPIRY_EPOCH - CURRENT_EPOCH) / 86400 ))

echo "Certificate expires in $DAYS_REMAINING days"

if [ $DAYS_REMAINING -lt 7 ]; then
  echo "CRITICAL: Certificate expires in less than 7 days!"
  exit 2
elif [ $DAYS_REMAINING -lt 30 ]; then
  echo "WARNING: Certificate expires in less than 30 days!"
  exit 1
fi
```

#### Cloud Monitor Alert Rule
```json
{
  "alarmName": "ssl-cert-expiration-warning",
  "namespace": "JDCloud/CLB",
  "metricName": "CertificateExpirationDays",
  "statistic": "Minimum",
  "period": 86400,
  "threshold": 30,
  "comparisonOperator": "LessThanThreshold",
  "evaluationPeriods": 1,
  "alarmActions": [
    "arn:aws:sns:cn-north-1:123456789012:ssl-alerts"
  ]
}
```

### 2. SSL Handshake Monitoring
- Monitor SSL handshake failure rate
- Track TLS version distribution
- Identify clients using deprecated protocols

### 3. Performance Metrics
- SSL handshake time
- Certificate validation time
- Impact of different cipher suites on performance

## Compliance and Audit

### 1. Regulatory Requirements
- **PCI DSS**: Requires TLS 1.2+, strong cipher suites, annual certificate audits
- **HIPAA**: Encryption in transit for protected health information
- **GDPR**: Appropriate security measures for personal data transmission
- **SOC 2**: Documented certificate management procedures

### 2. Audit Trail
Maintain records of:
- Certificate issuance dates and sources
- Upload timestamps and operators
- Rotation history and reasons
- Incident reports for certificate-related issues
- Decommissioning records

### 3. Access Control
- Implement least-privilege IAM policies for certificate operations
- Require MFA for certificate management actions
- Log all certificate upload/delete operations
- Regular access reviews for certificate management permissions

## Automation Strategies

### 1. Infrastructure as Code (Terraform)
```hcl
resource "jdcloud_clb_certificate" "main" {
  certificate_name    = "prod-web-cert"
  certificate_content = file("${path.module}/certs/server.crt")
  private_key         = file("${path.module}/certs/server.key")
  region              = "cn-north-1"
}

resource "jdcloud_clb_listener" "https" {
  clb_id                 = jdcloud_clb.main.id
  listener_name          = "https-listener"
  protocol               = "HTTPS"
  listener_port          = 443
  backend_server_group_id = jdcloud_clb_backend_server_group.main.id
  certificate_id         = jdcloud_clb_certificate.main.id
  ssl_policy             = "tls-1-2"
}
```

### 2. CI/CD Integration
```yaml
# GitHub Actions example for automated certificate deployment
name: Deploy SSL Certificate
on:
  schedule:
    - cron: '0 0 * * 0'  # Weekly check
  workflow_dispatch:

jobs:
  check-and-update:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Check Certificate Expiration
        run: |
          EXPIRY=$(openssl x509 -enddate -noout -in cert.pem | cut -d= -f2)
          EXPIRY_EPOCH=$(date -d "$EXPIRY" +%s)
          CURRENT_EPOCH=$(date +%s)
          DAYS_LEFT=$(( (EXPIRY_EPOCH - CURRENT_EPOCH) / 86400 ))
          
          if [ $DAYS_LEFT -lt 30 ]; then
            echo "Certificate expires in $DAYS_LEFT days. Initiating renewal..."
            echo "NEEDS_RENEWAL=true" >> $GITHUB_ENV
          fi
      
      - name: Renew Certificate (if needed)
        if: env.NEEDS_RENEWAL == 'true'
        run: |
          # Use Let's Encrypt or your CA's API
          certbot renew --force-renewal
          
      - name: Upload to JD Cloud CLB
        if: env.NEEDS_RENEWAL == 'true'
        run: |
          pip install jdcloud-cli
          jdc config init --access-key ${{ secrets.JDC_ACCESS_KEY }} \
                          --secret-key ${{ secrets.JDC_SECRET_KEY }}
          
          jdc clb upload-certificate \
            --region cn-north-1 \
            --certificate-name "auto-renewed-cert-$(date +%Y%m%d)" \
            --certificate-content "$(cat fullchain.pem)" \
            --private-key "$(cat privkey.pem)" \
            --output json
```

### 3. Automated Testing
```python
import subprocess
import sys

def test_ssl_certificate(clb_ip, domain):
    """Test SSL certificate configuration"""
    
    # Test 1: Check certificate served
    result = subprocess.run([
        'openssl', 's_client',
        '-connect', f'{clb_ip}:443',
        '-servername', domain
    ], input=b'', capture_output=True)
    
    cert_info = subprocess.run([
        'openssl', 'x509', '-noout', '-dates', '-subject'
    ], input=result.stdout, capture_output=True, text=True)
    
    print("Certificate Info:")
    print(cert_info.stdout)
    
    # Test 2: Check TLS version
    for tls_version in ['tls1', 'tls1_1', 'tls1_2', 'tls1_3']:
        result = subprocess.run([
            'openssl', 's_client',
            '-connect', f'{clb_ip}:443',
            '-servername', domain,
            f'-{tls_version}'
        ], input=b'', capture_output=True)
        
        status = "✓ Supported" if result.returncode == 0 else "✗ Not supported"
        print(f"{tls_version}: {status}")
    
    # Test 3: Check cipher suites
    result = subprocess.run([
        'nmap', '--script', 'ssl-enum-ciphers',
        '-p', '443', clb_ip
    ], capture_output=True, text=True)
    
    print("\nCipher Suites:")
    print(result.stdout)

if __name__ == '__main__':
    test_ssl_certificate(sys.argv[1], sys.argv[2])
```

## Troubleshooting Common Issues

### Issue 1: Certificate Not Recognized
**Symptoms**: Browser shows "Invalid Certificate" error

**Resolution**:
1. Verify certificate chain is complete
2. Check certificate format (must be PEM)
3. Ensure certificate matches the domain
4. Verify intermediate certificates are included

### Issue 2: Mixed Content Warnings
**Symptoms**: HTTPS page loads but shows security warnings

**Resolution**:
1. Ensure all resources (images, scripts, stylesheets) use HTTPS
2. Update hardcoded HTTP URLs to HTTPS or protocol-relative URLs
3. Implement Content Security Policy (CSP) headers

### Issue 3: SSL Handshake Failures
**Symptoms**: Clients cannot establish HTTPS connection

**Resolution**:
1. Check TLS protocol compatibility
2. Verify cipher suite support on client side
3. Review CLB SSL policy configuration
4. Check for firewall/proxy interference

### Issue 4: Certificate Name Mismatch
**Symptoms**: "Certificate name mismatch" error

**Resolution**:
1. Verify certificate CN and SANs match the domain
2. Check for www vs non-www discrepancies
3. Ensure wildcard certificates cover the subdomain
4. Use correct domain in DNS resolution

## Performance Optimization

### 1. Session Resumption
- Enable TLS session tickets for faster reconnections
- Configure appropriate session timeout (typically 1 hour)
- Monitor session cache hit rate

### 2. OCSP Stapling
- Reduces certificate validation latency
- Improves initial connection time
- Decreases load on CA's OCSP responders

### 3. Certificate Size
- Use ECDSA certificates (smaller than RSA, same security level)
- Minimize certificate chain length
- Compress certificate data where possible

### 4. Connection Reuse
- Enable HTTP/2 for multiplexing
- Configure appropriate keep-alive timeouts
- Monitor connection reuse rates

## Disaster Recovery

### 1. Certificate Backup Strategy
- Maintain offline backups of all certificates and private keys
- Store backups in geographically distributed locations
- Encrypt backups with strong encryption (AES-256)
- Test restoration procedures regularly

### 2. Emergency Rollback Plan
```bash
# Keep track of previous certificate ID
OLD_CERT_ID="cert-xxxxx"
NEW_CERT_ID="cert-yyyyy"

# If new certificate causes issues, rollback immediately
jdc clb modify-listener \
  --clb-id clb-xxxxx \
  --listener-id listener-xxxxx \
  --region cn-north-1 \
  --certificate-id $OLD_CERT_ID \
  --output json
```

### 3. Incident Response
1. **Detection**: Monitor alerts for certificate issues
2. **Assessment**: Determine scope and impact
3. **Containment**: Rollback to working certificate if needed
4. **Resolution**: Fix underlying issue and deploy corrected certificate
5. **Post-mortem**: Document incident and update procedures

## Resources and References

- [JD Cloud CLB Documentation](https://docs.jdcloud.com/clb)
- [Mozilla SSL Configuration Generator](https://ssl-config.mozilla.org/)
- [SSL Labs Server Test](https://www.ssllabs.com/ssltest/)
- [Let's Encrypt Documentation](https://letsencrypt.org/docs/)
- [OWASP TLS Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Transport_Layer_Protection_Cheat_Sheet.html)

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-04-28 | Initial SSL certificate management best practices guide |
