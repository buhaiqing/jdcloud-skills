# CLI — Audit Log (`jdc audit`)

## Install and config

- Install: see [JD Cloud CLI](https://github.com/jdcloud-api/jdcloud-cli)
- **CRITICAL:** The `jdc` CLI reads credentials exclusively from `~/.jdc/config` INI file, NOT from environment variables.
- For sandbox environments, redirect `HOME` and pre-create config files (see SKILL.md "Critical jdc CLI Behavioral Notes").

## Conventions (agent execution)

- `--output json` is a **top-level argument** — MUST be placed BEFORE the subcommand: `jdc --output json audit <command> ...`
- `--no-interactive` does NOT exist in `jdc` CLI — all commands are non-interactive by default; omit this flag.
- Document **exact** JSON paths after verifying with a real invocation (CLI output may differ from raw API).

## CLI vs API coverage gap

| Operation (API / SDK) | Available via `jdc`? | Notes |
|------------------------|---------------------|-------|
| Describe Events | Yes | `jdc audit describe-events` |
| Describe Event Detail | Yes | `jdc audit describe-event-detail` |
| Describe Trails | Yes | `jdc audit describe-trails` |

## Command map

| Goal | Example `jdc` invocation | Notes |
|------|--------------------------|-------|
| List Events | `jdc --output json audit describe-events --region-id cn-north-1 --start-time "2026-06-01T00:00:00+08:00" --end-time "2026-06-03T23:59:59+08:00"` | `--output json` BEFORE subcommand |
| List Events (Filtered) | `jdc --output json audit describe-events --region-id cn-north-1 --start-time ... --end-time ... --event-name CreateInstances --username admin` | Add filters as needed |
| Event Detail | `jdc --output json audit describe-event-detail --region-id cn-north-1 --event-id evt-xxx` | Get full event details |
| List Trails | `jdc --output json audit describe-trails --region-id cn-north-1` | List configured audit trails |

## JSON Path Reference

### Describe Events Response Paths

```json
{
  "result": {
    "events": [
      {
        "eventId": "evt-abc123",
        "eventTime": "2026-06-03T10:30:00+08:00",
        "eventName": "CreateInstances",
        "username": "admin",
        "resourceType": "vm",
        "resourceId": "i-xxx",
        "sourceIpAddress": "192.168.1.1",
        "userAgent": "jdcloud-sdk-python/1.6.26"
      }
    ],
    "totalCount": 100
  }
}
```

| Field | JSON Path | Example Value |
|-------|-----------|---------------|
| Event ID | `$.result.events[0].eventId` | `evt-abc123` |
| Event Time | `$.result.events[0].eventTime` | `2026-06-03T10:30:00+08:00` |
| Event Name | `$.result.events[0].eventName` | `CreateInstances` |
| Username | `$.result.events[0].username` | `admin` |
| Resource Type | `$.result.events[0].resourceType` | `vm` |
| Resource ID | `$.result.events[0].resourceId` | `i-xxx` |
| Source IP | `$.result.events[0].sourceIpAddress` | `192.168.1.1` |
| Total Count | `$.result.totalCount` | `100` |

### Describe Event Detail Response Paths

```json
{
  "result": {
    "eventDetail": {
      "eventId": "evt-abc123",
      "eventTime": "2026-06-03T10:30:00+08:00",
      "eventName": "CreateInstances",
      "username": "admin",
      "resourceType": "vm",
      "resourceId": "i-xxx",
      "sourceIpAddress": "192.168.1.1",
      "userAgent": "jdcloud-sdk-python/1.6.26",
      "requestParameters": {
        "instanceType": "g.n2.medium",
        "imageId": "img-xxx"
      },
      "responseElements": {
        "instanceId": "i-xxx"
      },
      "errorCode": null,
      "errorMessage": null
    }
  }
}
```

| Field | JSON Path | Example Value |
|-------|-----------|---------------|
| Event ID | `$.result.eventDetail.eventId` | `evt-abc123` |
| Request Params | `$.result.eventDetail.requestParameters` | `{...}` |
| Response | `$.result.eventDetail.responseElements` | `{...}` |
| Error Code | `$.result.eventDetail.errorCode` | `null` or error code |
| Error Message | `$.result.eventDetail.errorMessage` | `null` or message |
