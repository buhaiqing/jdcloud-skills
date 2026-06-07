# 安全门规范 (Safety Gate)

## 核心原则

本 Skill 的所有执行路径必须严格遵守 **只读 (Read-Only)** 策略。

## 允许的操作

| API 前缀 | 说明 |
|---------|------|
| `describe*` | 查询资源详情/列表(京东云 CLI 全部 `describe-*` 子命令) |
| `list*` | 查询资源列表(部分资源如 `describe-sub-users` 返回列表语义) |
| `get*` | 查询单个资源详情(京东云无独立 `get-*`,统一为 `describe-*`) |
| `sts assume-role` | **特殊情况**:跨账号扫描时允许调用 STS AssumeRole。此操作改变调用者身份但不改变目标资源。仅在 `--assume-role` 显式指定时触发。 |

## 禁止的操作

| API 前缀 | 风险说明 |
|---------|----------|
| `create*` | 创建/新建资源 |
| `delete*` | 删除/释放资源 |
| `modify*` | 修改配置/状态 |
| `update*` | 更新资源信息 |
| `associate*` | 关联绑定 (如 EIP 绑定、子网绑 ACL) |
| `disassociate*` | 解绑/分离资源 |
| `attach*` / `detach*` | 挂载/卸载(磁盘、安全组等) |
| `enable*` / `disable*` | 启用/停用(KMS 密钥、ActionTrail 等) |
| `reset*` | 重置(密码、密钥) |
| `start*` / `stop*` / `reboot*` | 启停/重启实例 |
| `restore*` / `failover*` | 恢复/故障切换 |
| `schedule*` | 计划操作(如 KMS key deletion) |
| `add*` / `remove*` (路由表/ACL/安全组规则) | 修改网络规则 |
| `grant*` / `revoke*` | 授权/撤销(策略、权限) |
| `terminate*` | 终止实例 |

> **京东云特定注意**:
> - `jdc vpc create-*` 是危险操作(创建 VPC/Subnet/ACL/SG/Route/ENI 等)
> - `jdc kms disable-key` / `enable-key` 是危险操作
> - `jdc iam create-*` / `attach-*` / `detach-*` 是危险操作
> - `jdc sts assume-role` 是**唯一允许**的写凭证操作(改变调用者身份,不修改资源)

## 执行前验

所有 CLI 命令在执行前必须经过正则匹配验证:

```python
# 京东云 CLI 命名约定:kebab-case 子命令
ALLOWED_PATTERN = r"^(describe|list|get|sts assume-role)"
FORBIDDEN_PATTERN = r"^(create|delete|modify|update|associate|disassociate|attach|detach|enable|disable|reset|start|stop|reboot|restore|failover|schedule|grant|revoke|terminate|add|remove)"
```

任何不匹配 `ALLOWED_PATTERN` 的命令将导致程序立即终止 (HALT)。

> **注**:`sts assume-role` 仅当 `--assume-role` 参数显式传入时才被调用。该操作改变调用者身份但不修改任何云资源,属于允许的例外。
