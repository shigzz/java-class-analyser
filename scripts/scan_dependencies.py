#!/usr/bin/env python3
"""
扫描 Maven 项目依赖，建立类索引

Usage:
    python scan_dependencies.py <project_path> [--force-refresh]

Examples:
    python scan_dependencies.py /path/to/my-maven-project
    python scan_dependencies.py /path/to/my-maven-project --force-refresh
"""

import argparse
import json
import os
import re
import subprocess
import sys
import zipfile
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Set
import random


def get_index_path(project_path: str) -> Path:
    """获取索引文件路径"""
    project_name = os.path.basename(project_path.rstrip(os.sep))
    home = os.path.expanduser("~")
    return Path(home) / "analyser-mcp" / project_name / "class_index.json"


def get_maven_local_repo() -> str:
    """获取 Maven 本地仓库路径"""
    m2_home = os.environ.get("M2_HOME", os.path.expanduser("~/.m2"))
    return os.path.join(m2_home, "repository")


def resolve_jar_path(dependency: str, local_repo: str) -> str:
    """
    解析依赖坐标为 JAR 路径
    
    Args:
        dependency: Maven 依赖坐标，格式：groupId:artifactId:type:version:scope
        local_repo: Maven 本地仓库路径
    
    Returns:
        JAR 包的本地路径，如果无法解析则返回 None
    """
    parts = dependency.split(":")
    if len(parts) < 4:
        return None
        
    group_id, artifact_id, dep_type, version = parts[0], parts[1], parts[2], parts[3]
    
    # 只处理 jar 类型
    if dep_type != "jar":
        return None
        
    # 构建 JAR 包路径
    group_path = group_id.replace(".", os.sep)
    jar_name = f"{artifact_id}-{version}.jar"
    
    return os.path.join(local_repo, group_path, artifact_id, version, jar_name)


def list_maven_dependencies(project_path: str) -> List[str]:
    """
    获取 Maven 依赖的 JAR 包路径列表
    
    Args:
        project_path: Maven 项目路径
    
    Returns:
        JAR 包路径列表
    """
    jar_paths: Set[str] = set()
    
    # 优先使用项目目录下的 mvnw
    mvnw = os.path.join(project_path, "mvnw")
    if os.path.isfile(mvnw) and os.access(mvnw, os.X_OK):
        mvn_cmd = mvnw
    else:
        # 判断操作系统
        mvn_cmd = "mvn.cmd" if sys.platform == "win32" else "mvn"
    
    try:
        print(f"Running Maven dependency resolution...")
        result = subprocess.run(
            [mvn_cmd, "dependency:resolve", "dependency:tree", "-DoutputType=text"],
            cwd=project_path,
            capture_output=True,
            text=True,
            timeout=300
        )
        
        # 匹配依赖行
        # 格式: [INFO] +- groupId:artifactId:type:version:scope
        pattern = re.compile(
            r'\[INFO\].*?([a-zA-Z0-9._-]+:[a-zA-Z0-9._-]+:[a-zA-Z0-9._-]+:[a-zA-Z0-9._-]+:[a-zA-Z0-9._-]+)'
        )
        local_repo = get_maven_local_repo()
        
        for line in result.stdout.split('\n'):
            match = pattern.search(line)
            if match:
                dep = match.group(1)
                jar_path = resolve_jar_path(dep, local_repo)
                if jar_path and os.path.exists(jar_path):
                    jar_paths.add(jar_path)
        
        if result.returncode != 0:
            print(f"Warning: Maven command exited with code {result.returncode}", file=sys.stderr)
            if result.stderr:
                print(f"Maven stderr: {result.stderr[:500]}", file=sys.stderr)
                    
    except subprocess.TimeoutExpired:
        print("Error: Maven command timed out", file=sys.stderr)
    except FileNotFoundError:
        print(f"Error: Maven not found. Please install Maven or use a project with mvnw", file=sys.stderr)
    except Exception as e:
        print(f"Error listing dependencies: {e}", file=sys.stderr)
        
    return list(jar_paths)


def extract_classes_from_jar(jar_path: str) -> List[Dict]:
    """
    从 JAR 包提取类信息
    
    Args:
        jar_path: JAR 包路径
    
    Returns:
        类索引条目列表
    """
    classes = []
    
    try:
        with zipfile.ZipFile(jar_path, 'r') as jar:
            for name in jar.namelist():
                # 只处理 .class 文件，排除内部类（含 $ 符号）
                if name.endswith(".class") and "$" not in name:
                    # 转换路径为类名: com/example/MyClass.class -> com.example.MyClass
                    class_name = name[:-6].replace("/", ".")
                    
                    # 解析包名和简单类名
                    last_dot = class_name.rfind(".")
                    package_name = class_name[:last_dot] if last_dot > 0 else ""
                    simple_name = class_name[last_dot + 1:] if last_dot > 0 else class_name
                    
                    classes.append({
                        "className": class_name,
                        "jarPath": jar_path,
                        "packageName": package_name,
                        "simpleName": simple_name
                    })
    except zipfile.BadZipFile:
        print(f"Warning: Invalid JAR file: {jar_path}", file=sys.stderr)
    except Exception as e:
        print(f"Error extracting from {jar_path}: {e}", file=sys.stderr)
        
    return classes


