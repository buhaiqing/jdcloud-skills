<!---
SKILL.md entry: [14_nondeterministic_eval_guide.md](file:///Users/bohaiqing/opensource/git/ai_study/.trae/skills/code-reviewer/references/14_nondeterministic_eval_guide.md)
Category: 14. Nondeterministic System Evaluation Methodology
When to use: When evaluating Agent/Skill systems that rely on LLM or other nondeterministic components
--->

# 非确定性系统评估方法论

## 0. 核心问题

LLM 驱动的 Agent/Skill 本质是非确定性系统：相同输入可能产生不同输出。传统确定性系统的评审方法（单次测试通过即判定正确）在此失效。本指南提供统计严谨的评估框架，确保评审结论可靠。

## 1. 基本原则

1. **统计声明必须有统计证据**：声称"99%成功率"必须同时报告样本量、置信区间与检验方法
2. **频率×严重度=风险**：评分体系必须综合失败频率与失败影响，而非仅看频率
3. **方差是信号而非噪声**：高方差本身即为质量缺陷指标
4. **基线对比而非绝对判定**：非确定性系统应与历史基线或对照版本对比，而非单点判定

## 2. 最小样本量要求

### 2.1 二项指标（成功率/失败率）

基于 Wilson 区间的最小样本量（95% 置信度，±3% 误差范围）：

| 目标成功率 | 最小样本量 | 说明 |
|-----------|-----------|------|
| ≥ 99% | 299 | 需至少观察到 0 次失败才能以 95% 置信度确认 |
| ≥ 95% | 73 | |
| ≥ 90% | 45 | |
| ≥ 80% | 28 | |

**规则**：声称达到某成功率阈值时，必须提供 ≥ 上表对应样本量的测试结果。

### 2.2 连续指标（时延/成本/质量分数）

- 最少 30 个独立样本（中心极限定理近似正态的最低要求）
- 必须报告：均值、标准差、P50、P95、最大值
- 对比两个版本时，必须使用效应量（Cohen's d）而非仅看 p 值

### 2.3 样本独立性要求

- 同一对话的不同轮次**不算**独立样本（存在上下文依赖）
- 相同 prompt 的多次调用算独立样本（前提：temperature > 0）
- 不同用户/不同场景的调用算独立样本

## 3. 风险调整评分体系

### 3.1 替代原有 A/B/C/D 纯频率评分

原评分仅看"成功率"，忽略了失败后果的差异。引入风险调整评分：

```
Risk-Adjusted Score = 100 - (Failure_Rate × Severity_Weight)
```

### 3.2 严重度权重

| 失败类型 | 严重度权重 | 示例 |
|---------|-----------|------|
| 灾难性（数据泄漏/安全绕过） | 100 | Prompt注入成功、跨租户数据泄漏 |
| 严重（功能不可用/错误决策） | 50 | 工具调用失败导致业务中断、RAG幻觉导致错误回答 |
| 中等（降级但可用） | 20 | 响应质量下降但仍有价值、降级到备选模型 |
| 轻微（体验问题） | 5 | 格式不规范、响应稍慢 |

### 3.3 评分映射

| 风险调整分数 | 等级 | 决策 |
|-------------|------|------|
| 90-100 | A | 可发布 |
| 80-89 | B | 修复 P2 后发布 |
| 70-79 | C | 修复 P1 后复审 |
| <70 | D | 禁止发布，需重构 |

### 3.4 示例

- Skill A：成功率 99.5%，0.5% 失败为灾难性 → Score = 100 - (0.5% × 100) = 50 → **D 级**
- Skill B：成功率 95%，5% 失败为轻微 → Score = 100 - (5% × 5) = 97.5 → **A 级**

> 结论：Skill A 虽然成功率更高，但因失败后果严重，实际风险远大于 Skill B。

## 4. 非确定性测试方法

### 4.1 多次运行取统计量

```python
results = [run_skill(test_input) for _ in range(N)]
success_rate = sum(1 for r in results if r.is_correct) / N
ci_lower, ci_upper = wilson_ci(success_rate, N, confidence=0.95)
```

### 4.2 对比测试（A/B 评估）

| 步骤 | 操作 |
|------|------|
| 1 | 准备相同的测试集 |
| 2 | 对版本 A 和版本 B 各运行 N 次 |
| 3 | 计算两者的成功率均值与方差 |
| 4 | 使用 Welch's t-test 判断差异是否显著 |
| 5 | 报告 Cohen's d 评估效应量 |
| 6 | 仅当 p < 0.05 且 d > 0.2 时声明"有改进" |

### 4.3 回归测试

- 每次变更前后的对比必须使用**相同测试集 + 相同随机种子（如适用）**
- 回归判定标准：新版本在所有关键指标上不低于旧版本（考虑统计波动）
- 非确定性回归允许 ±2% 的波动范围（需根据指标方差调整）

## 5. 评审检查清单

### 统计严谨性
- [ ] 声明的成功率/质量分数附有样本量与置信区间
- [ ] 样本量满足第 2 节最低要求
- [ ] 样本独立性符合第 2.3 节要求
- [ ] 对比测试使用了正确的统计检验方法

### 风险调整
- [ ] 评分使用了风险调整公式而非纯频率
- [ ] 失败类型已分类并赋予正确严重度权重
- [ ] 灾难性失败（权重100）的发生率为 0%（否则直接 D 级）

### 回归判定
- [ ] 回归测试使用了相同测试集
- [ ] 非确定性波动已纳入判定标准
- [ ] 效应量（Cohen's d）已计算并报告

## 6. 报告模板（非确定性评估专用）

```md
## Nondeterministic Evaluation Report

### Test Configuration
- Sample size: N = [n]
- Confidence level: [95%]
- Test set: [name/version]
- Temperature: [value]
- Runs per sample: [k]

### Key Metrics
| Metric | Mean | Std | P50 | P95 | Max | 95% CI |
|--------|------|-----|-----|-----|-----|--------|
| Success Rate | | | | | | |
| Latency (s) | | | | | | |
| Token Cost | | | | | | |

### Risk-Adjusted Score
- Score: [value] → Grade: [A/B/C/D]
- Failure breakdown: [catastrophic: n1, severe: n2, moderate: n3, minor: n4]

### Regression Comparison (if applicable)
- vs baseline [version]: p=[value], Cohen's d=[value]
- Conclusion: [improved / equivalent / degraded]
```

## 7. 与其他文档的关系

- 本指南的评分体系替代 `11_agent_skill_review_system.md` 第四节的纯频率评分
- 本指南的统计方法为 `10_ai_agent_rag_guide.md` 第六节量化阈值提供证据标准
- 对抗性测试的统计判定参见 `15_adversarial_review_guide.md`
