<!---
SKILL.md entry: [02_go_guide.md](file:///Users/bohaiqing/opensource/git/ai_study/.trae/skills/code-reviewer/references/02_go_guide.md)
Category: 2. Go Code Review Guide
When to use: When reviewing Go code
--->

# Go Code Review Guide (Lean 2026)

> Target: Go >= 1.21  
> Goal: 以最少检查项保障生产安全与稳定

## 1) P0/P1 阻断门禁

- [ ] 忽略错误返回（`_ = err` / 未检查 `err`）
- [ ] SQL 拼接导致注入风险
- [ ] goroutine 泄漏（无退出条件、无 `context` 取消）
- [ ] 外部调用缺少超时控制（HTTP/DB/RPC）
- [ ] 凭证硬编码或日志泄露敏感信息

## 2) 最小高价值清单

### Correctness
- [ ] 错误包装含上下文（`fmt.Errorf("...: %w", err)`）
- [ ] `context.Context` 作为首参并向下游传递
- [ ] API 返回值与错误语义一致（不混乱）

### Maintainability
- [ ] 命名简洁一致，包职责清晰
- [ ] 接口最小化，避免过抽象
- [ ] 公共函数有文档注释

### Modern Go
- [ ] 合理使用标准库 `slices` / `maps` / `cmp` / `slog`
- [ ] 泛型用于减少重复且不牺牲可读性

## 3) 并发与性能（只保留关键）

- [ ] goroutine 生命周期可控（`WaitGroup` + `context`）
- [ ] channel 关闭与消费策略明确
- [ ] 高分配热点优化：`strings.Builder`、切片预分配
- [ ] 使用 `go test -race` 作为并发回归门禁

## 4) 测试门禁

- [ ] 表驱动测试覆盖关键路径
- [ ] 并发代码有 race 检测
- [ ] 关键函数有 benchmark（性能敏感时）

## 5) 安全门禁

- [ ] SQL 参数化，禁止字符串拼接
- [ ] 公网接口有速率限制和超时策略
- [ ] 使用 `govulncheck`，高危漏洞不放行

## 6) 推荐命令（最小集）

```bash
gofmt -w .
go test ./...
go test -race ./...
golangci-lint run
govulncheck ./...
```

> 评审输出建议：先阻断项，再给最多 5 条可落地优化。
