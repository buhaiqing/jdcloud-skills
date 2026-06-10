# 前提条件与环境配置

> 本文档从 `SKILL.md` 提取。
> 环境配置遵循 **jdc-first 降级策略**。

## 概述

1. **通过 `uv` 尝试安装 `jdc` CLI**（主路径）
2. 失败后**最多重试 3 次**（指数退避：0s → 2s → 4s）
3. **3 次连续失败后**，降级到 **仅 SDK** 环境

## Python 运行时 (uv)

`jdc` CLI 和 JD Cloud Python SDK 都需要 Python 运行时。使用 **`uv`** 进行本地隔离的幂等环境管理。

**安装 uv（系统级，每台机器只需一次）：**
```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
# 或通过 Homebrew: brew install uv
# Windows (PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

## 阶段 1：jdc CLI 安装（主路径）

> **Python 3.10 是必需的，不能使用 3.12。** `jdcloud_cli==1.2.12` 使用了在 Python 3.12 中已移除的 `SafeConfigParser`。请始终使用 `uv venv --python 3.10`。

```bash
uv venv --python 3.10
source .venv/bin/activate
uv pip install jdcloud_cli jdcloud_sdk
jdc --version
python -c "import jdcloud_sdk; print('SDK OK')"
```

### 重试逻辑（最多 3 次）

若 `jdc --version` 或任何 `jdc` 命令失败：

```bash
# 重试 1
uv pip install jdcloud_cli jdcloud_sdk
jdc --version && echo "OK" || echo "FAIL"

# 重试 2（等待 2 秒）
sleep 2
uv pip install --force-reinstall jdcloud_cli
jdc --version && echo "OK" || echo "FAIL"

# 重试 3（等待 4 秒）
sleep 4
uv pip install --force-reinstall jdcloud_cli jdcloud_sdk
jdc --version && echo "OK" || echo "FAIL"
```

若全部 **3 次重试**均失败，进入**阶段 2：SDK 降级**。

## 阶段 2：SDK 降级（3 次 jdc 失败后）

> **Python 3.10 是必需的，不能使用 3.12。**

```bash
uv venv --python 3.10
source .venv/bin/activate
uv pip install jdcloud_sdk
python -c "import jdcloud_sdk; print('SDK OK')"
```

## 配置凭证

> **CRITICAL:** The `jdc` CLI reads credentials **only** from `~/.jdc/config` INI file. Environment variables (`JDC_ACCESS_KEY`, `JDC_SECRET_KEY`) are **ignored** by the CLI. The SDK mode reads from environment variables. Use the appropriate method below.

### 方式 A：配置 SDK 凭证（环境变量）

Agent 运行时必须设置以下环境变量，对应本 Skill 中的 `{{env.*}}` 占位符：
```bash
export JDC_ACCESS_KEY="{{env.JDC_ACCESS_KEY}}"
export JDC_SECRET_KEY="{{env.JDC_SECRET_KEY}}"
export JDC_REGION="cn-north-1"
```

### 方式 B：配置 CLI 凭证（`~/.jdc/config` INI 文件）

```bash
# 沙箱环境需将 HOME 重定向到可写目录
export HOME=/tmp/jdc-home
mkdir -p /tmp/jdc-home/.jdc
cat > /tmp/jdc-home/.jdc/config << 'CONFIGEOF'
[default]
access_key = {{env.JDC_ACCESS_KEY}}
secret_key = {{env.JDC_SECRET_KEY}}
region_id = {{env.JDC_REGION}}
endpoint = monitor.jdcloud-api.com
scheme = https
timeout = 20
CONFIGEOF
# 关键：~/.jdc/current 必须包含 "default" 且不能有尾随换行符
printf "%s" "default" > /tmp/jdc-home/.jdc/current
```