def scan_dependencies(project_path: str, force_refresh: bool = False) -> Dict:
    """
    扫描依赖并建立索引
    
    Args:
        project_path: Maven 项目路径
        force_refresh: 是否强制刷新
    
    Returns:
        扫描结果
    """
    # 规范化路径
    project_path = os.path.abspath(project_path)
    index_path = get_index_path(project_path)
    
    # 如果强制刷新且文件存在，删除旧文件
    if force_refresh and index_path.exists():
        index_path.unlink()
        print(f"Deleted existing index file")
    
    # 检查缓存
    if not force_refresh and index_path.exists():
        try:
            with open(index_path, 'r', encoding='utf-8') as f:
                cached = json.load(f)
            print(f"Loaded from cache: {cached['classCount']} classes from {cached['jarCount']} jars")
            print(f"Index path: {index_path}")
            # 返回精简结果
            return {
                "jarCount": cached["jarCount"],
                "classCount": cached["classCount"],
                "indexPath": str(index_path),
                "sampleEntries": cached.get("sampleEntries", [])
            }
        except Exception as e:
            print(f"Warning: Failed to read cache, rebuilding: {e}", file=sys.stderr)
    
    # 检查是否是 Maven 项目
    pom_path = os.path.join(project_path, "pom.xml")
    if not os.path.exists(pom_path):
        print(f"Error: No pom.xml found in {project_path}", file=sys.stderr)
        sys.exit(1)
    
    print(f"Scanning Maven dependencies for: {project_path}")
    
    # 获取所有 JAR 依赖
    jar_paths = list_maven_dependencies(project_path)
    print(f"Found {len(jar_paths)} JAR dependencies")
    
    if not jar_paths:
        print("Warning: No JAR dependencies found. Check Maven configuration.", file=sys.stderr)
    
    # 提取类信息
    all_classes = []
    processed_jars = 0
    
    for jar_path in jar_paths:
        classes = extract_classes_from_jar(jar_path)
        if classes:
            all_classes.extend(classes)
            processed_jars += 1
            jar_name = os.path.basename(jar_path)
            print(f"  [{processed_jars}/{len(jar_paths)}] {jar_name}: {len(classes)} classes")
    
    # 生成示例条目
    sample_size = min(10, len(all_classes))
    samples = random.sample(all_classes, sample_size) if all_classes else []
    sample_entries = [f"{c['className']} -> {os.path.basename(c['jarPath'])}" for c in samples]
    
    # 构建结果
    result = {
        "jarCount": processed_jars,
        "classCount": len(all_classes),
        "indexPath": str(index_path),
        "sampleEntries": sample_entries,
        "lastUpdated": datetime.now().isoformat(),
        "classIndexes": all_classes
    }
    
    # 保存索引
    try:
        index_path.parent.mkdir(parents=True, exist_ok=True)
        with open(index_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"\nIndex saved to: {index_path}")
    except Exception as e:
        print(f"Error saving index: {e}", file=sys.stderr)
        sys.exit(1)
    
    print(f"\nSummary:")
    print(f"  Total JARs processed: {processed_jars}")
    print(f"  Total classes indexed: {len(all_classes)}")
    print(f"\nSample entries:")
    for entry in sample_entries[:5]:
        print(f"  - {entry}")
    
    # 返回精简结果（不含完整类列表）
    return {
        "jarCount": processed_jars,
        "classCount": len(all_classes),
        "indexPath": str(index_path),
        "sampleEntries": sample_entries
    }


def main():
    parser = argparse.ArgumentParser(
        description="Scan Maven dependencies and build class index",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s /path/to/my-maven-project
  %(prog)s /path/to/my-maven-project --force-refresh
        """
    )
    parser.add_argument(
        "project_path",
        help="Maven project root directory (absolute path)"
    )
    parser.add_argument(
        "--force-refresh",
        action="store_true",
        help="Force refresh, ignore cache"
    )
    
    args = parser.parse_args()
    
    # 验证路径
    if not os.path.isdir(args.project_path):
        print(f"Error: Directory not found: {args.project_path}", file=sys.stderr)
        sys.exit(1)
    
    result = scan_dependencies(args.project_path, args.force_refresh)
    
    # 输出 JSON 结果（可用于程序化处理）
    print(f"\nJSON Result:")
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

