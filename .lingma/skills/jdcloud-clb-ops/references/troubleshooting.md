# JD Cloud CLB Troubleshooting

## Common Error Codes

| Error Code | Description | Solution |
|------------|-------------|----------|
| `InvalidParameter` | A required parameter is missing or invalid. | Check the CLI command syntax and required parameters. |
| `ResourceNotFound` | The specified CLB resource was not found. | Verify the CLB ID and region are correct. |
| `QuotaExceeded` | You have exceeded your CLB quota limit. | Request a quota increase or delete unused CLBs. |
| `InsufficientBalance` | Your account balance is insufficient. | Top up your JD Cloud account. |
| `ResourceConflict` | A resource with the same name already exists. | Use a unique name for the CLB resource. |
| `InternalError` | An internal error occurred in the CLB service. | Retry the operation; if persistent, contact support. |
| `OperationDenied` | The operation is denied due to insufficient permissions. | Check IAM policies and ensure proper permissions. |
| `InvalidCertificate` | Certificate format is invalid or corrupted. | Verify certificate is in PEM format and not corrupted. |
| `CertificateExpired` | Certificate has expired. | Upload a new valid certificate. |
| `KeyMismatch` | Private key doesn't match the certificate. | Ensure the private key corresponds to the certificate. |
| `DuplicateCertificate` | Certificate with same content already exists. | Use existing certificate or upload with different name. |

## Diagnostic Steps

### 1. Check CLB Status
```bash
jdc clb describe-clb \
  --clb-id clb-xxxxx \
  --region cn-north-1 \
  --output json
```

### 2. Verify Listener Configuration
```bash
jdc clb describe-listeners \
  --clb-id clb-xxxxx \
  --region cn-north-1 \
  --output json
```

### 3. Check Backend Server Health
```bash
jdc clb describe-backend-servers \
  --clb-id clb-xxxxx \
  --backend-server-group-id bsg-xxxxx \
  --region cn-north-1 \
  --output json
```

### 4. Test Network Connectivity
From a bastion host or management server:
```bash
# Test CLB IP reachability
ping <clb-ip-address>

# Test specific port
telnet <clb-ip-address> <port>
```

### 5. Review CLB Logs
Access CLB logs through JD Cloud Console or use the logging service to analyze traffic patterns and errors.

## Common Issues and Solutions

### CLB Cannot Be Accessed
1. Verify security group rules allow inbound traffic
2. Check if backend servers are healthy
3. Ensure listener is properly configured and started
4. Verify network ACLs are not blocking traffic

### Backend Servers Not Receiving Traffic
1. Check health check configuration and status
2. Verify backend servers are in the correct server group
3. Ensure network connectivity between CLB and backend servers
4. Check if backend servers are running and accessible

### High Latency or Connection Timeouts
1. Monitor CLB metrics for capacity issues
2. Check backend server performance
3. Verify network bandwidth and latency
4. Consider upgrading CLB specification

### SSL Certificate Issues
1. Verify certificate is valid and not expired
2. Check certificate chain completeness
3. Ensure certificate matches the domain name
4. Verify SSL listener configuration
5. Confirm private key matches certificate
6. Check certificate format (PEM)

#### Validate Certificate Format
```bash
# Check certificate validity
openssl x509 -in certificate.pem -noout -text

# Check expiration date
openssl x509 -in certificate.pem -noout -dates

# Verify private key matches certificate
openssl x509 -noout -modulus -in certificate.pem | openssl md5
openssl rsa -noout -modulus -in private-key.pem | openssl md5
# Both MD5 hashes should match
```

#### Test HTTPS Connection
```bash
# Test SSL handshake
echo | openssl s_client -connect <clb-ip>:443 -servername <domain> 2>/dev/null | openssl x509 -noout -dates

# Test with curl
curl -I https://<domain> --resolve <domain>:443:<clb-ip>

# Check certificate chain
echo | openssl s_client -connect <clb-ip>:443 -showcerts 2>/dev/null
```

## Performance Troubleshooting

### Monitor Key Metrics
- Connection count
- Bandwidth usage
- Request rate
- Response time
- Error rate

### Scale CLB Resources
- Upgrade CLB specification if under heavy load
- Add more backend servers to distribute load
- Optimize health check intervals

## Contact Support
If issues persist after following these troubleshooting steps, contact JD Cloud support with:
- CLB ID
- Error messages
- Timestamps of issues
- Steps already taken to resolve