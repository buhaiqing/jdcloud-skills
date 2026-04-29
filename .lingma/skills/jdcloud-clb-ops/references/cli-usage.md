# JD Cloud CLB CLI Usage

## Installation
```bash
pip install jdcloud-cli
jdc config init
```

## Basic Commands

### CLB Instance Management

#### Create CLB Instance
```bash
jdc clb create-clb \
  --region cn-north-1 \
  --clb-name "my-clb" \
  --clb-specification "2" \
  --network-type "BGP" \
  --output json \
  --no-interactive
```

#### Describe CLB Instance
```bash
jdc clb describe-clb \
  --clb-id clb-xxxxx \
  --region cn-north-1 \
  --output json
```

#### List CLB Instances
```bash
jdc clb describe-clbs \
  --region cn-north-1 \
  --output json
```

#### Delete CLB Instance
```bash
jdc clb delete-clb \
  --clb-id clb-xxxxx \
  --region cn-north-1 \
  --output json \
  --no-interactive
```

### Listener Management

#### Create Listener
```bash
jdc clb create-listener \
  --clb-id clb-xxxxx \
  --listener-name "http-listener" \
  --protocol "HTTP" \
  --listener-port 80 \
  --backend-server-group-id bsg-xxxxx \
  --region cn-north-1 \
  --output json \
  --no-interactive
```

#### Describe Listeners
```bash
jdc clb describe-listeners \
  --clb-id clb-xxxxx \
  --region cn-north-1 \
  --output json
```

#### Delete Listener
```bash
jdc clb delete-listener \
  --clb-id clb-xxxxx \
  --listener-id listener-xxxxx \
  --region cn-north-1 \
  --output json \
  --no-interactive
```

### Backend Server Group Management

#### Create Backend Server Group
```bash
jdc clb create-backend-server-group \
  --clb-id clb-xxxxx \
  --group-name "web-servers" \
  --region cn-north-1 \
  --output json \
  --no-interactive
```

#### Add Backend Servers
```bash
jdc clb add-backend-servers \
  --clb-id clb-xxxxx \
  --backend-server-group-id bsg-xxxxx \
  --backend-servers "[{\"backendServerId\":\"vm-xxxxx\",\"weight\":10}]" \
  --region cn-north-1 \
  --output json \
  --no-interactive
```

### Health Check Management

#### Configure Health Check
```bash
jdc clb modify-health-check \
  --clb-id clb-xxxxx \
  --listener-id listener-xxxxx \
  --health-check-type "HTTP" \
  --health-check-url "/health" \
  --health-check-port 80 \
  --healthy-threshold 3 \
  --unhealthy-threshold 3 \
  --health-check-timeout 5 \
  --health-check-interval 5 \
  --region cn-north-1 \
  --output json \
  --no-interactive
```

### SSL Certificate Management

#### Upload SSL Certificate
```bash
# Upload certificate from files
jdc clb upload-certificate \
  --region cn-north-1 \
  --certificate-name "my-domain-cert" \
  --certificate-content "$(cat /path/to/certificate.pem)" \
  --private-key "$(cat /path/to/private-key.pem)" \
  --output json \
  --no-interactive
```

#### List SSL Certificates
```bash
jdc clb describe-certificates \
  --region cn-north-1 \
  --output json
```

#### Describe Specific Certificate
```bash
jdc clb describe-certificate \
  --certificate-id cert-xxxxx \
  --region cn-north-1 \
  --output json
```

#### Update HTTPS Listener with New Certificate
```bash
jdc clb modify-listener \
  --clb-id clb-xxxxx \
  --listener-id listener-xxxxx \
  --region cn-north-1 \
  --certificate-id cert-yyyyy \
  --output json \
  --no-interactive
```

#### Delete SSL Certificate
```bash
jdc clb delete-certificate \
  --certificate-id cert-xxxxx \
  --region cn-north-1 \
  --output json \
  --no-interactive
```

#### Create HTTPS Listener with SSL Certificate
```bash
jdc clb create-listener \
  --clb-id clb-xxxxx \
  --listener-name "https-listener" \
  --protocol "HTTPS" \
  --listener-port 443 \
  --backend-server-group-id bsg-xxxxx \
  --certificate-id cert-xxxxx \
  --ssl-policy "tls-1-2" \
  --region cn-north-1 \
  --output json \
  --no-interactive
```

## Advanced Usage

### Query CLB Metrics
```bash
jdc clb describe-clb-metrics \
  --clb-id clb-xxxxx \
  --start-time "2026-04-28T00:00:00+08:00" \
  --end-time "2026-04-28T23:59:59+08:00" \
  --metric-name "NewConn" \
  --region cn-north-1 \
  --output json
```

### Configure ACL for CLB
```bash
jdc clb modify-clb-attributes \
  --clb-id clb-xxxxx \
  --acl-id acl-xxxxx \
  --region cn-north-1 \
  --output json \
  --no-interactive
```

## Output Format
All commands support `--output json` for machine-readable output. The response typically includes:
- `requestId`: Unique identifier for the API call
- `data`: Response data containing resource information
- `error`: Error information if the operation failed

## Tips
- Always use `--no-interactive` flag for automation
- Use `--output json` for parsing responses programmatically
- Check return codes to handle errors appropriately
- Use `--help` flag to see all available options for each command