<!---
SKILL.md entry: [04_java_kotlin_guide.md](file:///Users/bohaiqing/opensource/git/ai_study/.trae/skills/code-reviewer/references/04_java_kotlin_guide.md)
Category: 4. Java/Kotlin Code Review Guide
When to use: When reviewing Java/Kotlin code
--->

# Java/Kotlin Code Review Guide (Lean 2026)

> Target: Java >= 21, Kotlin >= 1.9  
> Goal: 最短路径保障稳定性、安全性、可维护性

## 1) P0/P1 阻断门禁

- [ ] SQL 字符串拼接（注入风险）
- [ ] 鉴权/授权缺失或可绕过
- [ ] 阻塞式 I/O 无超时（HTTP/DB/RPC）
- [ ] 异常吞没或错误语义混乱
- [ ] 硬编码密钥/敏感信息日志泄漏

## 2) 最小高价值清单

### Correctness
- [ ] 输入边界校验完整（`@Valid` / 显式校验）
- [ ] 事务边界合理，读写事务语义清晰
- [ ] API 错误码与业务错误一致

### Maintainability
- [ ] Java 用 `record`，Kotlin 用 `data class` 作为数据载体
- [ ] 领域服务职责单一，避免“上帝类”
- [ ] 关键公共 API 有文档注释

### Modern Java/Kotlin
- [ ] Java 使用 `switch pattern` / 虚拟线程（适配场景）
- [ ] Kotlin 使用空安全、协程结构化并发

## 3) 并发与性能（高杠杆）

- [ ] I/O 并发策略明确（虚拟线程或协程）
- [ ] 下游调用有 timeout + retry + 降级
- [ ] 避免 N+1 查询与不必要对象分配
- [ ] 热点路径有基准或压测依据

## 4) 测试门禁

- [ ] 关键业务逻辑单测覆盖
- [ ] 控制器/服务层至少有一条集成验证路径
- [ ] 关键异常路径有测试

## 5) 安全门禁

- [ ] 参数化查询 / ORM 安全用法
- [ ] 敏感字段脱敏日志
- [ ] 依赖漏洞扫描纳入 CI

## 6) 推荐命令（最小集）

```bash
# Java (Maven)
./mvnw test
./mvnw verify

# Kotlin/Gradle
./gradlew test
./gradlew detekt
```

> 评审输出建议：先阻断项，再给最多 5 条高价值优化建议。
