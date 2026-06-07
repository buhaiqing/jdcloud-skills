# CLI — JD Cloud JCS for Kubernetes (`jdc`)

## Install and Config

- Install: see [JD Cloud CLI](https://github.com/jdcloud-api/jdcloud-cli)
- **CRITICAL:** The `jdc` CLI reads credentials exclusively from `~/.jdc/config` INI file, NOT from environment variables.
- Kubernetes operations are exposed under the `nc` (Native Container) subcommand.
- For sandbox environments, redirect `HOME` and pre-create config files (see SKILL.md "Critical jdc CLI Behavioral Notes").

## Conventions (Agent Execution)

- `--output json` is a **top-level argument** — MUST be placed BEFORE the subcommand: `jdc --output json nc <command> ...`
- `--no-interactive` does NOT exist in `jdc` CLI — all commands are non-interactive by default; omit this flag.
- Document **exact** JSON paths after verifying with a real invocation (CLI output may differ from raw API).

## CLI vs API Coverage Gap

| Operation (API / SDK) | Available via `jdc`? | Notes |
|------------------------|---------------------|-------|
| Create Cluster | Yes | `nc create-cluster` |
| Describe Cluster | Yes | `nc describe-cluster` |
| Describe Clusters | Yes | `nc describe-clusters` |
| Modify Cluster (Upgrade) | Yes | `nc modify-cluster` |
| Delete Cluster | Yes | `nc delete-cluster` |
| Create Node Group | Yes | `nc create-node-group` |
| Describe Node Group | Yes | `nc describe-node-group` |
| Describe Node Groups | Yes | `nc describe-node-groups` |
| Modify Node Group (Scale) | Yes | `nc modify-node-group` |
| Delete Node Group | Yes | `nc delete-node-group` |
| Describe Cluster Credential | Yes | `nc describe-cluster-credential` |

## Command Map

### Cluster Operations

| Goal | Example `jdc` Invocation | Notes |
|------|--------------------------|-------|
| Create Cluster | `jdc --output json nc create-cluster --region-id <region> --cluster-name <name> --vpc-id <vpc> --subnet-id <subnet> --master-version <ver> --node-group-name <ng-name> --instance-type <type> --node-count <n>` | `--output json` BEFORE subcommand |
| Describe Cluster | `jdc --output json nc describe-cluster --region-id <region> --cluster-id <id>` | Returns cluster details |
| List Clusters | `jdc --output json nc describe-clusters --region-id <region> --page-number 1 --page-size 100` | Supports pagination |
| Modify Cluster | `jdc --output json nc modify-cluster --region-id <region> --cluster-id <id> --master-version <new-ver>` | Upgrade cluster version |
| Delete Cluster | `jdc --output json nc delete-cluster --region-id <region> --cluster-id <id>` | Irreversible operation |

### Node Group Operations

| Goal | Example `jdc` Invocation | Notes |
|------|--------------------------|-------|
| Create Node Group | `jdc --output json nc create-node-group --region-id <region> --cluster-id <id> --name <name> --instance-type <type> --node-count <n> --subnet-id <subnet>` | Add worker nodes |
| Describe Node Group | `jdc --output json nc describe-node-group --region-id <region> --cluster-id <id> --node-group-id <ng-id>` | Get node group details |
| List Node Groups | `jdc --output json nc describe-node-groups --region-id <region> --cluster-id <id>` | List all node groups for a cluster |
| Scale Node Group | `jdc --output json nc modify-node-group --region-id <region> --cluster-id <id> --node-group-id <ng-id> --node-count <n>` | Adjust node count |
| Delete Node Group | `jdc --output json nc delete-node-group --region-id <region> --cluster-id <id> --node-group-id <ng-id>` | Remove node group |

### Credential Operations

| Goal | Example `jdc` Invocation | Notes |
|------|--------------------------|-------|
| Get Kubeconfig | `jdc --output json nc describe-cluster-credential --region-id <region> --cluster-id <id>` | Returns base64-encoded kubeconfig |

## JSON Response Paths

### Create Cluster
```json
{
  "requestId": "req-xxx",
  "result": {
    "clusterId": "c-xxx"
  }
}
```
**Key path:** `$.result.clusterId`

### Describe Cluster
```json
{
  "requestId": "req-xxx",
  "result": {
    "cluster": {
      "clusterId": "c-xxx",
      "clusterName": "my-cluster",
      "state": "running",
      "masterVersion": "1.28.3",
      "endpoint": "https://c-xxx.cn-north-1.nc.jdcloud.com:6443",
      "vpcId": "vpc-xxx",
      "subnetId": "subnet-xxx",
      "nodeGroups": [
        {"nodeGroupId": "ng-xxx", "name": "worker-pool"}
      ],
      "createdTime": "2026-06-08T10:00:00+08:00"
    }
  }
}
```
**Key paths:**
- `$.result.cluster.clusterId` — Cluster ID
- `$.result.cluster.state` — running/creating/deleting/error
- `$.result.cluster.endpoint` — API server endpoint

### Describe Clusters (List)
```json
{
  "requestId": "req-xxx",
  "result": {
    "clusters": [
      {
        "clusterId": "c-xxx",
        "clusterName": "my-cluster",
        "state": "running"
      }
    ],
    "totalCount": 1
  }
}
```
**Key paths:**
- `$.result.clusters[*].clusterId` — Array of cluster IDs
- `$.result.totalCount` — Total number of clusters

### Create Node Group
```json
{
  "requestId": "req-xxx",
  "result": {
    "nodeGroupId": "ng-xxx"
  }
}
```
**Key path:** `$.result.nodeGroupId`

### Describe Node Group
```json
{
  "requestId": "req-xxx",
  "result": {
    "nodeGroup": {
      "nodeGroupId": "ng-xxx",
      "name": "worker-pool",
      "state": "running",
      "instanceType": "g.n2.large",
      "nodeCount": 3,
      "minCount": 1,
      "maxCount": 10,
      "subnetId": "subnet-xxx",
      "createdTime": "2026-06-08T10:05:00+08:00"
    }
  }
}
```
**Key paths:**
- `$.result.nodeGroup.nodeGroupId` — Node group ID
- `$.result.nodeGroup.state` — running/creating/deleting/error
- `$.result.nodeGroup.nodeCount` — Current number of nodes

### Describe Cluster Credential
```json
{
  "requestId": "req-xxx",
  "result": {
    "kubeconfig": "YXBpVmVyc2lvbjogdjEKa2luZDogQ29uZmln..."
  }
}
```
**Key path:** `$.result.kubeconfig` (base64-encoded)

## Common CLI Patterns

### Sandbox Setup (Before Running Commands)

```bash
export HOME=/tmp/jdc-home
mkdir -p /tmp/jdc-home/.jdc
cat > /tmp/jdc-home/.jdc/config << 'CONFIGEOF'
[default]
access_key = YOUR_ACCESS_KEY
secret_key = YOUR_SECRET_KEY
region_id = cn-north-1
endpoint = nc.jdcloud-api.com
scheme = https
timeout = 20
CONFIGEOF
printf "%s" "default" > /tmp/jdc-home/.jdc/current
```

### Polling for Cluster Status

```bash
# Poll until cluster is running
for i in $(seq 1 20); do
  STATE=$(jdc --output json nc describe-cluster \
    --region-id "cn-north-1" \
    --cluster-id "c-xxx" | jq -r '.result.cluster.state')
  [ "$STATE" = "running" ] && break
  sleep 30
done
```

### Extracting Values with jq

```bash
# Get cluster ID from create response
CLUSTER_ID=$(jdc --output json nc create-cluster ... | jq -r '.result.clusterId')

# Get all cluster IDs from list
CLUSTER_IDS=$(jdc --output json nc describe-clusters --region-id cn-north-1 | jq -r '.result.clusters[].clusterId')