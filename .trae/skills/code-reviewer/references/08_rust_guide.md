<!---
SKILL.md entry: [08_rust_guide.md](file:///Users/bohaiqing/opensource/git/ai_study/.trae/skills/code-reviewer/references/08_rust_guide.md)
Category: 8. Rust Code Review Guide
When to use: When reviewing Rust code
--->

# Rust Code Review Guide (Lean 2026)

> Target: Rust >= 1.75 (Edition 2021)  
> Goal: 用类型系统优势快速筛出生产风险

## 1) P0/P1 阻断门禁

- [ ] 生产路径存在 `unwrap` / `expect`（可控 panic 例外需说明）
- [ ] 未说明安全前提的 `unsafe` 代码
- [ ] 外部 I/O 无超时与错误恢复
- [ ] 注入/路径穿越/敏感数据泄漏风险
- [ ] 关键并发路径可能死锁或任务泄漏

## 2) 最小高价值清单

### Correctness
- [ ] 错误通过 `Result` 传递并保留上下文
- [ ] 关键不变量编码进类型（newtype / enum）
- [ ] 所有边界输入验证明确

### Maintainability
- [ ] 所有权模型清晰，避免无意义 clone
- [ ] 公共 API 文档完整
- [ ] 模块边界明确，避免巨大模块

### Rust Idioms
- [ ] 使用迭代器与模式匹配提高可读性
- [ ] 仅在必要时使用 `Arc<Mutex<_>>` / interior mutability

## 3) 并发与性能（高杠杆）

- [ ] `tokio` 任务生命周期可控（取消、回收、超时）
- [ ] 共享状态策略合理（原子、锁粒度、消息传递）
- [ ] 热点路径避免多余分配与拷贝
- [ ] 有 benchmark 或 profile 证据支持优化

## 4) 测试门禁

- [ ] 关键逻辑单测覆盖
- [ ] 错误路径与边界路径覆盖
- [ ] 异步路径有 async 测试

## 5) 安全门禁

- [ ] `unsafe` 块附带 `SAFETY` 说明
- [ ] 依赖漏洞扫描纳入 CI
- [ ] 敏感信息不写入日志

## 6) 推荐命令（最小集）

```bash
cargo fmt --check
cargo clippy -- -D warnings
cargo test
cargo audit
```

> 评审输出建议：先阻断项，再给最多 5 条高价值优化建议。
