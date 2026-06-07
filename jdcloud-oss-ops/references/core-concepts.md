# Core Concepts — JD Cloud Object Storage Service (OSS)

## Architecture Overview

JD Cloud Object Storage Service (OSS) is a scalable, durable, and secure cloud storage service. Data is stored as objects within buckets, distributed across multiple devices and facilities for high availability and durability.

### Key Components

| Component | Description |
|-----------|-------------|
| **Bucket** | A logical container for objects. Buckets are globally unique and region-scoped. |
| **Object** | The fundamental storage unit: file data + metadata (key, ETag, content-type, custom headers). |
| **Object Key** | The unique identifier for an object within a bucket (similar to a file path). |
| **Storage Class** | Defines the cost and access characteristics of stored objects. |
| **ACL** | Access Control List -- controls read/write permissions at bucket or object level. |

## Storage Classes

| Class | Durability | Availability | Min Object Size | Retrieval Time | Use Case |
|-------|-----------|-------------|----------------|----------------|----------|
| **Standard** | 99.9999999999% | 99.99% | 0 bytes | Immediate | Frequently accessed data, active workloads |
| **Infrequent Access (IA)** | 99.9999999999% | 99.9% | 128 KB | Immediate | Long-lived, infrequently accessed data |
| **Archive** | 99.9999999999% | 99.9% | 128 KB | 1-12 hours (restore) | Long-term archival, compliance data |

### Storage Class Comparison

| Feature | Standard | Infrequent Access | Archive |
|---------|----------|-------------------|---------|
| Storage Cost | High | Medium | Low |
| Retrieval Cost | Free | Per GB retrieved | Per GB restored |
| Minimum Billable Duration | 30 min | 30 days | 90 days |
| First Byte Latency | Milliseconds | Milliseconds | Minutes to hours |

## Bucket Naming Rules

- Length: 3-63 characters
- Must be globally unique across all JD Cloud regions
- Can contain lowercase letters, numbers, and hyphens (-)
- Must start and end with a letter or number
- Cannot contain underscores, uppercase letters, or periods
- Cannot be formatted as an IP address (e.g., 192.168.0.1)
- Recommended pattern: `<project>-<environment>-<purpose>-<region-code>`

Valid examples:
- `my-app-prod-logs-cn-north-1`
- `backup-data-2026`
- `static-assets-hosting`

## Access Control

### Bucket ACL

| ACL | Owner | Other Users | Public |
|-----|-------|-------------|--------|
| **private** | Full control | None | None |
| **public-read** | Full control | Read | Read |
| **public-read-write** | Full control | Read, Write | Read, Write |

> **Security Warning:** `public-read-write` should NEVER be used in production environments. Use `private` or presigned URLs for controlled access.

### Presigned URLs

Presigned URLs grant temporary access to specific objects for a limited time (1 second to 24 hours). They are safe to share and do not expose credentials.

## Lifecycle Policies

Lifecycle policies automate the management of objects over time:

| Action | Description |
|--------|-------------|
| **Transition** | Move objects to a different storage class after N days |
| **Expiration** | Delete objects after N days |
| **Non-current Version Transition** | Transition non-current object versions to lower-cost storage |
| **Non-current Version Expiration** | Delete non-current object versions after N days |
| **Abort Incomplete Multipart Upload** | Abort failed multipart uploads after N days |

## Object Operations

| Operation | Description | Idempotent |
|-----------|-------------|------------|
| PUT /{bucket}/{key} | Upload or overwrite an object | Yes (same key overwrites) |
| GET /{bucket}/{key} | Download an object | Yes |
| HEAD /{bucket}/{key} | Get object metadata | Yes |
| DELETE /{bucket}/{key} | Delete an object | Yes |

## Versioning

Versioning keeps multiple versions of an object in the same bucket:

- **Enabled:** Every object write creates a new version; deletes create a delete marker
- **Suspended:** New writes overwrite; existing versions are preserved
- **None:** Default state -- objects are overwritten or deleted permanently

## Cross-Region Replication (CRR)

CRR automatically replicates objects from a source bucket to a destination bucket in a different region:
- Source bucket must have versioning enabled
- Destination bucket must exist in a different region
- Replication scope: all objects or objects with a specific prefix

## Limits and Quotas

| Resource | Default Limit | Adjustable |
|----------|---------------|------------|
| Buckets per Account | 100 | Yes |
| Objects per Bucket | Unlimited | N/A |
| Object Size | 5 TB | N/A (5 GB via single PUT, >5 GB via multipart) |
| Bucket Name Length | 3-63 characters | Fixed |
| Presigned URL Expiration | 1 second - 24 hours | Configurable |

## Regions and Availability Zones

OSS is available in the following regions:

| Region ID | Region Name |
|-----------|-------------|
| cn-north-1 | 华北-北京 |
| cn-east-1 | 华东-宿迁 |
| cn-south-1 | 华南-广州 |
| cn-east-2 | 华东-上海 |

## Security Considerations

1. **Bucket ACL:** Use `private` for production buckets. Never use `public-read-write`.
2. **IAM Policies:** Use IAM policies for fine-grained access control instead of ACL.
3. **Encryption:** Enable server-side encryption (SSE-OSS or SSE-KMS) for sensitive data.
4. **Presigned URLs:** Use for temporary access; enforce short expiration times.
5. **Versioning:** Enable to protect against accidental overwrites and deletions.

## Integration with Other Services

| Service | Integration |
|---------|-------------|
| **CDN** | OSS can serve as origin for CDN to accelerate content delivery |
| **CloudMonitor** | Metrics for storage usage, request count, and latency |
| **IAM** | Policy-based access control for buckets and objects |
| **KMS** | Server-side encryption with KMS-managed keys |

## Pricing Model

OSS charges based on:
- **Storage:** Per GB per month (varies by storage class)
- **Requests:** Per PUT, GET, POST, HEAD, DELETE request
- **Data Transfer:** Outbound data transfer (inbound is free)
- **Retrieval:** Per GB retrieved from IA or Archive
- **CRR:** Per GB replicated across regions