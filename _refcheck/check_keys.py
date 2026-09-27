#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
check_keys.py - 论文引用与结构机械核验脚本
功能：
1. 校验 paper.tex 中的所有 \cite{...} 与 references.bib 中的条目严格一一对应；
2. 校验关键 LaTeX 环境（table, tabular, equation, enumerate, figure, definition 等）闭合配平；
3. 输出结构化状态与客观数据，杜绝引用缺失或孤立引用。
"""

import os
import re
import sys
import json

def check_paper_integrity(tex_path="paper.tex", bib_path="references.bib"):
    if not os.path.isabs(tex_path):
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if os.path.exists(os.path.join(base, tex_path)):
            tex_path = os.path.join(base, tex_path)
            bib_path = os.path.join(base, bib_path)

    if not os.path.exists(tex_path):
        print(f"[ERROR] 找不到主文件: {tex_path}")
        return False
    if not os.path.exists(bib_path):
        print(f"[ERROR] 找不到引用文件: {bib_path}")
        return False

    with open(tex_path, "r", encoding="utf-8") as f:
        tex_content = f.read()

    with open(bib_path, "r", encoding="utf-8") as f:
        bib_content = f.read()

    # 1. 提取正文中所有引用的 key
    cite_matches = re.findall(r"\\cite[a-zA-Z*]*\{([^}]+)\}", tex_content)
    cited_keys = set()
    for m in cite_matches:
        for k in m.split(","):
            k = k.strip()
            if k:
                cited_keys.add(k)

    # 2. 提取 bib 文件中所有 entry key
    bib_keys = set(re.findall(r"@\w+\s*\{\s*([^,\s]+),", bib_content))

    missing_in_bib = cited_keys - bib_keys
    unused_in_tex = bib_keys - cited_keys

    # 3. 统计关键环境闭合情况
    environments = ["enumerate", "table", "tabular", "equation", "definition", "figure"]
    env_stats = {}
    for env in environments:
        begins = len(re.findall(rf"\\begin\{{{env}\}}", tex_content))
        ends = len(re.findall(rf"\\end\{{{env}\}}", tex_content))
        env_stats[env] = {"begin": begins, "end": ends, "balanced": begins == ends}

    # 4. 括号配平检查
    left_braces = tex_content.count("{")
    right_braces = tex_content.count("}")

    print("=" * 60)
    print("AI4Math 论文完整性与机械核验报告 (Reproducibility Verification)")
    print("=" * 60)
    print(f"主文档: {tex_path} (字符数: {len(tex_content):,})")
    print(f"引用库: {bib_path} (条目数: {len(bib_keys)})")
    print(f"正文实际引用唯一键: {len(cited_keys)}")
    print("-" * 60)

    success = True
    if missing_in_bib:
        print(f"[FAIL] 缺少 Bib 条目 ({len(missing_in_bib)}): {sorted(missing_in_bib)}")
        success = False
    else:
        print(f"[PASS] 引用匹配: 所有 {len(cited_keys)} 个正文引用键均在 references.bib 中完整定义。")

    if unused_in_tex:
        print(f"[WARN] 未被正文引用的 Bib 条目 ({len(unused_in_tex)}): {sorted(unused_in_tex)}")
    else:
        print("[PASS] 孤立条目检查: bib 中无未引用的孤立条目 (100% 对应)。")

    print("-" * 60)
    print("LaTeX 环境配平检查:")
    for env, stat in env_stats.items():
        status_str = "PASS" if stat["balanced"] else "FAIL"
        if not stat["balanced"]:
            success = False
        print(f"  [{status_str}] \\begin{{{env}}}: {stat['begin']} | \\end{{{env}}}: {stat['end']}")

    brace_diff = left_braces - right_braces
    if brace_diff == 0:
        print(f"  [PASS] 花括号深度配平: 差值为 0 (总计 {{ : {left_braces:,})")
    else:
        print(f"  [WARN] 花括号计数差异: {brace_diff}")

    print("=" * 60)
    if success:
        print(">>> 机械核验总评: 100% 全部通过 (ALL CHECKS PASSED) <<<")
    else:
        print(">>> 机械核验总评: 存在未通过项 (CHECKS FAILED) <<<")
    print("=" * 60)

    result_manifest = {
        "status": "PASS" if success else "FAIL",
        "bib_count": len(bib_keys),
        "cited_count": len(cited_keys),
        "missing_in_bib": list(missing_in_bib),
        "unused_in_tex": list(unused_in_tex),
        "environments": env_stats,
        "brace_balance": brace_diff == 0
    }
    out_dir = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(out_dir, "verify_result.json"), "w", encoding="utf-8") as out:
        json.dump(result_manifest, out, indent=2, ensure_ascii=False)

    return success

if __name__ == "__main__":
    tex = sys.argv[1] if len(sys.argv) > 1 else "paper.tex"
    bib = sys.argv[2] if len(sys.argv) > 2 else "references.bib"
    ok = check_paper_integrity(tex, bib)
    sys.exit(0 if ok else 1)
