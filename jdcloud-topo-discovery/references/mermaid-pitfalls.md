# Mermaid 生成常见陷阱 (Mermaid Pitfalls)

> 本文档记录 `topo-render.py` 生成 Mermaid 图时遇到的真实错误模式，
> 作为后续开发和代码审查的参考。
>
> 每新增一个错误模式，请按下方模板追加。

---

## 陷阱索引

| # | 症状关键词 | 根因类别 | 首次发现 |
|:-:|-----------|----------|----------|
| 1 | `Expecting 'SQE'` + 标签中有 `()` | 特殊字符未转义 | 2026-06-09 |
| 2 | `Expecting 'TEXT', got 'PIPE'` + 标签中有 `\|` | 特殊字符未转义 | 2026-06-09 |
| 3 | 标签中出现 Python dict 字符串 | 嵌套字段未提取 | 2026-06-09 |
| 4 | `CSSStyleSheet is not defined` | render() 需要浏览器环境 | 2026-06-09 |
| 5 | `DOMPurify.addHook is not a function` | mermaid v11 + dompurify v3 兼容性 | 2026-06-09 |

---

## 陷阱 1: 标签中的括号 `()`

### 症状

```
Parse error on line 2:
...  subgraph VPC[丹东鹏飞 (vpc-24lk5go6oj)]
-----------------------^
Expecting 'SQE', 'DOUBLECIRCLEEND', 'PE', '-)', ...
```

### 根因

Mermaid 中 `[label]` 表示矩形节点，`(label)` 表示圆角节点。
当标签中包含 `(` 或 `)` 时，Mermaid 解析器会将其误判为节点形状语法。

### 修复

使用 `mermaid_escape()` 将 `()` 转义为 HTML 实体：

```python
from lib.mermaid_safe import mermaid_escape

# ❌ 错误
label = f"丹东鹏飞 ({vpc_id})"

# ✅ 正确
label = mermaid_escape(f"丹东鹏飞 ({vpc_id})")
# 输出: "丹东鹏飞 &#40;vpc-24lk5go6oj&#41;"
```

### 相关

- `lib/mermaid_safe.py` → `mermaid_escape()`
- `lib/mermaid_safe.py` → `mermaid_safe_vpc_label()`

---

## 陷阱 2: 标签中的管道符 `|`

### 症状

```
Parse error on line 4:
...hicj3hhk0[鹏飞-CRM-DB | 172.21.14.96/27]
-----------------------^
Expecting 'SQE', 'TAGEND', 'UNICODE_TEXT', 'TEXT', 'TAGSTART', got 'PIPE'
```

### 根因

Mermaid 中 `|` 是管道/分隔符 token，在 `[label]` 内部出现时会被解析器误判。

### 修复

使用 `mermaid_escape()` 将 `|` 转义为 `&#124;`：

```python
from lib.mermaid_safe import mermaid_escape

# ❌ 错误
label = f"{name} | {cidr}"

# ✅ 正确
label = mermaid_escape(f"{name} | {cidr}")
# 输出: "鹏飞-CRM-DB &#124; 172.21.14.96/27"
```

### 相关

- `lib/mermaid_safe.py` → `mermaid_escape()`
- `lib/mermaid_safe.py` → `mermaid_safe_subgraph_label()`

---

## 陷阱 3: 嵌套 JSON 字段被当作字符串

### 症状

Mermaid 节点标签中出现 Python dict 字符串：

```
res_alb_z5aeeqhdtj[✅ 丹东鹏飞\n{'privateIpAddress': '172.21.14.4', 'elasticIpId': 'fip-xxx', ...}]
```

### 根因

JD Cloud API 返回的某些字段是嵌套对象而非字符串：

```json
{
  "privateIp": {
    "privateIpAddress": "172.21.14.4",
    "elasticIpId": "fip-jh2nz2k0s9",
    "elasticIpAddress": "116.196.75.209"
  }
}
```

