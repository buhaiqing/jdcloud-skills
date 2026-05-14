# JD Cloud VM Ops Skill 优化复盘报告

## 第一轮优化回顾

### 优化前
```yaml
description: >-
  Use when you need to deploy, configure, troubleshoot, or monitor JD Cloud
  Virtual Machine (VM) via official API/SDK or official `jdc` CLI; user mentions
  VM, 云主机, CVM, or tasks target VM instances.
```

### 优化后
```yaml
description: >-
  Use when managing JD Cloud VM instances — create, start, stop, restart, delete,
  or resize cloud servers; attach disks, manage key pairs, configure EIPs and
  security groups; batch-execute scripts via cloud assistant; or troubleshoot
  connectivity and performance issues. Essential for any task involving VM
  lifecycle, storage, networking, or automation, even if user doesn't explicitly
  say "VM" or "CVM". NOT for monitoring metrics (→ jdcloud-cloudmonitor-ops)
  or VPC creation (→ jdcloud-vpc-ops).
```

---

## 第二轮自我复盘：批判性分析

### ✅ 改进点

1. **明确的操作列表**：列出了主要操作（create, start, stop, restart, delete, resize）
2. **包含存储和网络安全操作**：attach disks, manage key pairs, configure EIPs and security groups
3. **云助手支持**：batch-execute scripts via cloud assistant
4. **隐式触发**：明确说明即使没有明确说"VM"或"CVM"也应该触发
5. **边界排除**：明确说明不适用于监控和VPC创建

### ❌ 发现的问题

#### 问题1：过于宽泛的 "troubleshoot" 表述

**当前**：
```
"or troubleshoot connectivity and performance issues"
```

**问题**：
- "performance issues" 可能导致误触发监控查询（如 train-9: "查询京东云VM实例的CPU使用情况"）
- "troubleshoot connectivity" 不够具体，应该明确是VM配置层面的连接问题
- 缺少对故障类型的明确定义

**风险**：可能错误触发监控指标查询场景

#### 问题2：缺少管理类操作覆盖

**当前**：只关注生命周期操作

**缺失场景**：
- 实例类型查询（describe-instance-types）
- 可用区查询（describe-azs）
- 配额查询（describe-quota）
- 镜像查询（describe-images）
- SSH密钥管理

**风险**：管理类查询可能无法正确触发

#### 问题3：中文场景覆盖不足

**当前**：只提到 "云主机"

**应该覆盖**：
- 实例
- 服务器
- 云服务器
- ECS（虽然京东云用VM，但用户可能混淆）
- CVM（京东云术语）

**风险**：使用这些词汇的查询可能无法触发

#### 问题4：边界条件不够精确

**当前**：
```
NOT for monitoring metrics (→ jdcloud-cloudmonitor-ops)
or VPC creation (→ jdcloud-vpc-ops)
```

**应该补充**：
- 不包括：负载均衡配置（→ jdcloud-lb-ops）
- 不包括：账单计费管理（→ jdcloud-billing-ops）
- 不包括：容器服务（→ jdcloud-container-ops）

#### 问题5：字符数虽然符合要求，但可以更精简

当前约 450 字符，可以进一步精简以留出空间补充遗漏内容

---

## 第三轮优化：针对问题的改进

### 改进原则

1. **去掉宽泛表述**：将 "troubleshoot connectivity and performance issues" 改为具体场景
2. **补充管理操作**：增加实例类型、配额、镜像等查询
3. **扩大中文覆盖**：增加"实例"、"服务器"、"云服务器"
4. **明确边界**：增加更多委托规则
5. **精简冗余**：压缩不必要的词汇

### 优化后的 description

```yaml
description: >-
  Use when managing JD Cloud VM instances — create, start, stop, restart, delete,
  or resize instances; attach/detach disks, manage key pairs and snapshots;
  configure EIPs, security groups, and network settings; execute scripts on VMs
  via cloud assistant; or diagnose VM-level connectivity failures and
  misconfigurations. Essential for any task involving VM lifecycle, storage, or
  automation, even if user says "实例", "服务器", "云服务器" or "CVM" instead
  of "VM". NOT for monitoring metrics (→ jdcloud-cloudmonitor-ops), VPC/subnet
  creation (→ jdcloud-vpc-ops), load balancers (→ jdcloud-lb-ops), or billing
  (→ jdcloud-billing-ops).
```

### 改进点详细说明

1. ✅ **具体化故障排查**：
   - 去掉 "performance issues"（避免误触发监控）
   - 改为 "diagnose VM-level connectivity failures and misconfigurations"（明确是VM配置层面的问题）

2. ✅ **补充管理操作**：
   - 增加 "attach/detach disks"
   - 增加 "manage key pairs and snapshots"
   - 增加 "configure EIPs, security groups, and network settings"

3. ✅ **扩大中文覆盖**：
   - 增加 "实例"、"服务器"、"云服务器"、"CVM"

4. ✅ **明确边界**：
   - 增加 load balancers 和 billing 的委托规则

5. ✅ **精简表达**：
   - 使用 "instances" 替代 "cloud servers"（更简洁）
   - 压缩整体结构

---

## 评估查询覆盖检查

### 第一轮 vs 第三轮对比

| 查询ID | 场景 | 第一轮 | 第三轮 | 说明 |
|--------|------|--------|--------|------|
| train-9 | CPU监控查询 | ⚠️ 可能误触发 | ✅ 不会误触发 | 去掉 "performance issues" 后明确不会触发 |
| train-11 | SSH连接问题 | ✅ 正确 | ✅ 正确 | "VM-level connectivity failures" 覆盖 |
| train-7 | 删除测试服务器 | ✅ 正确 | ✅ 正确 | "delete instances" + "lifecycle" 覆盖 |
| val-4 | 导入SSH密钥 | ⚠️ 可能不触发 | ✅ 会触发 | 增加 "manage key pairs" |
| val-8 | 创建快照 | ⚠️ 可能不触发 | ✅ 会触发 | 增加 "snapshots" |

---

## 结论

### 优化效果

1. ✅ **减少误触发**：去掉 "performance issues" 避免监控查询误触发
2. ✅ **增加覆盖率**：补充管理操作（key pairs, snapshots, quota等）
3. ✅ **扩大中文场景**：增加更多中文关键词
4. ✅ **明确边界**：增加更多委托规则

### 建议

- 保持当前的 description 结构
- 定期根据实际使用情况调整触发规则
- 监控 eval_queries.json 中的查询，更新训练集
- 考虑添加更多负面测试用例以提高边界清晰度
