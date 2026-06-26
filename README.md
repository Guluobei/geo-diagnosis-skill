# GEO 诊断报告 Skill v1.1

自动生成 GEO（生成式引擎优化）诊断报告的 AI Skill，支持行业适配和国内 AI 平台基线诊断。

## v1.1 核心特性

- **双层评分体系**：需求侧 6 维 + 供给侧 3 维
- **8 端平台测试**：豆包×2 + DeepSeek×2 + 腾讯元宝×2 + 百度AI + 文心
- **4 类问题精简化**：去掉竞品对比
- **4 文件输出**：HTML 报告 + CSV 问题库 + CSV 结果 + TXT 盲区词
- **三级降级方案**：浏览器自动化 / 读取报告 / WebSearch 模拟
- **执行摘要 + 盲区词分级**：红黄绿灯 + 5 等级判定
- **5 个真实踩坑案例**：基于实测经验

## 文件结构

```
├── SKILL.md                    # 核心指令文件
├── scripts/
│   └── render_report.py        # HTML 报告渲染脚本（支持 4 文件输出）
├── templates/
│   └── report.html             # HTML 骨架模板（12 个模块）
├── references/
│   ├── module-specs.md         # 12 个模块填写规范
│   └── scoring-rules.md        # 双层评分计算规则
└── industry/
    ├── _default.yaml           # 通用行业配置
    ├── saas.yaml               # SaaS 行业配置
    └── ecommerce.yaml          # 电商行业配置
```

## 快速开始

用户输入品牌名称即可启动诊断：
> "帮我做一下'云杉智能'的 GEO 诊断"

## 输出物

| 文件 | 说明 |
|------|------|
| `diagnosis-report-{brand}-v1-{date}.html` | 完整诊断报告（12 模块） |
| `test-questions-{date}.csv` | 测试问题库（4 类） |
| `test-results-{date}.csv` | 原始测试结果（10 列） |
| `blind-keywords-{date}.txt` | 盲区词列表（5 等级） |

## 许可

MIT License
