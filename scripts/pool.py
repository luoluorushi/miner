#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Stock Pool Query Tool
股票池查询工具 - 从AI股票池获取指定范围的股票

Usage:
    python pool.py list --start 0 --end 10      # 获取第0-9只
    python pool.py list --start 10 --end 20     # 获取第10-19只
    python pool.py progress                      # 查看当前进度
    python pool.py set-progress 10               # 设置下一个待评估序号
"""

import json
import argparse
import sys
import io
from pathlib import Path

# Fix Windows encoding issue
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Paths
POOL_PATH = Path(__file__).parent.parent.parent / "stock-data" / "ai_stock_pool_v2.json"
PROGRESS_PATH = Path(__file__).parent.parent / "database" / "batch_progress.txt"


def load_pool():
    """Load stock pool and flatten to a list"""
    with open(POOL_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    stocks = []
    categories = data.get('categories', {})
    
    for cat_key, cat_data in categories.items():
        cat_name = cat_data.get('name', cat_key)
        sectors = cat_data.get('sectors', {})
        
        for sector_key, sector_data in sectors.items():
            sector_name = sector_data.get('name', sector_key)
            stock_lists = sector_data.get('stocks', {})
            
            # A shares
            for stock in stock_lists.get('a_shares', []):
                stocks.append({
                    'code': stock['code'],
                    'name': stock['name'],
                    'category': cat_name,
                    'sector': sector_name,
                    'market': 'A股'
                })
            
            # HK shares
            for stock in stock_lists.get('hk_shares', []):
                stocks.append({
                    'code': stock['code'],
                    'name': stock['name'],
                    'category': cat_name,
                    'sector': sector_name,
                    'market': '港股'
                })
            
            # US shares
            for stock in stock_lists.get('us_shares', []):
                stocks.append({
                    'code': stock['code'],
                    'name': stock['name'],
                    'category': cat_name,
                    'sector': sector_name,
                    'market': '美股'
                })
    
    return stocks


def get_progress():
    """Get current progress"""
    if PROGRESS_PATH.exists():
        with open(PROGRESS_PATH, 'r', encoding='utf-8') as f:
            return int(f.read().strip())
    return 0


def set_progress(index):
    """Set progress"""
    PROGRESS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(PROGRESS_PATH, 'w', encoding='utf-8') as f:
        f.write(str(index))


def cmd_list(args):
    """List stocks in range [start, end)"""
    stocks = load_pool()
    total = len(stocks)
    
    start = args.start
    end = min(args.end, total)
    
    if start >= total:
        print(f"起始序号 {start} 超出范围，股票池共 {total} 只")
        return
    
    print(f"股票池共 {total} 只，显示第 {start}-{end-1} 只:\n")
    print(f"{'序号':<6} {'代码':<12} {'名称':<12} {'板块':<12} {'市场':<6}")
    print("-" * 60)
    
    for i in range(start, end):
        s = stocks[i]
        print(f"{i:<6} {s['code']:<12} {s['name']:<12} {s['sector']:<12} {s['market']:<6}")
    
    print(f"\n共显示 {end - start} 只")


def cmd_progress(args):
    """Show current progress"""
    stocks = load_pool()
    total = len(stocks)
    current = get_progress()
    
    print(f"股票池总数: {total}")
    print(f"下一个待评估序号: {current}")
    print(f"已完成: {current}/{total} ({current*100/total:.1f}%)")
    
    if current < total:
        s = stocks[current]
        print(f"\n下一只待评估: {s['code']} {s['name']} ({s['sector']})")


def cmd_set_progress(args):
    """Set progress"""
    set_progress(args.index)
    print(f"已设置下一个待评估序号: {args.index}")
    
    stocks = load_pool()
    if args.index < len(stocks):
        s = stocks[args.index]
        print(f"下一只待评估: {s['code']} {s['name']} ({s['sector']})")


def main():
    parser = argparse.ArgumentParser(description='Stock Pool Query Tool')
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # list command
    list_parser = subparsers.add_parser('list', help='List stocks in range')
    list_parser.add_argument('--start', '-s', type=int, default=0, help='Start index (inclusive)')
    list_parser.add_argument('--end', '-e', type=int, default=10, help='End index (exclusive)')
    
    # progress command
    subparsers.add_parser('progress', help='Show current progress')
    
    # set-progress command
    set_parser = subparsers.add_parser('set-progress', help='Set progress index')
    set_parser.add_argument('index', type=int, help='Next index to evaluate')
    
    args = parser.parse_args()
    
    if args.command == 'list':
        cmd_list(args)
    elif args.command == 'progress':
        cmd_progress(args)
    elif args.command == 'set-progress':
        cmd_set_progress(args)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
