# API & SDK — JD Cloud Object Storage Service (OSS)

## OpenAPI Specification

- **Base URL**: `https://oss.jdcloud-api.com/v1`
- **API Version**: v1
- **Protocol**: HTTPS
- **Authentication**: Access Key + Secret Key (HMAC-SHA256)
- **Endpoint**: `oss.jdcloud-api.com`

## SDK Operations Map

| Goal | API Operation ID | SDK Method / Request | Notes |
|------|-----------------|---------------------|-------|
| Create Bucket | createBucket | `CreateBucketRequest` | Globally unique name required |
| List Buckets | listBuckets | `ListBucketsRequest` | Returns all buckets for account |
| Head Bucket | headBucket | `HeadBucketRequest` | Quick existence + metadata check |
| Delete Bucket | deleteBucket | `DeleteBucketRequest` | Bucket must be empty |
| Put Bucket ACL | putBucketAcl | `PutBucketAclRequest` | private / public-read / public-read-write |
| Get Bucket ACL | getBucketAcl | `GetBucketAclRequest` | Returns current ACL |
| Put Bucket Lifecycle | putBucketLifecycle | `PutBucketLifecycleRequest` | Set lifecycle rules |
| Get Bucket Lifecycle | getBucketLifecycle | `GetBucketLifecycleRequest` | Get current lifecycle rules |
| Delete Bucket Lifecycle | deleteBucketLifecycle | `DeleteBucketLifecycleRequest` | Remove lifecycle rules |
| Put Bucket Versioning | putBucketVersioning | `PutBucketVersioningRequest` | Enable / suspend versioning |
| Get Bucket Versioning | getBucketVersioning | `GetBucketVersioningRequest` | Get versioning status |
| Put Bucket Replication | putBucketReplication | `PutBucketReplicationRequest` | Configure CRR |
| Get Bucket Replication | getBucketReplication | `GetBucketReplicationRequest` | Get CRR config |
| Put Object | putObject | `PutObjectRequest` | Upload single object (<= 5 GB) |
| Get Object | getObject | `GetObjectRequest` | Download object |
| Head Object | headObject | `HeadObjectRequest` | Get object metadata |
| Delete Object | deleteObject | `DeleteObjectRequest` | Delete single object |
| Delete Multiple Objects | deleteMultipleObjects | `DeleteMultipleObjectsRequest` | Batch delete |
| List Objects | listObjects | `ListObjectsRequest` | List objects with prefix/delimiter |
| Copy Object | copyObject | `CopyObjectRequest` | Copy object within or across buckets |
| Initiate Multipart Upload | initiateMultipartUpload | `InitiateMultipartUploadRequest` | Start multipart upload |
| Upload Part | uploadPart | `UploadPartRequest` | Upload a part |
| Complete Multipart Upload | completeMultipartUpload | `CompleteMultipartUploadRequest` | Complete multipart upload |
| Abort Multipart Upload | abortMultipartUpload | `AbortMultipartUploadRequest` | Abort multipart upload |
| Generate Presigned URL | generatePresignedUrl | `GeneratePresignedUrlRequest` | Generate temporary access URL |

## Request/Response Examples

### Create Bucket

**Request:**
```json
{
  "bucketName": "my-test-bucket",
  "regionId": "cn-north-1"
}
```

**Response:**
```json
{
  "requestId": "req-xxx",
  "result": {
    "bucketName": "my-test-bucket",
    "location": "https://my-test-bucket.oss.cn-north-1.jdcloud.com"
  }
}
```

### List Buckets

**Response:**
```json
{
  "requestId": "req-xxx",
  "result": {
    "buckets": [
      {
        "bucketName": "my-test-bucket",
        "regionId": "cn-north-1",
        "storageClass": "Standard",
        "creationDate": "2026-06-01T10:00:00+08:00"
      }
    ],
    "totalCount": 1
  }
}
```

### Head Bucket

**Response:**
```json
{
  "requestId": "req-xxx",
  "result": {
    "bucketName": "my-test-bucket",
    "regionId": "cn-north-1",
    "bucketAcl": "private",
    "storageClass": "Standard",
    "objectCount": 150,
    "totalSizeBytes": 10737418240,
    "creationDate": "2026-06-01T10:00:00+08:00",
    "versioning": "none"
  }
}
```

### Put Bucket ACL

**Request:**
```json
{
  "bucketName": "my-test-bucket",
  "bucketAcl": "private"
}
```

### Put Bucket Lifecycle

**Request:**
```json
{
  "bucketName": "my-test-bucket",
  "rules": [
    {
      "id": "archive-old-logs",
      "status": "Enabled",
      "filter": { "prefix": "logs/" },
      "transitions": [
        { "days": 30, "storageClass": "InfrequentAccess" },
        { "days": 180, "storageClass": "Archive" }
      ],
      "expiration": { "days": 365 }
    }
  ]
}
```

### Put Object

**Request (HTTP):**
```
PUT /my-test-bucket/path/to/object.txt HTTP/1.1
Host: oss.jdcloud-api.com
Content-Length: 1024
Content-Type: text/plain
x-oss-storage-class: Standard
```

**Response:**
```json
{
  "requestId": "req-xxx",
  "result": {
    "objectETag": "d41d8cd98f00b204e9800998ecf8427e",
    "objectKey": "path/to/object.txt"
  }
}
```

### List Objects

**Response:**
```json
{
  "requestId": "req-xxx",
  "result": {
    "name": "my-test-bucket",
    "prefix": "",
    "maxKeys": 100,
    "keyCount": 2,
    "objects": [
      {
        "key": "path/to/object.txt",
        "size": 1024,
        "eTag": "d41d8cd98f00b204e9800998ecf8427e",
        "storageClass": "Standard",
        "lastModified": "2026-06-01T10:00:00+08:00"
      }
    ]
  }
}
```

