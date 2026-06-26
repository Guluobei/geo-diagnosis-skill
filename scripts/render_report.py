#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
render_report.py — GEO 诊断报告渲染脚本 v1.1

功能概述：
  - 双模式命令行：
      1) --data <json> --template <html> --output <html>  (v1.0 兼容)
      2) --data <json> --template <html> --output-dir <dir>
         [--brand <brand>] [--date <date>]                  (v1.1 新增)
  - 模板引擎：纯 Python 标准库实现，支持变量替换、条件、循环及 6 个辅助指令
  - 自动注入默认样式（若模板无 <style> 标签）
  - CSV / TXT 输出（按指定字段映射）
  - 仅依赖标准库：json, re, html, os, sys, argparse, datetime, csv

作者：TRAE Agent
"""

import argparse
import csv
import datetime
import html as html_lib
import json
import os
import re
import sys
from collections import OrderedDict


# ============================================================================
# 常量与默认值
# ============================================================================

# 默认样式：自动注入到没有 <style> 的模板
DEFAULT_STYLE = """
<style>
/* GEO 报告默认样式（自动注入） */
.kpi-card {
  display: inline-block; min-width: 160px; padding: 12px 16px;
  margin: 6px 8px 6px 0; border-radius: 8px;
  background: #FFFFFF; box-shadow: 0 1px 3px rgba(0,0,0,0.06);
  border-left: 4px solid #6B7280; vertical-align: top;
}
.kpi-card .kpi-value { font-size: 1.6rem; font-weight: 700; line-height: 1.2; }
.kpi-card .kpi-label { font-size: 0.85rem; color: #6B7280; margin-top: 4px; }
.kpi-card .kpi-grade { font-size: 0.75rem; margin-top: 2px; color: #6B7280; }
.kpi-card.grade-good    { border-left-color: #16A34A; }
.kpi-card.grade-good .kpi-value    { color: #16A34A; }
.kpi-card.grade-warn    { border-left-color: #CA8A04; }
.kpi-card.grade-warn .kpi-value    { color: #CA8A04; }
.kpi-card.grade-bad     { border-left-color: #DC2626; }
.kpi-card.grade-bad .kpi-value     { color: #DC2626; }

.score-card {
  background: #FFFFFF; padding: 12px 16px; border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.06); margin: 8px 0;
}
.score-bar { background: #E2E5EA; height: 10px; border-radius: 5px; overflow: hidden; }
.score-bar > span { display: block; height: 100%; background: #6B7280; }
.score-card.grade-good  .score-bar > span { background: #16A34A; }
.score-card.grade-warn  .score-bar > span { background: #CA8A04; }
.score-card.grade-bad   .score-bar > span { background: #DC2626; }
.score-card .score-num { font-weight: 700; font-size: 1.1rem; }

.callout {
  padding: 12px 16px; border-radius: 8px; margin: 12px 0;
  border-left: 4px solid #6B7280; background: #F8FAFC;
}
.callout.info    { border-left-color: #2563EB; background: #EFF6FF; }
.callout.success { border-left-color: #16A34A; background: #F0FDF4; }
.callout.warn    { border-left-color: #CA8A04; background: #FEFCE8; }
.callout.danger  { border-left-color: #DC2626; background: #FEF2F2; }
.callout.tip     { border-left-color: #0EA5E9; background: #ECFEFF; }
.callout .callout-title { font-weight: 600; margin-bottom: 4px; }

.tag {
  display: inline-block; padding: 2px 8px; border-radius: 10px;
  font-size: 0.78rem; line-height: 1.4; font-weight: 600;
  background: #E2E5EA; color: #1A1D23;
}
.tag.p0   { background: #FEE2E2; color: #B91C1C; }
.tag.p1   { background: #FEF3C7; color: #92400E; }
.tag.p2   { background: #DCFCE7; color: #166534; }
.tag.yes  { background: #DCFCE7; color: #166534; }
.tag.no   { background: #FEE2E2; color: #B91C1C; }
.tag.true { background: #DCFCE7; color: #166534; }
.tag.false{ background: #FEE2E2; color: #B91C1C; }

.checklist { list-style: none; padding-left: 0; }
.checklist li { padding: 4px 0 4px 22px; position: relative; }
.checklist li::before {
  content: "☐"; position: absolute; left: 0; color: #6B7280; font-weight: 700;
}
.checklist li.done::before { content: "☑"; color: #16A34A; }
</style>
"""

# 默认等级文本
GRADE_TEXT = {
    "good": "良好",
    "warn": "一般",
    "bad":  "较差",
}

# 标签颜色推断：按 P0/P1/P2 映射
TAG_COLOR_MAP = {
    "p0": "p0", "p1": "p1", "p2": "p2",
    "高": "p0", "中": "p1", "低": "p2",
    "high": "p0", "medium": "p1", "low": "p2",
}


# ============================================================================
# 工具函数
# ============================================================================

def safe_get(data, path, default=""):
    """按点分路径取值，路径不合法或不存在时返回默认值。"""
    if not path:
        return default
    cur = data
    for part in path.split("."):
        if part == "":
            continue
        # 支持数组下标写法，如 items.0.name
        if isinstance(cur, list):
            try:
                idx = int(part)
                cur = cur[idx]
                continue
            except (ValueError, IndexError):
                return default
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        else:
            return default
    return cur if cur is not None else default


def html_escape(value):
    """HTML 转义。"""
    if value is None:
        return ""
    if isinstance(value, (int, float)):
        return str(value)
    return html_lib.escape(str(value), quote=True)


def to_text(value):
    """转成纯文本（用于 CSV/TXT 字段）。"""
    if value is None:
        return ""
    if isinstance(value, bool):
        return "是" if value else "否"
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    return str(value)


def is_truthy(value):
    """判定真值。空字符串、0、None、false、[]、{} 都视为假。"""
    if value is None:
        return False
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, (list, dict, str)):
        return len(value) > 0
    return True


def pick_first(data, candidates, default=""):
    """从候选字段名列表中按顺序取第一个存在的值。"""
    for name in candidates:
        if "." in name:
            val = safe_get(data, name, None)
        else:
            val = data.get(name) if isinstance(data, dict) else None
        if val is not None and val != "":
            return val
    return default


# ============================================================================
# 表达式求值（条件指令用）
# ============================================================================

def eval_condition(expr, data, this_ctx=None):
    """
    求值条件表达式。支持：
      path           存在且真
      !path          假或不存在
      path == value  字符串/数字相等
      path != value  不等
      组合：expr1 && expr2 / expr1 || expr2（简单支持）
    """
    if expr is None:
        return True

    expr = expr.strip()
    if not expr:
        return True

    # 复合表达式：按 || 拆分
    if "||" in expr:
        parts = [p.strip() for p in expr.split("||")]
        return any(eval_condition(p, data, this_ctx) for p in parts)

    # 复合表达式：按 && 拆分
    if "&&" in expr:
        parts = [p.strip() for p in expr.split("&&")]
        return all(eval_condition(p, data, this_ctx) for p in parts)

    # 取反
    if expr.startswith("!"):
        return not eval_condition(expr[1:].strip(), data, this_ctx)

    # 相等/不等
    for op, op_func in [("==", lambda a, b: a == b),
                        ("!=", lambda a, b: a != b)]:
        if op in expr:
            left, right = expr.split(op, 1)
            left = left.strip()
            right = right.strip()
            # 左侧是路径
            lv = resolve_path(left, data, this_ctx)
            # 右侧可能是字面量（数字 / 字符串）
            rv = parse_literal(right)
            return op_func(lv, rv)

    # 纯路径：存在且真
    val = resolve_path(expr, data, this_ctx)
    return is_truthy(val)


def parse_literal(s):
    """解析字面量：数字、布尔、字符串（去引号）。"""
    s = s.strip()
    if s.lower() in ("true", "是", "yes"):
        return True
    if s.lower() in ("false", "否", "no", ""):
        return False
    if (s.startswith('"') and s.endswith('"')) or (s.startswith("'") and s.endswith("'")):
        return s[1:-1]
    try:
        if "." in s:
            return float(s)
        return int(s)
    except ValueError:
        return s


def resolve_path(path, data, this_ctx=None):
    """
    解析路径。
    优先级：this.xxx 显式前缀 > 顶层 data 的子键 > this_ctx (foreach item) > 空。
    这样在 foreach 内可以直接写 {{text}} 引用当前项的字段。
    """
    if not path:
        return data
    if path in ("this", "."):
        return this_ctx if this_ctx is not None else data
    if path.startswith("this."):
        sub = path[5:]
        if isinstance(this_ctx, dict):
            return this_ctx.get(sub, "")
        return safe_get(this_ctx or {}, sub, "")
    # 1) 优先在 data 中查找
    val = safe_get(data, path, None)
    if val not in (None, ""):
        return val
    # 2) 回退到 this_ctx（foreach 当前项）
    if isinstance(this_ctx, dict):
        if path in this_ctx:
            v = this_ctx[path]
            return v if v is not None else ""
    # 3) 路径形式（点分）也允许在 this_ctx 上
    v = safe_get(this_ctx or {}, path, None)
    if v is not None:
        return v
    return ""


# ============================================================================
# 辅助指令渲染
# ============================================================================

def resolve_helper_args(arg_str, data, this_ctx):
    """
    解析辅助指令参数。规则：
      - 不带引号的 token 视为路径（从 data/this_ctx 取值）
      - 带引号的 token（单/双引号）视为字面量
      - 数字字面量直接解析
    返回：已解析的 token 列表（保留顺序）。
    """
    tokens = []
    i = 0
    s = arg_str.strip()
    while i < len(s):
        if s[i].isspace():
            i += 1
            continue
        if s[i] in ('"', "'"):
            quote = s[i]
            j = i + 1
            buf = []
            while j < len(s) and s[j] != quote:
                if s[j] == "\\" and j + 1 < len(s):
                    buf.append(s[j + 1])
                    j += 2
                else:
                    buf.append(s[j])
                    j += 1
            tokens.append(("literal", "".join(buf)))
            i = j + 1
        else:
            j = i
            while j < len(s) and not s[j].isspace():
                j += 1
            token = s[i:j]
            # 数字字面量
            if re.fullmatch(r"-?\d+(\.\d+)?", token):
                tokens.append(("literal", parse_literal(token)))
            # 已知 grade 关键字：good/warn/bad/优/良/差/高/中/低 等
            elif token.lower() in ("good", "warn", "warning", "bad", "danger",
                                    "info", "tip", "success", "error",
                                    "优", "良", "差", "高", "中", "低"):
                tokens.append(("literal", token))
            # 已知 tag 关键字
            elif token.upper() in ("P0", "P1", "P2", "TRUE", "FALSE", "YES", "NO"):
                tokens.append(("literal", token))
            else:
                tokens.append(("path", token))
            i = j
    return tokens


def render_tag(value, data, this_ctx):
    """{{_tag value}} 彩色标签。"""
    raw = resolve_value_token(value, data, this_ctx)
    text = to_text(raw).strip()
    if not text:
        return ""
    # 推断 class
    key = text.lower()
    css = TAG_COLOR_MAP.get(key, "")
    cls = f'tag {css}' if css else "tag"
    return f'<span class="{cls}">{html_escape(text)}</span>'


def render_bool(value, data, this_ctx):
    """{{_bool value}} 是/否布尔标签。"""
    raw = resolve_value_token(value, data, this_ctx)
    truthy = is_truthy(raw)
    if isinstance(raw, str):
        s = raw.strip().lower()
        if s in ("是", "yes", "true", "1", "y", "t"):
            truthy = True
        elif s in ("否", "no", "false", "0", "n", "f"):
            truthy = False
    if truthy:
        return '<span class="tag yes">是</span>'
    return '<span class="tag no">否</span>'


def render_callout(type_token, inner, data, this_ctx):
    """{{_callout type}}...{{_/callout}} 提示框。"""
    raw = resolve_value_token(type_token, data, this_ctx)
    t = to_text(raw).strip().lower()
    if t not in ("info", "warn", "warning", "success", "danger", "tip", "error"):
        t = "info"
    if t == "warning":
        t = "warn"
    if t == "error":
        t = "danger"
    title_map = {
        "info": "提示", "warn": "注意", "success": "成功",
        "danger": "警告", "tip": "小贴士",
    }
    title = title_map[t]
    return (f'<div class="callout {t}">'
            f'<div class="callout-title">{title}</div>'
            f'<div class="callout-body">{inner}</div>'
            f'</div>')


def render_checklist(path_token, inner, data, this_ctx):
    """{{_checklist path}}...{{/_checklist}} 清单。"""
    items = resolve_value_token(path_token, data, this_ctx)
    if not isinstance(items, list):
        return ""
    rows = []
    for it in items:
        if not isinstance(it, dict):
            rows.append(f'<li>{html_escape(to_text(it))}</li>')
            continue
        done = is_truthy(it.get("done", it.get("checked", it.get("completed", False))))
        text = (it.get("text") or it.get("title") or it.get("name") or
                it.get("keyword") or it.get("word") or it.get("term") or
                it.get("label") or "")
        cls = " class=\"done\"" if done else ""
        rows.append(f'<li{cls}>{html_escape(to_text(text))}</li>')
    body = "\n".join(rows) if rows else inner
    return f'<ul class="checklist">\n{body}\n</ul>'


def render_score(path_token, data, this_ctx):
    """{{_score path}} 评分卡片。"""
    raw = resolve_value_token(path_token, data, this_ctx)
    # 支持传入 dict {value, label, grade} 或纯数字
    if isinstance(raw, dict):
        val = raw.get("value", raw.get("score", 0))
        label = raw.get("label", raw.get("name", ""))
        grade = raw.get("grade", "")
    else:
        val = raw
        label = ""
        grade = ""
    try:
        val_num = float(val)
    except (TypeError, ValueError):
        return ""
    # 归一化到 0-100
    if val_num <= 1:
        val_num *= 100
    val_num = max(0.0, min(100.0, val_num))
    if not grade:
        if val_num >= 80:
            grade = "good"
        elif val_num >= 60:
            grade = "warn"
        else:
            grade = "bad"
    label_html = f'<div class="score-label">{html_escape(to_text(label))}</div>' if label else ""
    return (f'<div class="score-card grade-{grade}">'
            f'{label_html}'
            f'<div class="score-num">{val_num:.1f}</div>'
            f'<div class="score-bar"><span style="width:{val_num:.1f}%"></span></div>'
            f'</div>')


def render_kpi(args, data, this_ctx):
    """
    {{_kpi value grade label [grade_text]}} 红黄绿灯指标卡。
    参数：
      value        数值或路径
      grade        good/warn/bad 或优/良/差
      label        标签文本
      grade_text   可选，等级文字（如"良好"）
    """
    if len(args) < 3:
        return ""
    value_raw = resolve_value_token(args[0], data, this_ctx)
    grade_raw = to_text(resolve_value_token(args[1], data, this_ctx)).strip()
    # 特殊处理：如果第二个 token 是 path 但没解析到值，回退为字面量
    if not grade_raw and isinstance(args[1], tuple) and args[1][0] == "path":
        grade_raw = args[1][1]
    grade_raw_l = grade_raw.lower()
    # 归一化 grade
    grade_map = {
        "good": "good", "优": "good", "高": "good", "green": "good", "g": "good",
        "warn": "warn", "良": "warn", "中": "warn", "yellow": "warn", "w": "warn",
        "bad": "bad", "差": "bad", "低": "bad", "red": "bad", "b": "bad",
    }
    grade = grade_map.get(grade_raw_l, "warn")

    # 标签与等级文字
    label = to_text(resolve_value_token(args[2], data, this_ctx)).strip()
    if not label and isinstance(args[2], tuple) and args[2][0] == "path":
        label = args[2][1]
    grade_text = ""
    if len(args) >= 4:
        grade_text = to_text(resolve_value_token(args[3], data, this_ctx)).strip()
        if not grade_text and isinstance(args[3], tuple) and args[3][0] == "path":
            grade_text = args[3][1]

    if not grade_text:
        grade_text = GRADE_TEXT[grade]

    # 数值
    try:
        if isinstance(value_raw, (int, float)):
            val_text = f"{float(value_raw):.1f}"
        else:
            val_text = to_text(value_raw)
    except (TypeError, ValueError):
        val_text = to_text(value_raw)

    return (f'<div class="kpi-card grade-{grade}">'
            f'<div class="kpi-value">{html_escape(val_text)}</div>'
            f'<div class="kpi-label">{html_escape(label)}</div>'
            f'<div class="kpi-grade">{html_escape(grade_text)}</div>'
            f'</div>')


def render_kpi_path(args, data, this_ctx):
    """
    {{_kpi_path path index}} 从数据按路径取第 N 个 KPI 渲染。
    path    指向列表的路径
    index   元素下标（默认 0）
    """
    if not args:
        return ""
    path_token = args[0]
    try:
        idx = int(args[1][1]) if len(args) > 1 else 0
    except (IndexError, ValueError, TypeError):
        idx = 0
    lst = resolve_value_token(path_token, data, this_ctx)
    if not isinstance(lst, list) or idx >= len(lst) or idx < 0:
        return ""
    item = lst[idx]
    if not isinstance(item, dict):
        return ""
    value = item.get("value", item.get("score", 0))
    grade = item.get("grade", "warn")
    label = item.get("label", item.get("name", ""))
    grade_text = item.get("grade_text", "")
    # 重新走 render_kpi
    return render_kpi(
        [("literal", value), ("literal", grade), ("literal", label),
         ("literal", grade_text) if grade_text else ("literal", "")],
        data, this_ctx)


def resolve_value_token(token, data, this_ctx):
    """解析单个 token：字面量直接返回，路径则从 data/this 取值。"""
    if isinstance(token, tuple):
        kind, val = token
        if kind == "literal":
            return val
        # 路径
        return resolve_path(val, data, this_ctx)
    if isinstance(token, str):
        return resolve_path(token, data, this_ctx)
    return token


# ============================================================================
# 模板引擎核心
# ============================================================================

class TemplateEngine:
    """
    轻量模板引擎。
    支持：
      {{path.to.var}}                  变量
      {{#each path}}...{{/each}}       循环
      {{foreach path}}...{{/foreach}}  循环（别名）
      {{#if expr}}...{{/if}}           条件
      {{#ifnot expr}}...{{/ifnot}}     反向条件
      {{_xxx args}}                    辅助指令（自闭合或成对）
    """

    # 块指令
    BLOCK_OPEN_RE = re.compile(
        r"\{\{\s*[#_]?(?P<tag>(?:each|foreach|if|ifnot|_?callout|_?checklist))"
        r"\s+(?P<expr>[^{}]*?)\s*\}\}",
        re.DOTALL,
    )
    # 块指令结束：支持 {{/tag}} / {{/tag}} / {{_/tag}} / {{/_tag}} 等多种写法
    BLOCK_CLOSE_RE = re.compile(
        r"\{\{\s*[_/]*?(?P<tag>(?:each|foreach|if|ifnot|callout|checklist))\s*\}\}",
        re.DOTALL,
    )
    # 自闭合辅助指令
    HELPER_SELF_RE = re.compile(
        r"\{\{\s*_(?P<name>tag|bool|score|kpi|kpi_path|checklist)\b"
        r"\s*(?P<args>[^{}]*?)\s*\}\}",
        re.DOTALL,
    )
    # 变量：{{path.to.var}}，但跳过 {{@meta}} 与 {{#block}} 与 {{_helper}}
    VAR_RE = re.compile(
        r"\{\{\s*(?P<expr>(?![@#_])[^{}]+?)\s*\}\}",
        re.DOTALL,
    )

    def __init__(self, template_str, data):
        self.template = template_str
        self.data = data or {}
        # 预处理：把 foreach 与 #each 统一为 each
        self.template = re.sub(
            r"\{\{\s*foreach\b", "{{#each", self.template
        )

    def render(self):
        return self._render(self.template, self.data, this_ctx=None)

    # ---------- 主渲染 ----------
    def _render(self, tpl, data, this_ctx):
        # 1) 块指令
        tpl = self._render_blocks(tpl, data, this_ctx)
        # 2) 自闭合辅助指令
        tpl = self._render_helpers(tpl, data, this_ctx)
        # 3) 变量
        tpl = self._render_vars(tpl, data, this_ctx)
        return tpl

    # ---------- 块指令处理 ----------
    def _render_blocks(self, tpl, data, this_ctx):
        # 反复扫描直到没有可处理的块
        while True:
            m_open = self.BLOCK_OPEN_RE.search(tpl)
            if not m_open:
                return tpl
            tag = m_open.group("tag")            # 形如 #each / #if / _callout
            expr = m_open.group("expr").strip()
            # 找匹配的结束标签：支持 {{/tag}} 与 {{_/tag}}
            base = tag.lstrip("#_")             # each / if / ifnot / callout / checklist
            # 扫描整段文本，匹配所有开/闭标签，按出现顺序维护栈
            open_re = self.BLOCK_OPEN_RE
            # 闭标签：{{可选_/}} + tag
            close_re = re.compile(
                r"\{\{\s*[_/]*?" + re.escape(base) + r"\s*\}\}",
                re.DOTALL,
            )
            start = m_open.end()
            close_match = None
            depth = 1
            pos = start
            while True:
                m_o = open_re.search(tpl, pos)
                m_c = close_re.search(tpl, pos)
                if not m_c:
                    break
                if m_o and m_o.start() < m_c.start():
                    depth += 1
                    pos = m_o.end()
                else:
                    depth -= 1
                    if depth == 0:
                        close_match = m_c
                        break
                    pos = m_c.end()
            if not close_match:
                # 找不到闭合，原样返回避免死循环
                return tpl
            inner = tpl[start:close_match.start()]
            replaced = self._dispatch_block(tag, expr, inner, data, this_ctx)
            tpl = tpl[:m_open.start()] + replaced + tpl[close_match.end():]
        # end while

    def _dispatch_block(self, tag, expr, inner, data, this_ctx):
        # tag 可能带前缀：#each / #if / _callout / callout / #checklist
        base = tag.lstrip("#_")
        if base == "each":
            return self._render_each(expr, inner, data, this_ctx)
        if base == "if":
            cond = eval_condition(expr, data, this_ctx)
            return self._render(inner, data, this_ctx) if cond else ""
        if base == "ifnot":
            cond = eval_condition(expr, data, this_ctx)
            return "" if cond else self._render(inner, data, this_ctx)
        if base == "callout":
            # 解析参数：第一个是类型（字面量或路径）
            args = resolve_helper_args(expr, data, this_ctx)
            type_token = args[0] if args else ("literal", "info")
            return render_callout(type_token, self._render(inner, data, this_ctx),
                                  data, this_ctx)
        if base == "checklist":
            return render_checklist(expr, inner, data, this_ctx)
        return inner

    def _render_each(self, expr, inner, data, this_ctx):
        # 解析参数：支持 "path" 或 "path as alias"
        parts = expr.split()
        path = parts[0] if parts else expr
        alias = None
        if len(parts) >= 3 and parts[1] == "as":
            alias = parts[2]
        seq = resolve_path(path, data, this_ctx)
        if not isinstance(seq, list):
            return ""
        out = []
        total = len(seq)
        for i, item in enumerate(seq):
            ctx_item = item
            # 渲染内部
            inner_data = data
            # 提供 @index/@first/@last 上下文
            meta = {
                "@index": i,
                "@first": (i == 0),
                "@last": (i == total - 1),
                "@total": total,
            }
            rendered = self._render_with_meta(inner, data, ctx_item, meta)
            out.append(rendered)
        return "".join(out)

    def _render_with_meta(self, inner, data, this_ctx, meta):
        """在 this 上下文中，额外支持 @index/@first/@last 变量。"""
        # 先处理块
        tpl = self._render_blocks(inner, data, this_ctx)
        # 自闭合辅助
        tpl = self._render_helpers(tpl, data, this_ctx)
        # 变量
        tpl = self._render_vars(tpl, data, this_ctx)
        # 替换 @index 等
        def _meta_sub(m):
            key = m.group(1)
            if key in meta:
                return to_text(meta[key])
            return m.group(0)
        tpl = re.sub(r"\{\{\s*(@index|@first|@last|@total)\s*\}\}", _meta_sub, tpl)
        return tpl

    # ---------- 自闭合辅助指令 ----------
    def _render_helpers(self, tpl, data, this_ctx):
        def repl(m):
            name = m.group("name")
            arg_str = m.group("args")
            args = resolve_helper_args(arg_str, data, this_ctx)
            if name == "tag":
                if not args:
                    return ""
                return render_tag(args[0], data, this_ctx)
            if name == "bool":
                if not args:
                    return ""
                return render_bool(args[0], data, this_ctx)
            if name == "score":
                if not args:
                    return ""
                return render_score(args[0], data, this_ctx)
            if name == "kpi":
                return render_kpi(args, data, this_ctx)
            if name == "kpi_path":
                return render_kpi_path(args, data, this_ctx)
            if name == "checklist":
                if not args:
                    return ""
                return render_checklist(args[0], "", data, this_ctx)
            return ""
        return self.HELPER_SELF_RE.sub(repl, tpl)

    # ---------- 变量 ----------
    def _render_vars(self, tpl, data, this_ctx):
        def repl(m):
            expr = m.group("expr").strip()
            if not expr:
                return ""
            # this.x 在 foreach 内已由 _render_with_meta 处理
            val = resolve_path(expr, data, this_ctx)
            return html_escape(val)
        return self.VAR_RE.sub(repl, tpl)


# ============================================================================
# 样式注入
# ============================================================================

def inject_default_style(template_str):
    """若模板无 <style> 标签，则在 </head> 之前注入默认样式。"""
    if re.search(r"<style\b", template_str, re.IGNORECASE):
        return template_str
    if "</head>" in template_str.lower():
        return re.sub(r"(?i)(</head>)", DEFAULT_STYLE + r"\1", template_str, count=1)
    # 无 </head>：在 <body 之前注入
    return re.sub(r"(?i)(<body\b)", DEFAULT_STYLE + r"\1", template_str, count=1)


# ============================================================================
# 数据加载与字段映射
# ============================================================================

def load_data(path):
    """加载 JSON 数据。"""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f, object_pairs_hook=OrderedDict)


def load_template(path):
    """加载模板。"""
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def write_text(path, content):
    """写文件，确保目录存在。"""
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def write_csv(path, fieldnames, rows):
    """写 CSV 文件。"""
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            writer.writerow(r)


# ---------------------------------------------------------------------------
# test-questions.csv
# ---------------------------------------------------------------------------

QUESTION_FIELDS = {
    "id":       ["id", "number", "qid", "编号"],
    "type":     ["type", "category", "问题类型", "类型"],
    "text":     ["text", "question", "问题", "问题文本"],
    "keyword":  ["keyword", "target", "target_keyword", "目标关键词"],
    "priority": ["priority", "优先级"],
}


def build_questions_rows(data):
    """从 data.questions / data.test_questions / data.items 取问题列表。"""
    candidates = ["questions", "test_questions", "items", "问题列表"]
    items = None
    for c in candidates:
        v = safe_get(data, c, None)
        if isinstance(v, list):
            items = v
            break
    if items is None:
        # 回退：可能 data 本身就是列表（不太可能）
        items = []
    rows = []
    for i, it in enumerate(items, 1):
        if not isinstance(it, dict):
            rows.append({
                "id": i,
                "type": "",
                "text": to_text(it),
                "keyword": "",
                "priority": "",
            })
            continue
        row = {
            "id":       pick_first(it, QUESTION_FIELDS["id"], i),
            "type":     pick_first(it, QUESTION_FIELDS["type"], ""),
            "text":     pick_first(it, QUESTION_FIELDS["text"], ""),
            "keyword":  pick_first(it, QUESTION_FIELDS["keyword"], ""),
            "priority": pick_first(it, QUESTION_FIELDS["priority"], ""),
        }
        rows.append(row)
    return rows


# ---------------------------------------------------------------------------
# test-results.csv
# ---------------------------------------------------------------------------

RESULT_FIELDS = {
    "id":          ["id", "qid", "编号"],
    "question":    ["question", "text", "问题", "问题文本"],
    "platform":    ["platform", "平台"],
    "endpoint":    ["endpoint", "device", "type", "端类型", "设备"],
    "mentioned":   ["mentioned", "是否提到品牌", "mentioned_brand"],
    "rank":        ["rank", "品牌排第几位", "brand_rank"],
    "sentiment":   ["sentiment", "情感倾向", "情感"],
    "description": ["description", "key_points", "summary", "AI描述要点",
                    "要点", "描述"],
    "accuracy":    ["accuracy", "accurate", "信息是否准确", "准确"],
    "source_url":  ["source_url", "url", "引用来源URL", "source", "来源"],
}


def to_yes_no(value):
    """布尔/字符串转 是/否。"""
    if isinstance(value, bool):
        return "是" if value else "否"
    if value is None:
        return ""
    s = to_text(value).strip().lower()
    if s in ("true", "yes", "y", "1", "是", "有", "提及"):
        return "是"
    if s in ("false", "no", "n", "0", "否", "无", "未提及"):
        return "否"
    return to_text(value)


def build_results_rows(data):
    """从 data.results / data.test_results 取结果列表。"""
    candidates = ["results", "test_results", "测试结果", "answers"]
    items = None
    for c in candidates:
        v = safe_get(data, c, None)
        if isinstance(v, list):
            items = v
            break
    if items is None:
        items = []
    rows = []
    for i, it in enumerate(items, 1):
        if not isinstance(it, dict):
            continue
        row = {
            "id":          pick_first(it, RESULT_FIELDS["id"], i),
            "question":    pick_first(it, RESULT_FIELDS["question"], ""),
            "platform":    pick_first(it, RESULT_FIELDS["platform"], ""),
            "endpoint":    pick_first(it, RESULT_FIELDS["endpoint"], ""),
            "mentioned":   to_yes_no(pick_first(it, RESULT_FIELDS["mentioned"], "")),
            "rank":        pick_first(it, RESULT_FIELDS["rank"], ""),
            "sentiment":   pick_first(it, RESULT_FIELDS["sentiment"], ""),
            "description": pick_first(it, RESULT_FIELDS["description"], ""),
            "accuracy":    pick_first(it, RESULT_FIELDS["accuracy"], ""),
            "source_url":  pick_first(it, RESULT_FIELDS["source_url"], ""),
        }
        rows.append(row)
    return rows


# ---------------------------------------------------------------------------
# blind-keywords.txt
# ---------------------------------------------------------------------------

def normalize_priority(p):
    """归一化优先级。"""
    s = to_text(p).strip().upper()
    if s in ("P0",):
        return "P0"
    if s in ("P1",):
        return "P1"
    if s in ("P2",):
        return "P2"
    if s in ("HIGH", "高"):
        return "P0"
    if s in ("MEDIUM", "中"):
        return "P1"
    if s in ("LOW", "低"):
        return "P2"
    return s or "P1"


# 等级到细分类的映射
PRIORITY_DETAIL_MAP = {
    "P0": ["完全盲区", "严重盲区"],
    "P1": ["部分盲区", "边缘盲区"],
    "P2": ["次要盲区"],
}


def build_blind_keywords(data):
    """
    构建盲区词列表。
    优先取 data.blind_keywords / data.盲区词 / data.gap_keywords。
    每项结构建议：{"keyword": "...", "priority": "P0/P1/P2", "detail": "完全盲区/严重盲区/..."}
    """
    candidates = ["blind_keywords", "blindWords", "gap_keywords", "盲区词", "keywords_blind"]
    items = None
    for c in candidates:
        v = safe_get(data, c, None)
        if isinstance(v, list):
            items = v
            break
    if items is None:
        items = []

    # 归类
    buckets = OrderedDict()
    for cat in ["完全盲区", "严重盲区", "部分盲区", "边缘盲区", "次要盲区"]:
        buckets[cat] = []
    # 等级桶
    level_buckets = {"P0": [], "P1": [], "P2": []}
    for it in items:
        if isinstance(it, str):
            # 纯字符串：当 P1 处理
            level_buckets["P1"].append({"keyword": it, "priority": "P1", "detail": "边缘盲区"})
            continue
        if not isinstance(it, dict):
            continue
        kw = (it.get("keyword") or it.get("word") or it.get("term") or
              it.get("name") or it.get("关键词") or "")
        pri = normalize_priority(it.get("priority") or it.get("level") or it.get("优先级") or "P1")
        detail = (it.get("detail") or it.get("category") or it.get("type") or "").strip()
        if not detail:
            # 缺省按 priority 推断
            if pri == "P0":
                detail = "完全盲区"
            elif pri == "P1":
                detail = "边缘盲区"
            else:
                detail = "次要盲区"
        if not kw:
            continue
        if detail not in buckets:
            buckets[detail] = []
        buckets[detail].append(kw)
        level_buckets.setdefault(pri, []).append({"keyword": kw, "priority": pri, "detail": detail})
    return buckets, level_buckets


def render_blind_keywords_text(brand, date, buckets, level_buckets):
    """渲染盲区词 TXT 文本。"""
    total = sum(len(v) for v in level_buckets.values())
    lines = []
    lines.append(f"# 盲区词列表 — {brand} — {date}")
    lines.append(f"# 总计: {total} 个盲区词")
    lines.append("")

    # 按要求的顺序输出
    order = [
        ("[P0 - 完全盲区]", "完全盲区", "P0"),
        ("[P0 - 严重盲区]", "严重盲区", "P0"),
        ("[P1 - 部分盲区]", "部分盲区", "P1"),
        ("[P1 - 边缘盲区]", "边缘盲区", "P1"),
        ("[P2 - 次要盲区]", "次要盲区", "P2"),
    ]
    for header, detail, prio in order:
        words = buckets.get(detail, [])
        # 过滤：同 detail 才输出
        words = [w for w in words]
        if not words:
            continue
        lines.append(header)
        for w in words:
            lines.append(to_text(w).strip())
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


# ============================================================================
# 主流程
# ============================================================================

def render_html(data, template_str):
    """渲染模板。"""
    template_str = inject_default_style(template_str)
    engine = TemplateEngine(template_str, data)
    return engine.render()


def run_mode_legacy(data, template_str, output_html):
    """v1.0 兼容模式：单文件输出。"""
    html_out = render_html(data, template_str)
    write_text(output_html, html_out)
    print(f"[OK] 渲染完成：{output_html}", file=sys.stderr)


def run_mode_batch(data, template_str, output_dir, brand, date):
    """v1.1 新增模式：4 文件输出。"""
    # 1) HTML 报告
    html_out = render_html(data, template_str)
    brand_slug = re.sub(r"[^\w\-]+", "-", brand).strip("-") or "brand"
    html_name = f"diagnosis-report-{brand_slug}-v1-{date}.html"
    html_path = os.path.join(output_dir, html_name)
    write_text(html_path, html_out)

    # 2) test-questions.csv
    q_rows = build_questions_rows(data)
    q_path = os.path.join(output_dir, f"test-questions-{date}.csv")
    write_csv(q_path, ["id", "type", "text", "keyword", "priority"], q_rows)

    # 3) test-results.csv
    r_rows = build_results_rows(data)
    r_path = os.path.join(output_dir, f"test-results-{date}.csv")
    write_csv(r_path,
              ["id", "question", "platform", "endpoint", "mentioned",
               "rank", "sentiment", "description", "accuracy", "source_url"],
              r_rows)

    # 4) blind-keywords.txt
    buckets, level_buckets = build_blind_keywords(data)
    txt_content = render_blind_keywords_text(brand, date, buckets, level_buckets)
    txt_path = os.path.join(output_dir, f"blind-keywords-{date}.txt")
    write_text(txt_path, txt_content)

    print(f"[OK] HTML : {html_path}", file=sys.stderr)
    print(f"[OK] Q-CSV: {q_path} ({len(q_rows)} 行)", file=sys.stderr)
    print(f"[OK] R-CSV: {r_path} ({len(r_rows)} 行)", file=sys.stderr)
    print(f"[OK] TXT  : {txt_path}", file=sys.stderr)


def parse_args(argv=None):
    """解析命令行参数。"""
    parser = argparse.ArgumentParser(
        prog="render_report",
        description="GEO 诊断报告渲染脚本 v1.1（双模式 + 模板引擎）",
    )
    parser.add_argument("--data", required=True, help="输入 JSON 数据文件")
    parser.add_argument("--template", required=True, help="HTML 模板文件")
    parser.add_argument("--output", help="v1.0 模式：输出 HTML 路径")
    parser.add_argument("--output-dir", help="v1.1 模式：输出目录（4 个文件）")
    parser.add_argument("--brand", help="v1.1 模式：品牌名（用于文件名与 TXT 标题）")
    parser.add_argument("--date", help="v1.1 模式：日期（用于文件名，默认今天）")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)

    # 校验模式
    if not args.output and not args.output_dir:
        print("[ERR] 必须指定 --output 或 --output-dir", file=sys.stderr)
        return 2

    # 加载
    try:
        data = load_data(args.data)
    except Exception as e:
        print(f"[ERR] 读取数据失败: {e}", file=sys.stderr)
        return 2
    try:
        template_str = load_template(args.template)
    except Exception as e:
        print(f"[ERR] 读取模板失败: {e}", file=sys.stderr)
        return 2

    # 分派
    if args.output:
        run_mode_legacy(data, template_str, args.output)
        return 0
    if args.output_dir:
        brand = args.brand or safe_get(data, "meta.brand", "") or safe_get(data, "brand", "brand")
        date = args.date or datetime.date.today().isoformat()
        run_mode_batch(data, template_str, args.output_dir, brand, date)
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
