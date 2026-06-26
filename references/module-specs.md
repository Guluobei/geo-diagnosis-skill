# GEO诊断报告 - 十大模块填写规范

## 概述

GEO诊断报告由十大模块组成，每个模块有明确的数据结构和填写要求。本文档定义每个模块的字段规范、数据来源和填写标准。

---

## 模块 0：报告头部（Header）

### 用途
报告元信息，标识报告基本信息。

### 字段定义

| 字段 | 路径 | 类型 | 必填 | 说明 |
|------|------|------|------|------|
| 品牌名称 | `meta.brand` | string | 是 | 诊断品牌的全称 |
| 行业 | `meta.industry` | string | 是 | 品牌所属行业 |
| 诊断日期 | `meta.date` | string | 是 | 格式 YYYY-MM-DD |
| 诊断师 | `meta.diagnostician` | string | 是 | 执行诊断的人员/系统名称 |

### 填写示例

```json
{
  "meta": {
    "brand": "示例品牌",
    "industry": "SaaS",
    "date": "2026-06-17",
    "diagnostician": "GEO诊断系统"
  }
}
```

---

## 模块 1：诊断目标与用户画像

### 用途
明确诊断范围、目标用户和核心问题集。

### 1.1 诊断目标（goals）

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | string | 是 | 目标编号，如 G1、G2 |
| description | string | 是 | 目标描述 |
| priority | string | 是 | P0/P1/P2 |
| priority_tag | string | 是 | CSS类名：green/yellow/red |
| metric | string | 是 | 衡量指标 |

### 1.2 目标用户画像（target_users）

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| type | string | 是 | 用户类型名称 |
| needs | string | 是 | 核心需求描述 |
| typical_queries | string | 是 | 典型查询，逗号分隔 |
| stage | string | 是 | 决策阶段：认知/考虑/决策/留存 |

### 1.3 核心问题集（question_set）

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| category | string | 是 | 问题类别 |
| examples | string | 是 | 示例问题，逗号分隔 |
| priority | string | 是 | high/medium/low |
| priority_tag | string | 是 | CSS类名：green/yellow/red |

### 数据来源
- 品牌方提供的业务信息
- 行业配置文件中的 `target_users` 和 `question_categories`

---

## 模块 2：AI平台问答实测

### 用途
记录在主流AI平台上的实际问答测试结果。

### 2.1 测试平台概览（platforms）

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | string | 是 | 平台名称 |
| test_date | string | 是 | 测试日期 |
| question_count | number | 是 | 测试问题数量 |
| mention_rate | string | 是 | 品牌提及率，如 "80%" |
| mention_tag | string | 是 | CSS类名：green/yellow/red |
| accuracy | string | 是 | 回答准确度，如 "75%" |
| accuracy_tag | string | 是 | CSS类名：green/yellow/red |

### 2.2 问答记录详情（question_records）

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| index | number | 是 | 问题序号 |
| question | string | 是 | 测试问题原文 |
| platform | string | 是 | 回答平台 |
| answer_summary | string | 是 | AI回答摘要（200字以内） |
| brand_mention | string | 是 | 品牌是否被提及及方式 |
| source | string | 是 | AI引用的信息来源 |
| evaluation | string | 是 | 对回答质量的评价 |
| severity | string | 是 | callout类型：info/warn/danger |
| severity_icon | string | 是 | 图标字符：i/!/x |

### 2.3 信息来源偏好（source_preference）

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| source_type | string | 是 | 来源类型（官网/媒体/论坛/社交等） |
| count | number | 是 | 出现次数 |
| percentage | string | 是 | 占比 |
| credibility | string | 是 | 可信度评级 |
| credibility_tag | string | 是 | CSS类名：green/yellow/red |

### 2.4 缺失信息汇总（missing_info）

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| info | string | 是 | 缺失的信息描述 |
| impact | string | 是 | 影响范围 |
| severity | string | 是 | 严重程度：高/中/低 |
| severity_tag | string | 是 | CSS类名：red/yellow/green |
| suggestion | string | 是 | 建议操作 |

### 2.5 回答结构分析（answer_structure）

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| dimension | string | 是 | 结构维度名称 |
| status | string | 是 | 达标/部分达标/未达标 |
| status_tag | string | 是 | CSS类名：green/yellow/red |
| description | string | 是 | 详细说明 |

### 数据来源
- AI平台实际测试记录
- 行业配置中的 `ai_platforms`

---

## 模块 3：品牌信息覆盖度

### 用途
评估品牌核心信息在AI可获取来源中的覆盖程度。

