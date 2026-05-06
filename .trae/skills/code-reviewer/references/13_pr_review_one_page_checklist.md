<!---
SKILL.md entry: [13_pr_review_one_page_checklist.md](file:///Users/bohaiqing/opensource/git/ai_study/.trae/skills/code-reviewer/references/13_pr_review_one_page_checklist.md)
Category: 13. PR One-page Execution Checklist
When to use: Copy-paste checklist for pull request review execution
--->

# PR Review One-page Checklist

> 使用方法：复制到 PR 评论区，按项勾选。  
> 规则：先阻断项，后优化项。

## A. Blocking (P0/P1)

- [ ] 无硬编码密钥/凭证/token
- [ ] 无注入风险（SQL/Command/Template/Prompt）
- [ ] 鉴权/授权完整，无越权路径
- [ ] 外部调用有超时与失败处理
- [ ] 无敏感数据泄露（日志/响应/前端资源）

## B. Correctness

- [ ] 关键业务逻辑正确
- [ ] 边界与异常路径可处理
- [ ] 错误语义明确且可追踪

## C. Reliability & Performance

- [ ] 并发模型合理（无泄漏/死锁风险）
- [ ] 热点路径无明显低效实现
- [ ] 关键链路有降级或回退策略

## D. Maintainability

- [ ] 职责边界清晰，避免过度复杂
- [ ] 重复代码可接受或已抽象
- [ ] 关键模块可读、可测

## E. Tests

- [ ] 新增关键逻辑有测试
- [ ] 失败路径有测试
- [ ] 相关测试在 CI 通过

## F. Final Decision

- [ ] Approve
- [ ] Request Changes
- [ ] Block (说明阻断项)

## Optional Output Template

```md
## Decision
- Result: [Approve | Request Changes | Block]
- Reason: [one sentence]

## Blocking Findings (P0/P1)
1. [title] - [risk] - [fix]

## Important Improvements (P2)
1. [title] - [benefit] - [fix]
```
