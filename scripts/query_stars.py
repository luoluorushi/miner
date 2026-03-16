#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
查询股票评级数据库

用法:
    python query_stars.py              # 查询所有五星股票
    python query_stars.py --stars 4    # 查询四星及以上股票
    python query_stars.py --stars 3    # 查询三星及以上股票
    python query_stars.py --sector 光通信  # 按板块筛选
    python query_stars.py --top 10     # 显示前10名
    python query_stars.py --brief      # 简洁模式（不显示详情）
"""
import json
import os
import sys
import io
import argparse

# 修复Windows控制台编码问题
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

def count_stars(rating_str):
    """计算星级字符串中的星星数量"""
    if not rating_str:
        return 0
    return rating_str.count('⭐')

def main():
    parser = argparse.ArgumentParser(description='查询股票评级数据库')
    parser.add_argument('--stars', type=int, default=5, help='最低星级 (1-5)，默认5')
    parser.add_argument('--sector', type=str, default=None, help='按板块筛选')
    parser.add_argument('--top', type=int, default=None, help='显示前N名')
    parser.add_argument('--brief', action='store_true', help='简洁模式')
    args = parser.parse_args()

    # 加载数据库
    db_path = os.path.join(os.path.dirname(__file__), '..', 'database', 'stock_ratings.json')
    with open(db_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 筛选股票
    # 重要: ai_rating 是字符串如 "⭐⭐⭐⭐⭐"，不是数字
    filtered = [s for s in data['stocks'] if count_stars(s.get('ai_rating', '')) >= args.stars]
    
    # 按板块筛选
    if args.sector:
        filtered = [s for s in filtered if args.sector in s.get('sector', '')]
    
    # 按总分排序
    filtered = sorted(filtered, key=lambda x: -x.get('ai_total_score', 0))
    
    # 限制数量
    if args.top:
        filtered = filtered[:args.top]

    # 输出标题
    star_display = '⭐' * args.stars
    sector_info = f" [{args.sector}]" if args.sector else ""
    print(f"\n{star_display} {args.stars}星及以上股票{sector_info} 共 {len(filtered)} 只\n")
    
    if not filtered:
        print("未找到符合条件的股票")
        return
    
    # 表头
    print(f"{'代码':<12} {'名称':<12} {'板块':<12} {'总分':>6} {'AI敞口':>6} {'护城河':>6} {'需求':>6} {'财务':>6} {'估值':>6} {'催化':>6}")
    print("-" * 100)

    # 列表
    for s in filtered:
        d = s.get('dimensions', {})
        print(f"{s.get('stock_code',''):<12} {s.get('stock_name',''):<12} {s.get('sector',''):<12} {s.get('ai_total_score',0):>6.2f} "
              f"{d.get('ai_exposure',{}).get('score','-'):>6} {d.get('moat',{}).get('score','-'):>6} "
              f"{d.get('demand_growth',{}).get('score','-'):>6} {d.get('financial_quality',{}).get('score','-'):>6} "
              f"{d.get('valuation',{}).get('score','-'):>6} {d.get('catalyst_risk',{}).get('score','-'):>6}")

    # 简洁模式则跳过详情
    if args.brief:
        return

    # 详细展示
    print("\n" + "=" * 100)
    print("详细信息:")
    print("=" * 100)

    for s in filtered:
        print(f"\n【{s.get('stock_name','')}】 {s.get('stock_code','')} - {s.get('sector','')}")
        print(f"  AI评分: {s.get('ai_rating','')} ({s.get('ai_total_score',0):.2f}分)")
        
        # AI摘要
        if s.get('ai_summary'):
            print(f"  摘要: {s.get('ai_summary','')}")
        
        # 投资论点
        if s.get('ai_investment_thesis'):
            thesis = s.get('ai_investment_thesis','')
            if len(thesis) > 150:
                thesis = thesis[:150] + "..."
            print(f"  投资要点: {thesis}")
        
        # 各维度评分明细
        d = s.get('dimensions', {})
        print(f"  评分明细:")
        for dim_name, dim_label in [
            ('ai_exposure', 'AI敞口'),
            ('moat', '护城河'),
            ('demand_growth', '需求增长'),
            ('financial_quality', '财务质量'),
            ('valuation', '估值'),
            ('catalyst_risk', '催化/风险')
        ]:
            dim = d.get(dim_name, {})
            if dim:
                evidence = dim.get('evidence', '')
                if len(str(evidence)) > 80:
                    evidence = str(evidence)[:80] + "..."
                print(f"    - {dim_label}: {dim.get('score','-')}分 | {evidence}")
        
        print("-" * 100)

if __name__ == '__main__':
    main()
