# Troubleshooting JCQ

## Common API Error Codes

| Code / HTTP | Meaning | Agent Action |
|-------------|---------|--------------|
| `InvalidParameter` / 400 | Request failed validation | Align body with OpenAPI; check field types and lengths |
| `ResourceNotFound` / 404 | Topic or consumer group does not exist | Verify resource name and region; create if needed |
| `ResourceAlreadyExists` / 409 | Topic or consumer group already exists | Suggest reuse or alternative name |
| `AccessDenied` / 403 | Insufficient IAM permissions | Check IAM policy; verify credentials |
| `MessageTooLarge` / 400 | Message body exceeds 256 KB | Split message or store payload in OSS |
| `QuotaExceeded` / 429 | Account quota exceeded | HALT; user raises quota or deletes unused resources |
| `Throttling` / 429 | Rate limit exceeded | Back off exponentially; respect `Retry-After` header |
| `InternalError` / 5xx | JD Cloud internal error | Retry up to 3 times; then HALT with requestId |
| `InsufficientBalance` / 403 | Account balance insufficient | HALT; user tops up |

## Diagnostic Order

1. **Verify credentials** — Ensure `JDC_ACCESS_KEY` and `JDC_SECRET_KEY` are set and valid.
2. **Check region** — Confirm `regionId` matches the region where the resource was created.
3. **Describe resource by ID/name** — Use `describeTopics` or `describeConsumerGroups` to verify existence and status.
4. **Check IAM policy** — Verify the credential has `jcq:*` or appropriate scoped permissions.
5. **Check message size** — For send failures, verify message body is ≤ 256 KB.
6. **Check consumer group binding** — Consumer groups are bound to topics; verify the topic exists before creating a consumer group.

## Topic-Specific Issues

### Topic creation fails with `ResourceAlreadyExists`

- Topic names must be unique within the region.
- Use `describeTopics` to list existing topics and suggest a unique alternative.

### Topic appears in `CREATING` state for too long

- Normal creation time: < 30 seconds.
- If stuck > 60 seconds, retry `describeTopics`.
- If still stuck, open a JD Cloud support ticket with the topic name and region.

### Delete topic fails with dependent consumer groups

- JCQ may refuse to delete a topic that has active consumer groups.
- First delete all consumer groups bound to the topic, then retry topic deletion.

## ConsumerGroup-Specific Issues

### Consumer group creation fails with `ResourceNotFound`

- The target topic must exist before creating a consumer group.
- Verify topic via `describeTopics`, or create the topic first.

### Consumer group not receiving messages

1. Verify the consumer group is `ACTIVE` via `describeConsumerGroups`.
2. Verify the topic has messages via `describeMessages`.
3. Check if a `tag` filter is applied that excludes all messages.
4. Verify no other consumers in the same group are consuming all messages.

### Message receive returns empty array

- This is normal if the topic has no messages.
- Verify via `describeMessages` that messages exist in the topic.
- Check `tag` filter — it may be filtering out all available messages.
- Check message retention — messages may have expired.

## Message-Specific Issues

### Send message fails with `MessageTooLarge`

- Maximum message body size is 256 KB.
- For larger payloads, store data in OSS and send the object key in the message body.

### Duplicate message delivery

- JCQ guarantees at-least-once delivery.
- Consumers MUST be idempotent — handle duplicate `messageId` gracefully.
- Use `messageId` for deduplication if exactly-once semantics are required.

### High `receiveCount` on messages

- Indicates consumers are failing to process messages successfully.
- Check consumer application logs for processing errors.
- Verify consumer logic handles message format correctly.
- Consider implementing dead-letter handling after max retries.

## SDK-Specific Issues

### `ImportError: cannot import name 'JcqClient'`

- Verify `jdcloud_sdk` is installed: `pip show jdcloud_sdk`
- Verify version: `jdcloud_sdk>=1.6.26`
- Check Python version: MUST be 3.10 (NOT 3.12).

### SDK call hangs or times out

- Check network connectivity to `jcq.jdcloud-api.com`.
- Verify firewall rules allow HTTPS outbound on port 443.
- Increase timeout in SDK client configuration.

### Authentication failures

- Verify `JDC_ACCESS_KEY` and `JDC_SECRET_KEY` are correct.
- Check for extra whitespace or newline characters in environment variables.
- Verify the access key has not been disabled or deleted in IAM console.
