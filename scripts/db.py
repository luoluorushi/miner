#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gold Miner Database CLI Tool
股票评级数据库命令行工具

Usage:
    python db.py list [--top N] [--sort ai|user] [--sector SECTOR]
    python db.py get <stock_code>
    python db.py add <stock_code> <stock_name> <sector>
    python db.py update <stock_code> --dimension <dim> --score <score> [--evidence "..."]
    python db.py batch <stock_code> [--ai_exposure 4 "evidence"] [--moat 5 "evidence"] ...
    python db.py rate <stock_code> --stars <1-5> [--notes "..."]
    python db.py pending [--top N]
    python db.py export [--format json|csv]
"""

import json
import argparse
import sys
import io
import time
from datetime import datetime
from pathlib import Path

# Windows file locking
if sys.platform == 'win32':
    import msvcrt
    def lock_file(f):
        """Acquire exclusive lock on file (Windows)"""
        msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
    def unlock_file(f):
        """Release file lock (Windows)"""
        f.seek(0)
        msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
else:
    import fcntl
    def lock_file(f):
        """Acquire exclusive lock on file (Unix)"""
        fcntl.flock(f.fileno(), fcntl.LOCK_EX)
    def unlock_file(f):
        """Release file lock (Unix)"""
        fcntl.flock(f.fileno(), fcntl.LOCK_UN)

# Fix Windows encoding issue
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Database path
DB_PATH = Path(__file__).parent.parent / "database" / "stock_ratings.json"

# Lock file path
LOCK_PATH = DB_PATH.with_suffix('.lock')

# Dimension weights
DIMENSION_WEIGHTS = {
    "ai_exposure": 0.25,
    "moat": 0.20,
    "demand_growth": 0.20,
    "financial_quality": 0.15,
    "mcap_ai_profit_ratio": 0.10,
    "valuation": 0.05,
    "catalyst_risk": 0.05
}

# Rating thresholds
RATING_THRESHOLDS = {
    5: 4.5,  # ⭐⭐⭐⭐⭐
    4: 4.0,  # ⭐⭐⭐⭐
    3: 3.0,  # ⭐⭐⭐
    2: 2.0,  # ⭐⭐
    1: 0.0   # ⭐
}


def load_db():
    """Load database from JSON file"""
    if not DB_PATH.exists():
        return {"metadata": {}, "stocks": []}
    with open(DB_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_db(db):
    """Save database to JSON file"""
    db["metadata"]["updated_at"] = datetime.now().strftime("%Y-%m-%d")
    db["metadata"]["total_stocks"] = len(db["stocks"])
    db["metadata"]["evaluated_stocks"] = sum(1 for s in db["stocks"] if s.get("ai_total_score"))
    db["metadata"]["user_reviewed_stocks"] = sum(1 for s in db["stocks"] if s.get("user_rating"))
    
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(DB_PATH, 'w', encoding='utf-8') as f:
        json.dump(db, f, ensure_ascii=False, indent=2)


def load_db_locked():
    """Load database with file lock (for write operations)"""
    if not DB_PATH.exists():
        return {"metadata": {}, "stocks": []}, None
    
    # Create lock file
    LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
    lock_file_handle = open(LOCK_PATH, 'w')
    
    # Try to acquire lock with retry
    max_retries = 10
    for i in range(max_retries):
        try:
            lock_file(lock_file_handle)
            break
        except (IOError, OSError):
            if i == max_retries - 1:
                lock_file_handle.close()
                raise Exception("Failed to acquire database lock after retries")
            time.sleep(0.1 * (i + 1))  # Exponential backoff
    
    # Read database
    with open(DB_PATH, 'r', encoding='utf-8') as f:
        db = json.load(f)
    
    return db, lock_file_handle


def save_db_locked(db, lock_file_handle):
    """Save database and release file lock"""
    try:
        db["metadata"]["updated_at"] = datetime.now().strftime("%Y-%m-%d")
        db["metadata"]["total_stocks"] = len(db["stocks"])
        db["metadata"]["evaluated_stocks"] = sum(1 for s in db["stocks"] if s.get("ai_total_score"))
        db["metadata"]["user_reviewed_stocks"] = sum(1 for s in db["stocks"] if s.get("user_rating"))
        
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(DB_PATH, 'w', encoding='utf-8') as f:
            json.dump(db, f, ensure_ascii=False, indent=2)
    finally:
        if lock_file_handle:
            try:
                unlock_file(lock_file_handle)
            except:
                pass
            lock_file_handle.close()


def calculate_ai_score(dimensions):
    """Calculate total AI score from dimensions"""
    total = 0.0
    for dim, weight in DIMENSION_WEIGHTS.items():
        if dim in dimensions and "score" in dimensions[dim]:
            total += dimensions[dim]["score"] * weight
    return round(total, 2)


def score_to_rating(score):
    """Convert score to star rating"""
    if score >= 4.5:
        return "⭐⭐⭐⭐⭐"
    elif score >= 4.0:
        return "⭐⭐⭐⭐"
    elif score >= 3.0:
        return "⭐⭐⭐"
    elif score >= 2.0:
        return "⭐⭐"
    else:
        return "⭐"


def cmd_list(args):
    """List stocks with optional filtering and sorting"""
    db = load_db()
    stocks = db.get("stocks", [])
    
    # Filter by sector
    if args.sector:
        stocks = [s for s in stocks if args.sector.lower() in s.get("sector", "").lower()]
    
    # Sort
    if args.sort == "user":
        stocks.sort(key=lambda x: (x.get("user_rating") or 0, x.get("ai_total_score") or 0), reverse=True)
    else:  # default: ai
        stocks.sort(key=lambda x: x.get("ai_total_score") or 0, reverse=True)
    
    # Limit
    if args.top:
        stocks = stocks[:args.top]
    
    # Output
    print(f"{'#':<3} {'代码':<10} {'名称':<12} {'板块':<10} {'AI评分':<8} {'AI评级':<12} {'用户评级':<10}")
    print("-" * 75)
    for i, s in enumerate(stocks, 1):
        user_rating = f"⭐×{s.get('user_rating')}" if s.get('user_rating') else "-"
        print(f"{i:<3} {s.get('stock_code', ''):<10} {s.get('stock_name', ''):<12} "
              f"{s.get('sector', ''):<10} {s.get('ai_total_score', '-'):<8} "
              f"{s.get('ai_rating', '-'):<12} {user_rating:<10}")
    
    print(f"\n共 {len(stocks)} 只股票")


def cmd_get(args):
    """Get detailed info for a stock"""
    db = load_db()
    stock = None
    for s in db.get("stocks", []):
        if s.get("stock_code") == args.stock_code or s.get("stock_name") == args.stock_code:
            stock = s
            break
    
    if not stock:
        print(f"Error: Stock '{args.stock_code}' not found")
        sys.exit(1)
    
    # Output as JSON
    print(json.dumps(stock, ensure_ascii=False, indent=2))


def cmd_add(args):
    """Add a new stock to database"""
    db, lock_handle = load_db_locked()
    
    try:
        # Check if exists
        for s in db.get("stocks", []):
            if s.get("stock_code") == args.stock_code:
                print(f"Error: Stock '{args.stock_code}' already exists")
                sys.exit(1)
        
        # Create new stock entry
        new_stock = {
            "stock_code": args.stock_code,
            "stock_name": args.stock_name,
            "market": "A股",
            "sector": args.sector,
            "dimensions": {},
            "ai_total_score": None,
            "ai_rating": None,
            "ai_summary": None,
            "user_rating": None,
            "user_notes": None,
            "user_reviewed_at": None,
            "created_at": datetime.now().strftime("%Y-%m-%d"),
            "updated_at": datetime.now().strftime("%Y-%m-%d")
        }
        
        if "stocks" not in db:
            db["stocks"] = []
        db["stocks"].append(new_stock)
        save_db_locked(db, lock_handle)
    except Exception as e:
        if lock_handle:
            try:
                unlock_file(lock_handle)
            except:
                pass
            lock_handle.close()
        raise e
    
    print(f"Added: {args.stock_code} {args.stock_name}")


def cmd_update(args):
    """Update a dimension score for a stock"""
    db, lock_handle = load_db_locked()
    
    try:
        # Find stock
        stock = None
        for s in db.get("stocks", []):
            if s.get("stock_code") == args.stock_code or s.get("stock_name") == args.stock_code:
                stock = s
                break
        
        if not stock:
            print(f"Error: Stock '{args.stock_code}' not found")
            sys.exit(1)
        
        # Validate dimension
        if args.dimension not in DIMENSION_WEIGHTS:
            print(f"Error: Invalid dimension '{args.dimension}'")
            print(f"Valid dimensions: {', '.join(DIMENSION_WEIGHTS.keys())}")
            sys.exit(1)
        
        # Validate score
        if not 1 <= args.score <= 5:
            print("Error: Score must be between 1 and 5")
            sys.exit(1)
        
        # Update dimension
        if "dimensions" not in stock:
            stock["dimensions"] = {}
        
        if args.dimension not in stock["dimensions"]:
            stock["dimensions"][args.dimension] = {}
        
        stock["dimensions"][args.dimension]["score"] = args.score
        stock["dimensions"][args.dimension]["updated_at"] = datetime.now().strftime("%Y-%m-%d")
        
        if args.evidence:
            stock["dimensions"][args.dimension]["evidence"] = args.evidence
        
        # Recalculate total score
        stock["ai_total_score"] = calculate_ai_score(stock["dimensions"])
        stock["ai_rating"] = score_to_rating(stock["ai_total_score"])
        stock["updated_at"] = datetime.now().strftime("%Y-%m-%d")
        
        save_db_locked(db, lock_handle)
    except Exception as e:
        if lock_handle:
            try:
                unlock_file(lock_handle)
            except:
                pass
            lock_handle.close()
        raise e
    
    print(f"Updated: {stock['stock_code']} {stock['stock_name']}")
    print(f"  {args.dimension}: {args.score}")
    print(f"  AI Total Score: {stock['ai_total_score']}")
    print(f"  AI Rating: {stock['ai_rating']}")


def cmd_batch(args):
    """Batch update multiple dimensions for a stock in one operation"""
    db, lock_handle = load_db_locked()
    
    try:
        # Find stock
        stock = None
        for s in db.get("stocks", []):
            if s.get("stock_code") == args.stock_code or s.get("stock_name") == args.stock_code:
                stock = s
                break
        
        if not stock:
            print(f"Error: Stock '{args.stock_code}' not found")
            sys.exit(1)
        
        if "dimensions" not in stock:
            stock["dimensions"] = {}
        
        # Process each dimension
        updated_dims = []
        for dim_name in DIMENSION_WEIGHTS.keys():
            dim_value = getattr(args, dim_name, None)
            if dim_value:
                # nargs=2 returns a list: [score_str, evidence]
                score = int(dim_value[0])
                evidence = dim_value[1]
                
                # Validate score
                if not 1 <= score <= 5:
                    print(f"Error: Score for {dim_name} must be between 1 and 5")
                    sys.exit(1)
                
                if dim_name not in stock["dimensions"]:
                    stock["dimensions"][dim_name] = {}
                
                stock["dimensions"][dim_name]["score"] = score
                stock["dimensions"][dim_name]["evidence"] = evidence
                stock["dimensions"][dim_name]["updated_at"] = datetime.now().strftime("%Y-%m-%d")
                updated_dims.append(f"{dim_name}={score}")
        
        if not updated_dims:
            print("Error: No dimensions provided. Use --ai_exposure, --moat, etc.")
            sys.exit(1)
        
        # Recalculate total score
        stock["ai_total_score"] = calculate_ai_score(stock["dimensions"])
        stock["ai_rating"] = score_to_rating(stock["ai_total_score"])
        stock["updated_at"] = datetime.now().strftime("%Y-%m-%d")
        
        save_db_locked(db, lock_handle)
    except Exception as e:
        if lock_handle:
            try:
                unlock_file(lock_handle)
            except:
                pass
            lock_handle.close()
        raise e
    
    print(f"Batch Updated: {stock['stock_code']} {stock['stock_name']}")
    print(f"  Dimensions: {', '.join(updated_dims)}")
    print(f"  AI Total Score: {stock['ai_total_score']}")
    print(f"  AI Rating: {stock['ai_rating']}")


def cmd_update_full(args):
    """Update full stock data from JSON input"""
    db = load_db()
    
    # Read JSON from stdin or file
    if args.file:
        with open(args.file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    else:
        data = json.loads(sys.stdin.read())
    
    stock_code = data.get("stock_code")
    if not stock_code:
        print("Error: stock_code is required")
        sys.exit(1)
    
    # Find or create stock
    stock = None
    for s in db.get("stocks", []):
        if s.get("stock_code") == stock_code:
            stock = s
            break
    
    if not stock:
        stock = {"stock_code": stock_code, "created_at": datetime.now().strftime("%Y-%m-%d")}
        if "stocks" not in db:
            db["stocks"] = []
        db["stocks"].append(stock)
    
    # Update fields
    for key, value in data.items():
        stock[key] = value
    
    # Recalculate total score if dimensions updated
    if "dimensions" in data:
        stock["ai_total_score"] = calculate_ai_score(stock["dimensions"])
        stock["ai_rating"] = score_to_rating(stock["ai_total_score"])
    
    stock["updated_at"] = datetime.now().strftime("%Y-%m-%d")
    
    save_db(db)
    
    print(f"Updated: {stock['stock_code']} {stock.get('stock_name', '')}")
    print(f"  AI Total Score: {stock.get('ai_total_score', '-')}")


def cmd_rate(args):
    """Set user rating for a stock"""
    db, lock_handle = load_db_locked()
    
    try:
        # Find stock
        stock = None
        for s in db.get("stocks", []):
            if s.get("stock_code") == args.stock_code or s.get("stock_name") == args.stock_code:
                stock = s
                break
        
        if not stock:
            print(f"Error: Stock '{args.stock_code}' not found")
            sys.exit(1)
        
        # Validate stars
        if not 1 <= args.stars <= 5:
            print("Error: Stars must be between 1 and 5")
            sys.exit(1)
        
        # Update user rating
        stock["user_rating"] = args.stars
        stock["user_reviewed_at"] = datetime.now().strftime("%Y-%m-%d")
        
        if args.notes:
            stock["user_notes"] = args.notes
        
        stock["updated_at"] = datetime.now().strftime("%Y-%m-%d")
        
        save_db_locked(db, lock_handle)
    except Exception as e:
        if lock_handle:
            try:
                unlock_file(lock_handle)
            except:
                pass
            lock_handle.close()
        raise e
    
    print(f"Rated: {stock['stock_code']} {stock['stock_name']}")
    print(f"  User Rating: {'⭐' * args.stars}")
    if args.notes:
        print(f"  Notes: {args.notes}")


def cmd_pending(args):
    """List stocks pending user review"""
    db = load_db()
    stocks = db.get("stocks", [])
    
    # Filter: has AI score but no user rating
    pending = [s for s in stocks if s.get("ai_total_score") and not s.get("user_rating")]
    
    # Sort by AI score
    pending.sort(key=lambda x: x.get("ai_total_score") or 0, reverse=True)
    
    # Limit
    if args.top:
        pending = pending[:args.top]
    
    # Output
    print(f"{'#':<3} {'代码':<10} {'名称':<12} {'板块':<10} {'AI评分':<8} {'AI评级':<12}")
    print("-" * 65)
    for i, s in enumerate(pending, 1):
        print(f"{i:<3} {s.get('stock_code', ''):<10} {s.get('stock_name', ''):<12} "
              f"{s.get('sector', ''):<10} {s.get('ai_total_score', '-'):<8} "
              f"{s.get('ai_rating', '-'):<12}")
    
    print(f"\n共 {len(pending)} 只待评级股票")


def cmd_export(args):
    """Export database"""
    db = load_db()
    
    if args.format == "csv":
        # CSV export
        print("stock_code,stock_name,sector,ai_total_score,ai_rating,user_rating,user_notes")
        for s in db.get("stocks", []):
            print(f"{s.get('stock_code','')},{s.get('stock_name','')},{s.get('sector','')},"
                  f"{s.get('ai_total_score','')},{s.get('ai_rating','')},{s.get('user_rating','')},\"{s.get('user_notes','')}\"")
    else:
        # JSON export
        print(json.dumps(db, ensure_ascii=False, indent=2))


def cmd_stats(args):
    """Show database statistics"""
    db = load_db()
    stocks = db.get("stocks", [])
    
    total = len(stocks)
    evaluated = sum(1 for s in stocks if s.get("ai_total_score"))
    reviewed = sum(1 for s in stocks if s.get("user_rating"))
    
    # Rating distribution
    rating_dist = {5: 0, 4: 0, 3: 0, 2: 0, 1: 0}
    for s in stocks:
        score = s.get("ai_total_score")
        if score:
            if score >= 4.5:
                rating_dist[5] += 1
            elif score >= 4.0:
                rating_dist[4] += 1
            elif score >= 3.0:
                rating_dist[3] += 1
            elif score >= 2.0:
                rating_dist[2] += 1
            else:
                rating_dist[1] += 1
    
    # Sector distribution
    sectors = {}
    for s in stocks:
        sector = s.get("sector", "未知")
        sectors[sector] = sectors.get(sector, 0) + 1
    
    print("=== 数据库统计 ===")
    print(f"总股票数: {total}")
    print(f"已评估: {evaluated}")
    print(f"用户已评级: {reviewed}")
    print(f"待评级: {evaluated - reviewed}")
    print()
    print("=== AI评级分布 ===")
    print(f"⭐⭐⭐⭐⭐ (金矿股): {rating_dist[5]}")
    print(f"⭐⭐⭐⭐ (优质股): {rating_dist[4]}")
    print(f"⭐⭐⭐ (中等股): {rating_dist[3]}")
    print(f"⭐⭐ (一般股): {rating_dist[2]}")
    print(f"⭐ (低质量): {rating_dist[1]}")
    print()
    print("=== 板块分布 ===")
    for sector, count in sorted(sectors.items(), key=lambda x: x[1], reverse=True):
        print(f"{sector}: {count}")


def main():
    parser = argparse.ArgumentParser(description="Gold Miner Database CLI Tool")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # list command
    list_parser = subparsers.add_parser("list", help="List stocks")
    list_parser.add_argument("--top", type=int, help="Limit to top N")
    list_parser.add_argument("--sort", choices=["ai", "user"], default="ai", help="Sort by")
    list_parser.add_argument("--sector", help="Filter by sector")
    
    # get command
    get_parser = subparsers.add_parser("get", help="Get stock details")
    get_parser.add_argument("stock_code", help="Stock code or name")
    
    # add command
    add_parser = subparsers.add_parser("add", help="Add new stock")
    add_parser.add_argument("stock_code", help="Stock code (e.g., sz300308)")
    add_parser.add_argument("stock_name", help="Stock name")
    add_parser.add_argument("sector", help="Sector name")
    
    # update command
    update_parser = subparsers.add_parser("update", help="Update dimension score")
    update_parser.add_argument("stock_code", help="Stock code or name")
    update_parser.add_argument("--dimension", "-d", required=True, help="Dimension name")
    update_parser.add_argument("--score", "-s", type=int, required=True, help="Score (1-5)")
    update_parser.add_argument("--evidence", "-e", help="Evidence text")
    
    # batch command - update multiple dimensions at once
    batch_parser = subparsers.add_parser("batch", help="Batch update multiple dimensions")
    batch_parser.add_argument("stock_code", help="Stock code or name")
    
    # Use nargs=2 for better shell compatibility: --dim SCORE EVIDENCE
    batch_parser.add_argument("--ai_exposure", nargs=2, metavar=("SCORE", "EVIDENCE"),
                              help="AI exposure: SCORE(1-5) EVIDENCE")
    batch_parser.add_argument("--moat", nargs=2, metavar=("SCORE", "EVIDENCE"),
                              help="Moat: SCORE(1-5) EVIDENCE")
    batch_parser.add_argument("--demand_growth", nargs=2, metavar=("SCORE", "EVIDENCE"),
                              help="Demand growth: SCORE(1-5) EVIDENCE")
    batch_parser.add_argument("--financial_quality", nargs=2, metavar=("SCORE", "EVIDENCE"),
                              help="Financial quality: SCORE(1-5) EVIDENCE")
    batch_parser.add_argument("--valuation", nargs=2, metavar=("SCORE", "EVIDENCE"),
                              help="Valuation: SCORE(1-5) EVIDENCE")
    batch_parser.add_argument("--mcap_ai_profit_ratio", nargs=2, metavar=("SCORE", "EVIDENCE"),
                              help="MCap/AI Profit ratio: SCORE(1-5) EVIDENCE")
    batch_parser.add_argument("--catalyst_risk", nargs=2, metavar=("SCORE", "EVIDENCE"),
                              help="Catalyst/Risk: SCORE(1-5) EVIDENCE")
    
    # update-full command
    update_full_parser = subparsers.add_parser("update-full", help="Update full stock data from JSON")
    update_full_parser.add_argument("--file", "-f", help="JSON file path (or read from stdin)")
    
    # rate command
    rate_parser = subparsers.add_parser("rate", help="Set user rating")
    rate_parser.add_argument("stock_code", help="Stock code or name")
    rate_parser.add_argument("--stars", "-s", type=int, required=True, help="Stars (1-5)")
    rate_parser.add_argument("--notes", "-n", help="User notes")
    
    # pending command
    pending_parser = subparsers.add_parser("pending", help="List pending stocks")
    pending_parser.add_argument("--top", type=int, default=10, help="Limit to top N")
    
    # export command
    export_parser = subparsers.add_parser("export", help="Export database")
    export_parser.add_argument("--format", "-f", choices=["json", "csv"], default="json", help="Export format")
    
    # stats command
    stats_parser = subparsers.add_parser("stats", help="Show statistics")
    
    args = parser.parse_args()
    
    if args.command == "list":
        cmd_list(args)
    elif args.command == "get":
        cmd_get(args)
    elif args.command == "add":
        cmd_add(args)
    elif args.command == "update":
        cmd_update(args)
    elif args.command == "batch":
        cmd_batch(args)
    elif args.command == "update-full":
        cmd_update_full(args)
    elif args.command == "rate":
        cmd_rate(args)
    elif args.command == "pending":
        cmd_pending(args)
    elif args.command == "export":
        cmd_export(args)
    elif args.command == "stats":
        cmd_stats(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
