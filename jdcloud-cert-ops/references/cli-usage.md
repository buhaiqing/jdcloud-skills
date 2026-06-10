# CLI — JD Cloud SSL Certificate (`jdc`)

## Install and Config

- Install: see [JD Cloud CLI](https://github.com/jdcloud-api/jdcloud-cli)
- **CRITICAL:** `jdc` reads credentials exclusively from `~/.jdc/config` INI file, NOT from env vars.
- For sandbox environments, redirect `HOME` and pre-create config files (see SKILL.md §Sandbox Config).

## Conventions

- `--output json` is a **top-level argument** — MUST be placed BEFORE the subcommand: `jdc --output json ssl <command> ...`
- `--no-interactive` does NOT exist in `jdc` CLI — omit this flag.

## CLI vs API Coverage Gap

| Operation | `jdc ssl` | Notes |
|-----------|-----------|-------|
| Upload Certificate | `upload-cert` | Requires cert file path and key file path |
| Describe Certificates | `describe-certs` | Supports domain name and cert ID filters |
| Describe Certificate | `describe-cert` | Detail view of single cert |
| Download Certificate | `download-cert` | [MFA enabled]; requires server type |
| Update Certificate Name | `update-cert-name` | Rename only |
| Update Certificate | `update-cert` | [MFA enabled]; replaces cert and key |
| Delete Certificate | `delete-certs` | [MFA enabled]; irreversible |

## Command Map

### Certificate Operations

| Goal | `jdc` Invocation |
|------|-----------------|
| Upload | `jdc --output json ssl upload-cert --cert-name <name> --cert-file <path> --key-file <path> [--alias-name <alias>]` |
| List All | `jdc --output json ssl describe-certs --page-number 1 --page-size 100` |
| List by Domain | `jdc --output json ssl describe-certs --domain-name <domain>` |
| Detail | `jdc --output json ssl describe-cert --cert-id <id>` |
| Download | `jdc --output json ssl download-cert --cert-id <id> --server-type <Nginx\|Apache\|Tomcat\|IIS\|Other>` |
| Rename | `jdc --output json ssl update-cert-name --cert-id <id> --cert-name <new-name>` |
| Update Content | `jdc --output json ssl update-cert --cert-id <id> --cert-file <path> --key-file <path>` |
| Delete | `jdc --output json ssl delete-certs --cert-id <id>` |

## JSON Response Paths

### Upload Certificate
```json
{"requestId": "...", "result": {"certId": "cert-xxx"}}
```
- `$.result.certId` — New certificate ID

### Describe Certificates (List)
```json
{"requestId": "...", "result": {"certListDetails": [{"certId": "cert-xxx", "domainName": "example.com", "issuer": "Let's Encrypt", "startDate": "2026-01-01", "endDate": "2026-07-01"}], "totalCount": 1}}
```
- `$.result.certListDetails[*].certId` — Certificate IDs
- `$.result.certListDetails[*].domainName` — Domain names
- `$.result.certListDetails[*].endDate` — Expiry dates

### Describe Certificate (Detail)
```json
{"requestId": "...", "result": {"certId": "cert-xxx", "domainName": "example.com", "certType": "DV", "issuer": "Let's Encrypt", "startDate": "2026-01-01", "endDate": "2026-07-01"}}
```
- `$.result.certId` — Certificate ID
- `$.result.domainName` — Domain name
- `$.result.endDate` — Expiry date

### Download Certificate
```json
{"requestId": "...", "result": {"certInfo": {"certFile": "...", "keyFile": "..."}}}
```
- `$.result.certInfo.certFile` — Certificate content
- `$.result.certInfo.keyFile` — Private key content

## Common CLI Patterns

### Sandbox Setup
```bash
export HOME=/tmp/jdc-home
mkdir -p /tmp/jdc-home/.jdc
cat > /tmp/jdc-home/.jdc/config << 'CONFIGEOF'
[default]
access_key = YOUR_ACCESS_KEY
secret_key = YOUR_SECRET_KEY
region_id = cn-north-1
endpoint = ssl.jdcloud-api.com
scheme = https
timeout = 20
CONFIGEOF
printf "%s" "default" > /tmp/jdc-home/.jdc/current
```

### Certificate Expiry Check (one-liner)
```bash
# List certs and filter by expiry (requires jq)
jdc --output json ssl describe-certs --page-number 1 --page-size 100 | \
  jq -r '.result.certListDetails[] | "\(.certId) \(.domainName) \(.endDate)"'
```
