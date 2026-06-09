# Function Compute Core Concepts

## Service (服务)
A logical grouping of functions. Services allow you to organize functions by application, environment, or team. Services can have shared configurations like VPC, environment variables, and log settings.

## Function (函数)
The basic unit of execution. A function contains:
- **Code**: Your business logic (uploaded as ZIP or from OSS)
- **Runtime**: Execution environment (Python, Node.js, Java, Go, etc.)
- **Handler**: Entry point (e.g., `index.handler`)
- **Configuration**: Memory, timeout, environment variables

## Version (版本)
Immutable snapshots of a function at a specific point in time. Versions are numbered (1, 2, 3...) and cannot be modified after creation. Use versions for:
- Rollback capabilities
- Stable deployments
- Audit trails

## Alias (别名)
Named pointers to versions. Aliases enable:
- Traffic shifting (canary deployments)
- Environment separation (dev, staging, prod)
- Rollback without code changes

## Trigger (触发器)
Event sources that invoke functions:
- **HTTP**: API Gateway or direct HTTP endpoint
- **Timer**: Scheduled execution (Cron expressions)
- **OSS**: Object Storage events
- **Log Service**: Log processing

## Execution Context
- **Cold start**: First invocation or after idle period; includes runtime initialization
- **Warm start**: Reusing existing execution environment; faster
- **Concurrency**: Multiple simultaneous invocations
- **Billing**: Per invocation + duration (GB-seconds)
