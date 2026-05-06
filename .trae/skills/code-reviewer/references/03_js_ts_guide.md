<!---
SKILL.md entry: [03_js_ts_guide.md](file:///Users/bohaiqing/opensource/git/ai_study/.trae/skills/code-reviewer/references/03_js_ts_guide.md)
Category: 3. JavaScript/TypeScript Code Review Guide
When to use: When reviewing JS/TS code
--->

# JavaScript/TypeScript Code Review Guide (Lean 2026)

> Target: TypeScript >= 5.x, ECMAScript >= 2022  
> Goal: 用最少规则保障类型安全、运行安全与可维护性

## 1) P0/P1 阻断门禁

- [ ] 关闭严格模式或大量 `any` 逃逸
- [ ] `eval` / `new Function` / 不安全动态执行
- [ ] API 边界无运行时校验（仅靠类型断言）
- [ ] XSS 风险（不安全 HTML 注入）
- [ ] 密钥进入前端包或本地存储不当

## 2) 最小高价值清单

### Type Safety
- [ ] `strict` 开启，关键模块无 `any`
- [ ] 复杂状态使用可判别联合（discriminated union）
- [ ] 禁止用 `as` 掩盖真实类型问题

### Runtime Safety
- [ ] 外部输入在边界做 schema 校验（如 Zod）
- [ ] 异步调用具备超时与取消（AbortController）
- [ ] 错误处理路径完整，不吞异常

### Maintainability
- [ ] 模块职责单一，函数长度可控
- [ ] 公共类型定义稳定，避免重复类型碎片
- [ ] 前端组件优先可读性与可测试性

## 3) 性能与可靠性（高杠杆）

- [ ] 并发请求使用 `Promise.all` / 容错场景 `allSettled`
- [ ] 避免不必要重渲染（组件边界、memo化策略）
- [ ] 大对象处理避免深拷贝滥用
- [ ] 网络层统一重试/超时/错误映射策略

## 4) 测试门禁

- [ ] 关键业务逻辑有单测
- [ ] 组件测试以行为为中心，不测实现细节
- [ ] API 客户端与错误分支有测试覆盖

## 5) 安全门禁

- [ ] 不信任浏览器端输入，后端二次校验
- [ ] CORS/CSP 配置合理
- [ ] 依赖漏洞扫描纳入 CI

## 6) 推荐命令（最小集）

```bash
eslint .
tsc --noEmit
npm test
npm audit
```

> 评审输出建议：先列阻断项，再列不超过 5 条高价值优化建议。
