# Troubleshooting — JD Cloud Object Storage Service (OSS)

## Common API Error Codes

| Code / HTTP | Meaning | Agent Action |
|-------------|---------|--------------|
| InvalidBucketName / 400 | Bucket name does not meet naming rules | Fix name per naming rules (3-63 chars, lowercase) |
| InvalidObjectKey / 400 | Object key format invalid | Fix key format (UTF-8, no control characters) |
| BucketAlreadyExists / 409 | Bucket name already taken globally | Suggest alternative unique name |
| BucketNotEmpty / 409 | Bucket contains objects | Empty bucket before delete, or use force flag |
| NoSuchBucket / 404 | Bucket does not exist | Verify bucket name and region |
| NoSuchKey / 404 | Object does not exist | Verify object key; check for versioning |
| AccessDenied / 403 | No permission to perform operation | Check ACL, IAM policy, and credentials |
| InvalidArgument / 400 | Invalid argument value | Fix parameter per OpenAPI |
| EntityTooLarge / 400 | Object exceeds 5 TB | Use multipart upload for large objects |
| MalformedPolicy / 400 | Lifecycle/cors policy format invalid | Fix policy JSON structure |
| PreconditionFailed / 412 | Precondition header mismatch | Check If-Match, If-None-Match values |
| InternalError / 500 | Internal server error | Retry with backoff; HALT if persists |
| ServiceUnavailable / 503 | Service temporarily unavailable | Retry with exponential backoff |
| SlowDown / 503 | Reduce request rate | Implement exponential backoff and retry |

## Diagnostic Order

### 1. Bucket Issues

**Bucket Creation Fails**
1. Verify bucket name uniqueness (listBuckets or headBucket)
2. Check bucket naming rules (3-63 chars, lowercase, no IP format)
3. Verify region is valid for OSS
4. Check bucket quota (max 100 per account)

**Bucket Not Found**
1. Verify bucket name spelling
2. Check correct region -- buckets are region-scoped
3. List all buckets to see available buckets
4. Check if bucket was recently deleted (not recoverable)

**Bucket Access Denied**
1. Check bucket ACL
2. Verify IAM policy grants access
3. Check credentials (access key, secret key)
4. Verify regional endpoint matches bucket region

### 2. Object Issues

**Object Upload Fails**
1. Verify bucket exists and is accessible
2. Check object size (<= 5 TB)
3. For > 5 GB objects, use multipart upload
4. Verify storage class is valid
5. Check network connectivity

**Object Download Fails**
1. Verify object key path is correct
2. Check if object exists (headObject)
3. If versioning enabled, check if latest version is delete marker
4. Check if object has been moved or archived
5. For Archive class, restore before download

**Object Not Found**
1. Verify object key is exactly correct (case-sensitive)
2. Check if versioning is enabled -- object may have a delete marker
3. List objects with prefix to find exact key
4. Check if lifecycle policy expired the object

### 3. ACL / Permission Issues

**ACL Change Not Taking Effect**
1. Verify ACL value is valid: private, public-read, public-read-write
2. Check ACL was applied to correct bucket
3. Note: object ACL may override bucket ACL for individual objects
4. IAM policies take precedence over ACL

**Presigned URL Expired or Invalid**
1. Check expiration time (max 86400 seconds / 24 hours)
2. Verify HTTP method matches intended operation
3. Ensure the access key used to generate URL is still active
4. Check that object key in URL is correct

### 4. Lifecycle Policy Issues

**Lifecycle Rule Not Executing**
1. Verify rule status is "Enabled"
2. Check filter prefix matches target objects
3. Verify transition days and storage class are valid
4. Note: lifecycle runs once per day (not real-time)
5. Check for overlapping rules

**Objects Not Transitioned**
1. Verify days since creation exceeds transition threshold
2. Check object minimum size (128 KB for IA and Archive)
3. Verify target storage class is valid
4. Check if objects are in versioning-suspended state

### 5. Versioning Issues

**Cannot Access Previous Version**
1. Verify versioning is enabled on the bucket
2. Use GetObject with versionId parameter
3. List versions to find the correct version ID

**Delete Not Removing Object**
1. When versioning is enabled, DELETE creates a delete marker
2. To permanently delete, specify versionId
3. To remove delete marker, DELETE the delete marker version

### 6. CRR Issues

**Replication Not Working**
1. Verify source and destination buckets exist
2. Check IAM role for replication service
3. Verify source and destination regions are valid pair
4. Check replication scope (prefix filter)
5. Verify source bucket has versioning enabled

### 7. Performance Issues

**High Latency**
1. Check client network connectivity
2. Verify region proximity -- use bucket in nearest region
3. Enable CDN for frequently accessed content
4. Use multipart upload for large objects

**Throttling (SlowDown)**
1. Implement exponential backoff with jitter
2. Reduce request rate (requests per second)
3. Distribute load across multiple buckets if possible
4. Request higher throughput limits from JD Cloud support

## SDK-Specific Issues

### Import Errors

**Symptom:** `ModuleNotFoundError: No module named 'jdcloud_sdk'`

**Solution:**
```bash
source .venv/bin/activate
uv pip install jdcloud_sdk
```

### Authentication Errors

**Symptom:** `InvalidAccessKeyId.NotFound` or signature errors

**Solution:**
```bash
# Verify environment variables are set correctly
echo $JDC_ACCESS_KEY  # Should be non-empty
# Do NOT echo JDC_SECRET_KEY

# Verify credentials are valid
python -c "
import os
from jdcloud_sdk.core.credential import Credential
cred = Credential(os.environ['JDC_ACCESS_KEY'], os.environ['JDC_SECRET_KEY'])
print('Credentials initialized')
"
```

### Network Errors

**Symptom:** `ConnectionError` or timeout

**Solution:**
```bash
# Test connectivity to OSS endpoint
curl -v https://oss.jdcloud-api.com/v1

# Increase timeout if needed
export JDC_TIMEOUT=30
```

## Getting Help

If issues persist after following this guide:

1. Collect request ID from API response
2. Gather relevant resource IDs (bucket name, object key)
3. Note timestamp of issue occurrence
4. Contact JD Cloud support with above information