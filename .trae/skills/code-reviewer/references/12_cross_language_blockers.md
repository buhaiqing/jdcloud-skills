<!---
SKILL.md entry: [12_cross_language_blockers.md](file:///Users/bohaiqing/opensource/git/ai_study/.trae/skills/code-reviewer/references/12_cross_language_blockers.md)
Category: 12. Cross-language P0/P1 Blocker Index
When to use: Fast triage before deep code review
--->

# Cross-language P0/P1 Blocker Index (Quick Reference)

## 通用阻断项（所有语言）

- 硬编码密钥/凭证/Token
- 注入漏洞（SQL/Command/Template/Prompt）
- 未鉴权高权限操作或越权访问
- 外部依赖调用无超时与降级
- 敏感数据泄露（日志、响应、前端资源）

## Python

- `eval` / `exec` / 不安全反序列化
- 关键异常吞没（`except Exception: pass`）

## Go

- 忽略 `err`
- goroutine 泄漏（无取消与回收）

## Java/Kotlin

- SQL 字符串拼接
- 事务/异常边界错误导致数据不一致

## JavaScript/TypeScript

- 大量 `any` 逃逸 + 无运行时校验
- 不安全动态执行（`eval` / `new Function`）
- XSS 风险（不安全 HTML 注入）

## Rust

- 生产路径 `unwrap` / `expect`
- 缺失 `SAFETY` 注释的 `unsafe` 块

## AI Agent / RAG / Skill

- Prompt Injection 可绕过系统约束
- Tool 调用无权限模型（allowlist/approval 缺失）
- 检索无租户隔离导致数据串读
- Skill 组合产生权限提升（超出各自权限并集）
- Skill 间上下文传递泄漏敏感信息
- 链式调用无故障隔离导致级联崩溃

## 侧信道泄漏阻断项（AI Agent / Skill 专属）

- 响应时延差异暴露内部状态或数据存在性
- 错误消息泄露内部路径/配置/数据结构
- 响应长度差异暴露数据存在性（存在/不存在资源返回不同长度）
- Token 消耗模式差异暴露处理逻辑分支
- 缓存命中/未命中行为差异暴露历史请求模式

> 建议流程：先扫本页阻断项，再进入语言专项清单。
> 侧信道泄漏检测方法详见 `15_adversarial_review_guide.md` 第四节。
> Skill 组合权限提升检测方法详见 `11_agent_skill_review_system.md` 第五节。
