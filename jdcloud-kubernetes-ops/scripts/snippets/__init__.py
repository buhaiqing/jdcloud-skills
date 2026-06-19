"""JD Cloud K8s Ops — composable SDK snippets for LLM agents.

Modules:
    cluster_ops      — Cluster CRUD (jdcloud_sdk)
    node_group_ops   — Node Group CRUD + scaling (jdcloud_sdk)
    credential_ops   — Kubeconfig retrieval (jdcloud_sdk)
    storage_ops      — PV/PVC/StorageClass management (kubernetes client)
    workload_ops     — Pod/Service/Deployment/HPA/Ingress operations (kubernetes client)
    cloudshell_ops   — CloudShell remote kubectl execution with fallback
    diagnostics_ops  — Cross-resource anomaly aggregation and performance analysis
    k8s_client       — Unified K8s client initialization and error handling
    wait_utils       — Polling helpers for state transitions
"""
