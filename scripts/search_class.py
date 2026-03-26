#!/usr/bin/env python3
"""
在类索引中搜索类名

Usage:
    python search_class.py <keyword> <project_path> [--limit N]

Examples:
    python search_class.py JSON /path/to/my-project
    python search_class.py RequestMapping /path/to/my-project --limit 20
    python search_class.py com.alibaba /path/to/my-project
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import List, Dict


def get_index_path(project_path: str) -> Path:
    """获取索引文件路径"""
    project_name = os.path.basename(project_path.rstrip(os.sep))
    home = os.path.expanduser("~")
    return Path(home) / "analyser-mcp" / project_name / "class_index.json"


def search_classes(keyword: str, project_path: str, limit: int = 50) -> List[Dict]:
    """
    搜索类名
    
    Args:
        keyword: 搜索关键词
        project_path: 项目路径
        limit: 最大返回数量
    
    Returns:
        匹配的类列表
    """
    project_path = os.path.abspath(project_path)
    index_path = get_index_path(project_path)
    
    if not index_path.exists():
        raise FileNotFoundError(
            f"Index not found: {index_path}\n"
            f"Please run scan_dependencies.py first to build the class index."
        )
    
    with open(index_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    class_indexes = data.get("classIndexes", [])
    if not class_indexes:
        raise ValueError("Index file contains no class information")
    
    # 搜索匹配的类
    keyword_lower = keyword.lower()
    matches = []
    
    for entry in class_indexes:
        class_name = entry["className"]
        simple_name = entry.get("simpleName", "")
        
        # 匹配完整类名或简单类名
        if keyword_lower in class_name.lower() or keyword_lower in simple_name.lower():
            matches.append(entry)
            
            if len(matches) >= limit:
                break
    
    return matches


def main():
    parser = argparse.ArgumentParser(
        description="Search for classes in the index",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s JSON /path/to/my-project
  %(prog)s RequestMapping /path/to/my-project --limit 20
  %(prog)s com.alibaba /path/to/my-project

Note:
  Run scan_dependencies.py first to build the class index.
        """
    )
    parser.add_argument(
        "keyword",
        help="Search keyword (supports partial match)"
    )
    parser.add_argument(
        "project_path",
        help="Maven project root directory"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=50,
        help="Maximum number of results (default: 50)"
    )
    
    args = parser.parse_args()
    
    # 验证路径
    if not os.path.isdir(args.project_path):
        print(f"Error: Directory not found: {args.project_path}", file=sys.stderr)
        sys.exit(1)
    
    try:
        matches = search_classes(args.keyword, args.project_path, args.limit)
        
        if not matches:
            print(f"No classes found matching '{args.keyword}'")
            sys.exit(0)
        
        print(f"Found {len(matches)} classes matching '{args.keyword}':\n")
        
        # 按包名分组显示
        by_package = {}
        for m in matches:
            pkg = m.get("packageName", "(default)")
            if pkg not in by_package:
                by_package[pkg] = []
            by_package[pkg].append(m)
        
        for pkg in sorted(by_package.keys()):
            print(f"Package: {pkg}")
            for m in by_package[pkg]:
                jar_name = os.path.basename(m["jarPath"])
                print(f"  - {m['simpleName']}")
                print(f"    Full: {m['className']}")
                print(f"    JAR:  {jar_name}")
            print()
        
        # 输出 JSON 格式（便于程序化处理）
        if args.limit <= 10:
            print("JSON Result:")
            print(json.dumps(matches, indent=2, ensure_ascii=False))
            
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

