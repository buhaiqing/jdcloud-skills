<!---
SKILL.md Entry: [01_python_guide.md](file:///Users/bohaiqing/opensource/git/ai_study/.trae/skills/code-reviewer/references/01_python_guide.md)
Category: 1. Python Code Review Guide
When to use: When reviewing Python code
--->

# Python Code Review Guide (Lean 2026)

> Target: Python >= 3.11 (prefer 3.12+)  
> Goal: 用最短评审路径发现最高风险问题

## 1) P0/P1 阻断门禁

- [ ] 硬编码密钥、凭证、token
- [ ] `eval` / `exec` / 不安全反序列化（如不可信 `pickle`）
- [ ] SQL/命令注入风险（字符串拼接查询或shell拼接）
- [ ] 外部调用无超时、无重试、无失败降级
- [ ] 关键异常被吞掉（`except Exception: pass`）

## 2) 最小高价值清单

### Correctness
- [ ] 边界输入处理完整（空、None、极值、非法值）
- [ ] 错误分层清晰，异常链保留（`raise ... from e`）
- [ ] 函数职责单一，避免“巨型函数”

### Maintainability
- [ ] 类型标注完整（公共函数/关键模块）
- [ ] 复杂逻辑有测试，不靠注释解释行为
- [ ] 避免重复实现，抽象层级不过度

### Modern Python
- [ ] 使用 `pathlib` / `tomllib` / `dataclass(slots=True)` 等现代特性
- [ ] 合理使用 `match/case` 与 `|` 联合类型

## 3) 性能与并发（只看高杠杆）

- [ ] 成员判断用 `set`，频繁头部出队用 `deque`
- [ ] 大数据处理避免中间大列表（优先生成器）
- [ ] I/O并发优先 `asyncio`，CPU密集用多进程
- [ ] 并发任务具备取消、超时、回收，避免协程泄漏

## 4) 测试门禁

- [ ] 新增关键逻辑必须有单测
- [ ] 异常路径和边界路径有覆盖
- [ ] 异步代码有异步测试

## 5) 安全门禁

- [ ] 输入白名单验证，不信任外部输入
- [ ] 日志不落敏感数据（PII/token）
- [ ] 文件路径处理防止路径穿越

## 6) 推荐命令（最小集）

```bash
ruff check .
ruff format --check .
mypy .
bandit -r .
pytest -q
```

> 评审输出建议：先给 P0/P1 阻断项，再给最多 5 条高杠杆优化。
