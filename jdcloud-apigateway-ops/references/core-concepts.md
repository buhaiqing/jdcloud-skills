# API Gateway Core Concepts

## API Group (API分组)
A logical container for related APIs. An API group allows you to organize APIs by application, service, or version. All APIs within a group share the same base domain and can be managed together.

Key attributes:
- **Group Name**: Unique identifier within a region (1–128 characters)
- **Group ID**: System-generated unique identifier
- **Status**: `Active`, `Deleting`
- **Domain**: Each group gets a default subdomain for API invocation

## API (API接口)
The basic unit of an API Gateway configuration. An API defines:
- **Request Configuration**: Path, method, protocol (HTTP/HTTPS) that clients use
- **Service Configuration**: Backend service details (address, path, timeout)
- **Authentication**: How callers are authenticated
- **Status Lifecycle**: `UnDeployed` → `Deployed` (per stage)

### Request Configuration
| Field | Description | Example |
|-------|-------------|---------|
| `requestPath` | Client-facing path | `/users/{id}` |
| `requestMethod` | HTTP method | `GET`, `POST`, `PUT`, `DELETE` |
| `requestProtocol` | Protocol | `HTTP`, `HTTPS`, `HTTP_HTTPS` |

### Service Configuration
| Field | Description | Example |
|-------|-------------|---------|
| `serviceProtocol` | Backend protocol | `HTTP`, `HTTPS`, `FC`, `MOCK` |
| `serviceAddress` | Backend URL | `http://backend.internal:8080` |
| `servicePath` | Backend path | `/api/users/{id}` |
| `serviceMethod` | Backend HTTP method | `GET` |
| `serviceTimeout` | Timeout in milliseconds | `10000` |

## Stage (环境)
Deployment environments that represent different release stages of an API:
- **test**: Development and testing environment
- **pre**: Pre-production / staging environment
- **prod**: Production environment

Each API can be deployed independently to different stages. Deploying to a stage creates a runtime instance of the API accessible via the stage-specific URL.

### Stage URL Format
```
https://{apiGroupId}.apigateway.jdcloud-api.com/{stageName}{requestPath}
```

## Throttling Policy (流控策略)
Rate limiting configuration that controls how many requests an API can handle:
- **API-level limit**: Total requests allowed for the API
- **App-level limit**: Requests allowed per calling application
- **Time unit**: `second`, `minute`, `hour`, `day`

Policies are bound to specific APIs and stages. Multiple APIs can share the same policy.

## Authentication Types

### no_auth (开放认证)
No authentication required. Suitable for public APIs, health checks, or webhook receivers.
- **Risk**: Anyone can call the API
- **Use case**: Public data APIs, health endpoints

### app_auth (应用认证)
API key-based authentication. Callers must provide a valid AppKey and AppSecret.
- **Security**: Medium; keys can be rotated
- **Use case**: Partner APIs, third-party integrations

### jdcloud_auth (京东云认证)
IAM-based authentication using JD Cloud credentials.
- **Security**: High; leverages IAM policies
- **Use case**: Internal services, microservice communication

## Backend Types

### HTTP/HTTPS
Forwards requests to HTTP backend services. Most common backend type.

### FC (Function Compute)
Triggers JD Cloud Function Compute functions. The API Gateway passes the request event to the function.
- Requires function to exist in the same region
- Supports async and sync invocation modes

### MOCK
Returns a configured static response without calling a backend.
- **Use case**: API prototyping, testing, health checks
- **Configuration**: Response body, status code, headers

## Deployment Lifecycle
```
Create API → UnDeployed
    ↓
Deploy to Stage → Deployed
    ↓
Modify API → UnDeployed (on that stage)
    ↓
Redeploy to Stage → Deployed (new version)
    ↓
Undeploy from Stage → UnDeployed
```

## Parameter Mapping
API Gateway supports path parameter mapping between client-facing URLs and backend URLs:
- Client path: `/products/{productId}`
- Backend path: `/api/v1/items/{productId}`
- Parameters are automatically forwarded
