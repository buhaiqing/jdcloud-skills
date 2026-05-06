<!---
SKILL.md entry: [09_infra_guide.md](file:///Users/bohaiqing/opensource/git/ai_study/.trae/skills/code-reviewer/references/09_infra_guide.md)
Category: 9. Infrastructure Review Guide
When to use: When reviewing Terraform, Docker, Kubernetes, CI/CD configurations
--->

# Infrastructure Review Guide (Lean 2026)

> Scope: Terraform, Docker, Kubernetes, CI/CD  
> Goal: 用最少检查项拦截最致命基础设施风险

## 1) P0/P1 阻断门禁

- [ ] 公网暴露高危端口/资源（无明确业务理由）
- [ ] 明文密钥或凭证出现在 IaC、镜像、流水线
- [ ] Terraform state 未加密或无锁
- [ ] 容器以 root 运行且无最小权限限制
- [ ] K8s 缺失网络隔离（默认全通）或 RBAC 过权
- [ ] CI/CD 未做安全扫描直接发布生产

## 2) 最小高价值清单

### Terraform
- [ ] 输入变量有约束校验
- [ ] provider 版本固定，`plan` 变更可审计
- [ ] 敏感输出标记 `sensitive`

### Docker
- [ ] 多阶段构建 + 最小化基础镜像
- [ ] 非 root 用户运行
- [ ] 镜像不包含 secrets

### Kubernetes
- [ ] 资源 requests/limits 完整
- [ ] liveness/readiness 探针齐全
- [ ] 安全上下文（`runAsNonRoot`, `readOnlyRootFilesystem`）合理

### CI/CD
- [ ] 最小权限原则（token permissions）
- [ ] 依赖、镜像、IaC 扫描纳入门禁
- [ ] 生产发布有审批与回滚路径

## 3) 可靠性与成本（高杠杆）

- [ ] 部署策略可回滚（滚动/蓝绿/金丝雀）
- [ ] 关键链路有 SLO 监控与告警
- [ ] 资源规格与实际负载匹配，避免长期过配

## 4) 测试门禁

- [ ] Terraform 至少执行 `fmt/validate/plan`
- [ ] 容器镜像构建后通过漏洞扫描
- [ ] K8s 清单通过静态策略检查

## 5) 安全门禁

- [ ] 默认拒绝网络策略（default deny）
- [ ] 最小权限 RBAC 与服务账号隔离
- [ ] 敏感配置通过 Secret Manager/Vault 注入

## 6) 推荐命令（最小集）

```bash
terraform fmt -check
terraform validate
terraform plan
trivy image <image>
kube-linter lint <manifests>
```

> 评审输出建议：先阻断项，再给最多 5 条高价值优化建议。