### 3.1 信息覆盖总览（coverage）

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| category | string | 是 | 覆盖类别 |
| score | number | 是 | 得分 |
| max_score | number | 是 | 满分 |
| percentage | number | 是 | 百分比（用于进度条宽度） |
| grade_class | string | 是 | CSS类名：excellent/good/fair/poor |

### 3.2 信息卡片（fact_cards）

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| title | string | 是 | 信息项标题 |
| status | string | 是 | 状态：完整/部分/缺失 |
| status_tag | string | 是 | CSS类名：green/yellow/red |
| current_state | string | 是 | 当前实际状态 |
| ai_perception | string | 是 | AI对该信息的认知 |
| gap_analysis | string | 是 | 差距分析 |

### 3.3 信息一致性检查（consistency）

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| item | string | 是 | 信息项名称 |
| official | string | 是 | 官网信息 |
| third_party | string | 是 | 第三方平台信息 |
| ai_answer | string | 是 | AI回答中的信息 |
| consistency | string | 是 | 一致性：一致/偏差/矛盾 |
| consistency_tag | string | 是 | CSS类名：green/yellow/red |

### 数据来源
- 官网内容审计
- 第三方平台信息收集
- AI平台问答对比

---

## 模块 4：内容结构合规性

### 用途
检查现有内容是否满足AI搜索引擎的结构化抓取要求。

### 4.1 内容清单（content_list）

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| type | string | 是 | 内容类型 |
| priority | string | 是 | P0/P1/P2 |
| priority_tag | string | 是 | CSS类名：red/yellow/green |
| status | string | 是 | 状态：已发布/草稿/缺失 |
| status_tag | string | 是 | CSS类名：green/yellow/red |
| url | string | 否 | 内容URL或位置 |
| updated_at | string | 否 | 最后更新日期 |

### 4.2 结构合规检查（structure_compliance）

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| item | string | 是 | 合规检查项 |
| requirement | string | 是 | 具体要求 |
| status | string | 是 | 达标/部分达标/未达标 |
| status_tag | string | 是 | CSS类名：green/yellow/red |
| note | string | 否 | 备注说明 |

### 4.3 内容质量检查清单（content_quality_checks）

使用 `_checklist` 语法，每项格式：

```
[pass/fail/partial/pending] 检查项描述
```

### 数据来源
- 网站技术审计
- 结构化数据验证工具
- 行业配置中的 `content_types`

---

## 模块 5：分发渠道覆盖

### 用途
评估品牌在自有渠道、第三方平台和分发层级的覆盖情况。

### 5.1 自有渠道（owned_channels）

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | string | 是 | 渠道名称 |
| type | string | 是 | 渠道类型（官网/公众号/视频号等） |
| status | string | 是 | 状态：活跃/维护中/停更 |
| status_tag | string | 是 | CSS类名：green/yellow/red |
| crawlable | string | 是 | AI可抓取：是/部分/否 |
| crawl_tag | string | 是 | CSS类名：green/yellow/red |
| richness | string | 是 | 内容丰富度：高/中/低 |
| richness_tag | string | 是 | CSS类名：green/yellow/red |

### 5.2 第三方平台（third_party）

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | string | 是 | 平台名称 |
| status | string | 是 | 入驻状态：已入驻/未入驻 |
| status_tag | string | 是 | CSS类名：green/red |
| content_count | number | 否 | 内容数量 |
| frequency | string | 否 | 更新频率 |
| impact | string | 是 | 影响力：高/中/低 |
| impact_tag | string | 是 | CSS类名：green/yellow/red |

### 5.3 分发层级分析（distribution_layers）

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| layer | string | 是 | 层级名称（L1核心/L2扩展/L3影响/L4长尾） |
| channel_count | number | 是 | 已覆盖渠道数 |
| score | string | 是 | 覆盖评分 |
| score_tag | string | 是 | CSS类名：green/yellow/red |
| suggestion | string | 是 | 改进建议 |

### 数据来源
- 品牌方渠道清单
- 第三方平台搜索验证

---

## 模块 6：素材资产管理

### 用途
盘点品牌可复用的素材资产及管理规范。

### 6.1 素材清单（materials）

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | string | 是 | 素材名称 |
| type | string | 是 | 素材类型（文档/图片/视频/数据等） |
| format | string | 是 | 文件格式 |
| usage | string | 是 | 适用场景 |
| updated_at | string | 否 | 更新日期 |
| status | string | 是 | 状态：可用/需更新/缺失 |
| status_tag | string | 是 | CSS类名：green/yellow/red |