代码直接取了 `data.get('privateIp', '')`，得到整个 dict。

### 修复

使用 `mermaid_extract_str()` 安全提取嵌套字段：

```python
from lib.mermaid_safe import mermaid_extract_str

# ❌ 错误: 得到整个 dict
ip = data.get('privateIp', '')

# ✅ 正确: 提取内层字段
ip = mermaid_extract_str(data, 'privateIp.privateIpAddress')
# 输出: "172.21.14.4"
```

### 相关

- `lib/mermaid_safe.py` → `mermaid_extract_str()`

---

## 陷阱 4: `mermaid.render()` 需要浏览器环境

### 症状

```
❌ Render failed: CSSStyleSheet is not defined
```

### 根因

`mermaid.render()` 需要完整的浏览器 DOM 环境（CSSStyleSheet、Canvas 等），
在 Node.js 中需要 puppeteer/playwright 提供。

### 修复

**语法校验用 `mermaid.parse()`**（仅需 jsdom，已在 `lint.mjs` 中处理），
**渲染用 `mermaid.render()`** 需要 puppeteer 环境。

```javascript
// ✅ 语法校验（轻量，Node.js 可用）
await mermaid.parse(code);

// ❌ 渲染（需要浏览器环境）
await mermaid.render('id', code);
```

### 相关

- `scripts/mermaid-lint/lint.mjs` → 使用 `mermaid.parse()` 做语法校验

---

## 陷阱 5: mermaid v11 + dompurify v3 兼容性

### 症状

```
DOMPurify.addHook is not a function
```

### 根因

mermaid v11 内部使用 `DOMPurify.addHook`，但 dompurify v3.x 移除了该 API。
mermaid v11 自带的 dompurify 是 v3.4.8，不兼容。

### 修复

在 Node.js 中使用 CJS 方式加载 mermaid，并在加载前设置 `globalThis.DOMPurify`
为 dompurify v2.x 版本：

```javascript
// 1. 设置 DOM 环境
const window = new jsdom.JSDOM('').window;
globalThis.window = window;
globalThis.document = window.document;

// 2. 使用 dompurify v2.x（有 addHook）
const purify = dompurify(window);
globalThis.DOMPurify = purify;

// 3. 加载 mermaid（CJS 方式）
const mermaid = require('mermaid');
const M = mermaid.default || mermaid;
M.initialize({ startOnLoad: false });
```

### 相关

- `scripts/mermaid-lint/lint.mjs` → 已处理此兼容性问题
- `scripts/mermaid-lint/package.json` → 锁定 `dompurify@^2.5.8`

---

## 通用修复模式

### 修复流程

```
发现错误
    │
    ▼
1. 识别错误类型（对照本文档）
    │
    ▼
2. 在 lib/mermaid_safe.py 中添加/复用工具函数
    │
    ▼
3. 在 topo-render.py 中替换裸字符串拼接
    │
    ▼
4. 运行 mermaid-lint 验证
    │
    ▼
5. 将新错误模式追加到本文档
```

### 代码审查检查点

在审查 Mermaid 生成代码时，检查以下模式：

- [ ] 是否存在 `f"... ({...})"` 裸括号拼接 → 改用 `mermaid_safe_vpc_label()`
- [ ] 是否存在 `f"... | ..."` 裸管道符拼接 → 改用 `mermaid_safe_subgraph_label()`
- [ ] 是否存在 `data.get('field', '')` 可能返回 dict → 改用 `mermaid_extract_str()`
- [ ] 是否存在未转义的 `[]` `{}` `"` → 改用 `mermaid_escape()`
- [ ] 节点 ID 是否包含 `.` `-` 以外字符 → 改用 `mermaid_safe_id()`
- [ ] 标签是否可能超过 200 字符 → 改用 `mermaid_safe_label()`

---

## 变更记录

| 日期 | 版本 | 变更 |
|------|------|------|
| 2026-06-09 | 1.0.0 | 初始版本，收录 5 个已知陷阱 |
