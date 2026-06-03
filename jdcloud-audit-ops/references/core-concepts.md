# Core Concepts — JD Cloud Audit Log

## What is Audit Log?

JD Cloud Audit Log (操作审计/云审计) is a service that records and tracks user operations and API calls made on JD Cloud resources. It provides a comprehensive audit trail for:

- **Security Analysis:** Detect unauthorized access or suspicious activities
- **Compliance Auditing:** Meet regulatory requirements with detailed operation records
- **Operational Troubleshooting:** Investigate issues by reviewing what changes were made
- **Accountability:** Track who performed what actions and when

## Key Concepts

### Event

An **Event** represents a single recorded operation or API call. Each event contains:

| Attribute | Description |
|-----------|-------------|
| Event ID | Unique identifier for the event (e.g., `evt-abc123`) |
| Event Time | Timestamp when the operation occurred (ISO 8601) |
| Event Name | The operation/API name (e.g., `CreateInstances`, `DeleteInstance`) |
| Username | User who performed the action |
| Resource Type | Type of resource affected (e.g., `vm`, `vpc`, `rds`) |
| Resource ID | Specific resource identifier |
| Source IP | IP address from which the request originated |
| User Agent | Client SDK or tool used |
| Request Parameters | Input parameters of the API call |
| Response Elements | Output/result of the operation |
| Error Code | Error code if operation failed |
| Error Message | Detailed error message if operation failed |

### Trail

A **Trail** is a configuration that determines how audit events are captured and stored. Trails can:

- Record events to specific storage (e.g., Object Storage Service)
- Filter events by resource type or operation type
- Enable/disable auditing for specific services

### Event Types

Audit Log captures various types of events:

| Event Category | Examples |
|----------------|----------|
| Console Operations | Web console login, resource creation via UI |
| API Calls | Direct API invocations via SDK or CLI |
| System Events | Automated operations by JD Cloud services |
| Scheduled Actions | Cron-based or scheduled operations |

### Common Event Names

| Event Name | Description |
|------------|-------------|
| `CreateInstances` | Create VM instances |
| `DeleteInstance` | Delete a VM instance |
| `StartInstance` | Start a stopped VM |
| `StopInstance` | Stop a running VM |
| `CreateVpc` | Create a VPC |
| `DeleteVpc` | Delete a VPC |
| `CreateSubnet` | Create a subnet |
| `CreateSecurityGroup` | Create a security group |
| `CreateRDSInstance` | Create an RDS instance |
| `CreateAccessKey` | Create an access key |
| `CreateSubUser` | Create an IAM sub-user |
| `AttachPolicy` | Attach a policy to user/group/role |

## Time Range Queries

Audit Log queries require a time range specified as ISO 8601 timestamps:

```
Format: YYYY-MM-DDTHH:MM:SS+HH:MM
Example: 2026-06-03T10:30:00+08:00
```

**Important Constraints:**

- Maximum query window: typically 90 days
- Start time must be before end time
- Both times should include timezone offset
- Events older than retention period may not be available

## Retention Policy

Audit Log retention policies determine how long events are stored:

| Storage Type | Typical Retention |
|--------------|-------------------|
| Platform Default | 90 days |
| Custom Trail (OSS) | Configurable, up to several years |

## Security Considerations

1. **Sensitive Data:** Audit logs may contain sensitive information in request/response parameters
2. **Access Control:** Only authorized users should be able to query audit logs
3. **Tamper Evidence:** Audit logs should be immutable once recorded
4. **Encryption:** Events in transit and at rest should be encrypted

## Use Cases

### Security Investigation

```
Scenario: Detect unauthorized access
Approach: Query events by unusual source IP or after-hours activity
```

### Compliance Reporting

```
Scenario: Generate monthly compliance report
Approach: Query all events for the month, export to CSV/JSON
```

### Operational Debugging

```
Scenario: Investigate why a resource was deleted
Approach: Query Delete events for the resource type, filter by time range
```

### Change Tracking

```
Scenario: Track configuration changes over time
Approach: Query Modify/Update events for specific resources
```

## Cross-Service Integration

Audit Log integrates with other JD Cloud services:

| Service | Integration |
|---------|-------------|
| Cloud Monitor | Metrics on audit event volume |
| Object Storage | Long-term event archival |
| IAM | Permission control for audit access |
| Message Queue | Real-time event streaming (if supported) |