### Generate Presigned URL

**Response:**
```json
{
  "requestId": "req-xxx",
  "result": {
    "presignedUrl": "https://my-test-bucket.oss.cn-north-1.jdcloud.com/path/to/object.txt?X-Amz-Algorithm=..."
  }
}
```

## Required Fields

### Create Bucket

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| bucketName | string | Yes | Globally unique bucket name (3-63 chars) |
| regionId | string | Yes | Region ID |

### Put Bucket ACL

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| bucketName | string | Yes | Existing bucket name |
| bucketAcl | string | Yes | private, public-read, public-read-write |

### Put Bucket Lifecycle

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| bucketName | string | Yes | Existing bucket name |
| rules | array | Yes | Array of lifecycle rule objects |
| rules[].id | string | Yes | Unique rule identifier |
| rules[].status | string | Yes | Enabled or Disabled |

### Put Object

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| bucketName | string | Yes | Existing bucket name |
| objectKey | string | Yes | Object key (path) |
| contentLength | integer | Yes | Object size in bytes |
| body | bytes | Yes | Object data |

## Pagination

List Objects supports pagination:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| prefix | string | "" | Filter objects by prefix |
| delimiter | string | "" | Group objects by delimiter (e.g., "/") |
| maxKeys | integer | 100 | Max keys to return (max: 1000) |
| marker | string | "" | Start after this key |

**Response pagination:**
```json
{
  "result": {
    "objects": [...],
    "keyCount": 100,
    "isTruncated": true,
    "nextMarker": "some-key"
  }
}
```

## Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| AccessDenied | 403 | Access denied |
| BucketAlreadyExists | 409 | Bucket name already exists |
| BucketNotEmpty | 409 | Bucket is not empty |
| NoSuchBucket | 404 | Bucket does not exist |
| NoSuchKey | 404 | Object does not exist |
| InvalidBucketName | 400 | Invalid bucket name format |
| InvalidArgument | 400 | Invalid argument |
| EntityTooLarge | 400 | Object exceeds size limit |
| InternalError | 500 | Internal server error |
| ServiceUnavailable | 503 | Service temporarily unavailable |
| SlowDown | 503 | Reduce request rate |

## SDK Import Pattern

```python
# Client
from jdcloud_sdk.services.oss.client.OssClient import OssClient

# Bucket APIs
from jdcloud_sdk.services.oss.apis.CreateBucketRequest import CreateBucketRequest, CreateBucketParameters
from jdcloud_sdk.services.oss.apis.ListBucketsRequest import ListBucketsRequest, ListBucketsParameters
from jdcloud_sdk.services.oss.apis.HeadBucketRequest import HeadBucketRequest, HeadBucketParameters
from jdcloud_sdk.services.oss.apis.DeleteBucketRequest import DeleteBucketRequest, DeleteBucketParameters

# ACL APIs
from jdcloud_sdk.services.oss.apis.PutBucketAclRequest import PutBucketAclRequest, PutBucketAclParameters
from jdcloud_sdk.services.oss.apis.GetBucketAclRequest import GetBucketAclRequest, GetBucketAclParameters

# Lifecycle APIs
from jdcloud_sdk.services.oss.apis.PutBucketLifecycleRequest import PutBucketLifecycleRequest, PutBucketLifecycleParameters
from jdcloud_sdk.services.oss.apis.GetBucketLifecycleRequest import GetBucketLifecycleRequest, GetBucketLifecycleParameters

# Versioning APIs
from jdcloud_sdk.services.oss.apis.PutBucketVersioningRequest import PutBucketVersioningRequest, PutBucketVersioningParameters
from jdcloud_sdk.services.oss.apis.GetBucketVersioningRequest import GetBucketVersioningRequest, GetBucketVersioningParameters

# Replication APIs
from jdcloud_sdk.services.oss.apis.PutBucketReplicationRequest import PutBucketReplicationRequest, PutBucketReplicationParameters
from jdcloud_sdk.services.oss.apis.GetBucketReplicationRequest import GetBucketReplicationRequest, GetBucketReplicationParameters

# Object APIs
from jdcloud_sdk.services.oss.apis.PutObjectRequest import PutObjectRequest, PutObjectParameters
from jdcloud_sdk.services.oss.apis.GetObjectRequest import GetObjectRequest, GetObjectParameters
from jdcloud_sdk.services.oss.apis.HeadObjectRequest import HeadObjectRequest, HeadObjectParameters
from jdcloud_sdk.services.oss.apis.DeleteObjectRequest import DeleteObjectRequest, DeleteObjectParameters
from jdcloud_sdk.services.oss.apis.ListObjectsRequest import ListObjectsRequest, ListObjectsParameters
from jdcloud_sdk.services.oss.apis.CopyObjectRequest import CopyObjectRequest, CopyObjectParameters

# Multipart APIs
from jdcloud_sdk.services.oss.apis.InitiateMultipartUploadRequest import InitiateMultipartUploadRequest, InitiateMultipartUploadParameters
from jdcloud_sdk.services.oss.apis.CompleteMultipartUploadRequest import CompleteMultipartUploadRequest, CompleteMultipartUploadParameters
from jdcloud_sdk.services.oss.apis.AbortMultipartUploadRequest import AbortMultipartUploadRequest, AbortMultipartUploadParameters

# Presigned URL
from jdcloud_sdk.services.oss.apis.GeneratePresignedUrlRequest import GeneratePresignedUrlRequest, GeneratePresignedUrlParameters
```