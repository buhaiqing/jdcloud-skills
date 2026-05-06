
&lt;!---
SKILL.md entry: [05_general_framework.md](file:///Users/bohaiqing/opensource/git/ai_study/.trae/skills/code-reviewer/references/05_general_framework.md)
Category: 5. General Review Framework
When to use: When conducting any code review
---&gt;

# General Code Review Framework (Lean)

## 1) 快速流程（默认）

1. 定界：确认业务目标、变更范围、关键路径
2. 阻断项：先查 P0/P1（安全/正确性/可靠性）
3. 高杠杆项：性能与可维护性改进
4. 双轮复盘：查漏 + 去除过度建议
5. 输出：按严重级别给结论与行动

> 时间盒：小PR 30分钟内，大PR建议拆分后再评审。

## 2) 严重级别（统一定义）

- **P0**：必须立刻阻断（漏洞、越权、数据破坏、不可恢复故障）
- **P1**：合并前必须修复（关键逻辑错误、严重稳定性风险）
- **P2**：本迭代修复（中等质量/性能/测试缺口）
- **P3**：可排期优化（风格与低影响问题）

## 3) 最小检查清单（20项内）

### Correctness
- [ ] 关键路径逻辑正确
- [ ] 边界输入可处理（空值/极值/异常）
- [ ] 错误处理可预期且不吞错

### Security
- [ ] 无硬编码密钥
- [ ] 输入已校验，危险拼接被禁止
- [ ] 鉴权/授权完整，无越权路径
- [ ] 依赖无已知高危漏洞

### Reliability
- [ ] 超时、重试、幂等策略合理
- [ ] 关键依赖故障有降级方案
- [ ] 关键操作可追踪（日志/trace）

### Maintainability
- [ ] 复杂逻辑可读，职责清晰
- [ ] 无明显重复代码
- [ ] 新增关键逻辑有测试

## 4) 输出规则

- 先给“阻断项”，再给“高价值优化”
- 每条问题包含：位置、风险、修复建议、影响范围
- 对不确定问题明确标注假设，避免误导