### 6.2 管理规范检查（management_rules）

使用 `_checklist` 语法，每项格式：

```
[pass/fail/partial/pending] 规范检查项描述
```

### 数据来源
- 品牌方素材库审计
- 内容管理流程评估

---

## 模块 7：综合评分与优先级矩阵

### 用途
基于六维评分模型给出综合评分及优化优先级。

### 7.1 六维评分（scores）

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| dimension | string | 是 | 维度名称 |
| score | number | 是 | 得分 |
| max_score | number | 是 | 满分（通常为100） |
| percentage | number | 是 | 百分比 |
| grade_class | string | 是 | CSS类名：excellent/good/fair/poor |

附加字段：
- `total_score`: 综合加权总分
- `overall_grade`: 综合等级（S/A/B/C/D）
- `overall_tag`: CSS类名（green/green/blue/yellow/red）

### 7.2 优先级矩阵（priority_matrix）

四个象限，每个象限为数组：

| 象限 | 路径 | 说明 |
|------|------|------|
| 紧急且重要 | `priority_matrix.urgent` | 立即处理 |
| 重要不紧急 | `priority_matrix.important` | 计划处理 |
| 紧急不重要 | `priority_matrix.maintain` | 委托处理 |
| 不紧急不重要 | `priority_matrix.low` | 持续关注 |

每个条目字段：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| item | string | 是 | 优化项描述 |
| impact | string | 是 | 影响程度：高/中/低 |

### 数据来源
- 前六个模块的诊断数据汇总
- 评分规则（见 `scoring-rules.md`）

---

## 模块 8：常见误区与风险提示

### 用途
列举GEO优化中的常见误区和风险。

### 误区条目（pitfalls）

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| title | string | 是 | 误区标题 |
| severity | string | 是 | 严重程度：高/中/低 |
| severity_tag | string | 是 | CSS类名：red/yellow/green |
| description | string | 是 | 误区描述 |
| fix | string | 是 | 正确做法 |

### 数据来源
- 行业配置中的 `high_risk_claims`
- GEO优化最佳实践
- 常见品牌踩坑案例

---

## 模块 9：优化行动计划

### 用途
按周拆分的4周优化行动计划。

### 9.1 周计划（week1-4）

使用 `_checklist` 语法，每项格式：

```
[pass/fail/partial/pending] 任务描述 | 负责人 | 截止日期
```

### 9.2 衡量指标（metrics）

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | string | 是 | 指标名称 |
| current | string | 是 | 当前值 |
| target | string | 是 | 目标值 |
| method | string | 是 | 衡量方式 |
| cycle | string | 是 | 检查周期（周/双周/月） |

### 数据来源
- 前序模块的诊断结论
- 行业基准数据
- 品牌方资源评估

---

## 模块 10：回答模板库

### 用途
为高频问题提供标准化回答模板。

### 模板条目（templates）

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | string | 是 | 模板名称 |
| priority | string | 是 | P0/P1/P2 |
| priority_tag | string | 是 | CSS类名：red/yellow/green |
| applicable_questions | string | 是 | 适用问题，逗号分隔 |
| content | string | 是 | 模板内容（支持多行） |

### 填写原则

1. 每个模板对应一类高频问题
2. 模板内容需包含品牌核心信息点
3. 避免使用绝对化用语（参考 `high_risk_claims`）
4. 保持语言简洁、结构清晰
5. 定期根据AI回答变化更新模板

### 数据来源
- 模块2中的高频问题
- 品牌方提供的标准话术
- 行业最佳实践

---

## 通用填写规范

### 标签颜色映射

| 状态/等级 | CSS类名 | 适用场景 |
|----------|---------|---------|
| 正向/优秀 | green | 达标、完整、高覆盖 |
| 中性/良好 | blue | 一般信息、参考项 |
| 警告/一般 | yellow | 部分达标、需改进 |
| 危险/较差 | red | 未达标、缺失、高风险 |

### Checklist 状态

| 状态 | 图标 | 含义 |
|------|------|------|
| pass | 对勾 | 已完成/已达标 |
| fail | 叉号 | 未完成/未达标 |
| partial | 横线 | 部分完成 |
| pending | 圆点 | 待处理 |

### 数据格式要求

1. 日期统一使用 `YYYY-MM-DD` 格式
2. 百分比统一使用 `XX%` 格式
3. 分数统一使用数字类型
4. 多值字段使用逗号分隔
5. URL字段需包含完整协议前缀
