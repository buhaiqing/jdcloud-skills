# Scripts 目录结构

本目录按照 **AIOps 三阶段模型**组织：Perceive → Reason → Execute

## 目录结构

```
scripts/
├── 01-perceive/          # 感知层 — 数据收集与拓扑发现
│   └── cruise_sniff.py   #   Phase 1: 资源嗅探 + 拓扑初判
├── 02-reason/            # 推理层 — 分析与诊断
│   ├── cruise_analyze.py #   Phase 2: 全链路深度巡检与分析编排器
│   └── analyzers/        #   各资源类型分析器
│       ├── base_analyzer.py
│       ├── vm_analyzer.py
│       ├── clb_analyzer.py
│       ├── eip_analyzer.py
│       ├── redis_analyzer.py
│       ├── rds_mysql_analyzer.py
│       ├── k8s_analyzer.py
│       ├── nat_analyzer.py
│       ├── es_analyzer.py
│       └── sg_analyzer.py
├── 03-execute/           # 执行层 — 修复建议与闭环（本 Skill 为只读，见 README）
│   └── README.md
└── lib/                  # 共享库
    ├── jdc_client.py     #   JD Cloud CLI/SDK 封装
    └── resource_discovery.py  # 资源发现逻辑
```

## 三阶段说明

### 01-perceive（感知层）

**职责**: 数据采集、资源发现、拓扑构建

**输入**: 客户标签、区域范围
**输出**: 拓扑初判报告（JSON/Markdown）、置信度评估

**核心脚本**:
- `cruise_sniff.py` — 扫描客户标签下的所有资源，构建 VPC→子网→资源拓扑

### 02-reason（推理层）

**职责**: 指标分析、异常检测、根因定位、关联推理

**输入**: Phase 1 拓扑数据、监控指标、告警历史
**输出**: 深度巡检报告（findings + 建议）

**核心脚本**:
- `cruise_analyze.py` — 巡检分析编排器，驱动所有 analyzers
- `analyzers/*` — 各资源类型专用分析器

**Analyzer 开发规范**:
1. 继承 `BaseAnalyzer`
2. 实现 `discover()`, `query_metrics()`, `analyze()`, `report()` 方法
3. 输出标准 finding 格式（severity, resource, message, action）

### 03-execute（执行层）

**职责**: 修复建议生成、闭环跟踪

**设计约束**: 本 Skill 为纯只读巡检，不直接执行资源变更

**实际用途**:
- 生成标准化的 Action 建议（供人工确认后通过对应 ops skill 执行）
- 跟踪问题从发现到修复的闭环状态

**执行流程**:
```
发现问题 → 生成建议 → 人工确认 → 调用对应 ops skill → 闭环验证
```

## 执行顺序

```bash
# Phase 1: 感知
python 01-perceive/cruise_sniff.py --customer 烟台振华

# Phase 2: 推理（依赖 Phase 1 输出）
python 02-reason/cruise_analyze.py --customer 烟台振华 --sniff-file reports/output/sniff-xxx.json

# Phase 3: 执行建议（本 Skill 只生成建议，不直接执行）
# 根据 Phase 2 报告，人工确认后调用对应 skill:
# - jdcloud-vm-ops 处理 VM 相关建议
# - jdcloud-redis-ops 处理 Redis 相关建议
# - ...
```

## 扩展指南

新增资源类型分析器：
1. 在 `02-reason/analyzers/` 创建 `<resource>_analyzer.py`
2. 继承 `BaseAnalyzer`，注册到 `__init__.py`
3. 在 `references/threshold-definitions.md` 定义阈值
4. 更新 runbook 文档

## 版本

- v1.1.0 — 2026-06-08: 目录结构按 Preceive/Reason/Execute 三阶段重组
- v1.0.0 — 2026-06-06: 初始版本
