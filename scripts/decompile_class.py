#!/usr/bin/env python3
"""
反编译 Java 类获取源码

Usage:
    python decompile_class.py <class_name> <project_path> [--no-cache]

Examples:
    python decompile_class.py com.alibaba.fastjson2.JSON /path/to/my-project
    python decompile_class.py org.springframework.web.bind.annotation.RequestMapping /path/to/my-project --no-cache
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import Optional


def get_index_path(project_path: str) -> Path:
    """获取索引文件路径"""
    project_name = os.path.basename(project_path.rstrip(os.sep))
    home = os.path.expanduser("~")
    return Path(home) / "analyser-mcp" / project_name / "class_index.json"


def get_cache_path(class_name: str, project_path: str) -> Path:
    """获取反编译缓存路径"""
    project_name = os.path.basename(project_path.rstrip(os.sep))
    home = os.path.expanduser("~")
    
    # 分离包名和类名
    if "." not in class_name:
        raise ValueError(f"Invalid class name (missing package): {class_name}")
    
    package_path = class_name.rsplit(".", 1)[0].replace(".", os.sep)
    simple_name = class_name.rsplit(".", 1)[1]
    
    return Path(home) / "analyser-mcp" / project_name / "mcp-decompile-cache" / package_path / f"{simple_name}.java"


def find_jar_for_class(class_name: str, project_path: str) -> str:
    """
    从索引中查找类对应的 JAR 包
    
    Args:
        class_name: 完整类名
        project_path: 项目路径
    
    Returns:
        JAR 包路径
    
    Raises:
        FileNotFoundError: 索引文件不存在
        ValueError: 类不在索引中
    """
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
    
    for entry in class_indexes:
        if entry["className"] == class_name:
            return entry["jarPath"]
    
    raise ValueError(f"Class not found in index: {class_name}")


def try_get_source_jar(jar_path: str) -> Optional[str]:
    """
    尝试获取源码 JAR
    
    Args:
        jar_path: 原始 JAR 路径
    
    Returns:
        源码 JAR 路径，如果不存在则返回 None
    """
    if not jar_path.endswith(".jar"):
        return None
    
    source_jar = jar_path[:-4] + "-sources.jar"
    return source_jar if os.path.exists(source_jar) else None


def extract_source_from_jar(source_jar: str, class_name: str) -> Optional[str]:
    """
    从源码 JAR 提取 Java 文件
    
    Args:
        source_jar: 源码 JAR 路径
        class_name: 完整类名
    
    Returns:
        Java 源代码，如果提取失败则返回 None
    """
    java_file_name = class_name.replace(".", "/") + ".java"
    
    try:
        with zipfile.ZipFile(source_jar, 'r') as jar:
            if java_file_name in jar.namelist():
                with jar.open(java_file_name) as f:
                    return f.read().decode('utf-8')
    except Exception as e:
        print(f"Warning: Failed to extract from source JAR: {e}", file=sys.stderr)
    
    return None


def extract_class_file(jar_path: str, class_name: str, temp_dir: str) -> str:
    """
    从 JAR 包提取 class 文件
    
    Args:
        jar_path: JAR 包路径
        class_name: 完整类名
        temp_dir: 临时目录
    
    Returns:
        提取后的 class 文件路径
    """
    class_file_name = class_name.replace(".", "/") + ".class"
    
    with zipfile.ZipFile(jar_path, 'r') as jar:
        if class_file_name not in jar.namelist():
            raise FileNotFoundError(f"Class file not found in JAR: {class_file_name}")
        
        # 提取到临时目录，保持目录结构
        jar.extract(class_file_name, temp_dir)
        return os.path.join(temp_dir, class_file_name)


def decompile_with_cfr(class_file_path: str) -> str:
    """
    使用 CFR 反编译
    
    Args:
        class_file_path: class 文件路径
    
    Returns:
        反编译后的源代码
    """
    # 尝试多种方式调用 CFR
    cfr_commands = [
        ["cfr", class_file_path],  # 系统安装的 cfr
        ["cfr-decompiler", class_file_path],  # Homebrew 安装
    ]
    
    # 检查环境变量中的 CFR_JAR
    cfr_jar = os.environ.get("CFR_JAR")
    if cfr_jar and os.path.exists(cfr_jar):
        cfr_commands.insert(0, ["java", "-jar", cfr_jar, class_file_path])
    
    last_error = None
    for cmd in cfr_commands:
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout
            
            last_error = result.stderr or "Empty output"
            
        except FileNotFoundError:
            continue
        except subprocess.TimeoutExpired:
            last_error = "Decompilation timed out"
        except Exception as e:
            last_error = str(e)
    
    # 如果 CFR 不可用，尝试使用 javap 作为备选（只能输出字节码，不是真正的反编译）
    try:
        result = subprocess.run(
            ["javap", "-c", "-p", class_file_path],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            return f"// Note: CFR not available, using javap bytecode output\n// Install CFR: brew install cfr-decompiler (macOS)\n\n{result.stdout}"
    except Exception:
        pass
    
    return f"// Decompilation failed: {last_error}\n// Please install CFR decompiler: brew install cfr-decompiler (macOS)"


def decompile_class(class_name: str, project_path: str, use_cache: bool = True) -> str:
    """
    反编译指定的类
    
    Args:
        class_name: 完整类名
        project_path: 项目路径
        use_cache: 是否使用缓存
    
    Returns:
        Java 源代码
    """
    project_path = os.path.abspath(project_path)
    cache_path = get_cache_path(class_name, project_path)
    
    # 检查缓存
    if use_cache and cache_path.exists():
        print(f"# Loaded from cache: {cache_path}", file=sys.stderr)
        return cache_path.read_text(encoding='utf-8')
    
    # 查找 JAR 包
    jar_path = find_jar_for_class(class_name, project_path)
    print(f"# Found in: {os.path.basename(jar_path)}", file=sys.stderr)
    
    source_code = None
    
    # 尝试从源码 JAR 获取
    source_jar = try_get_source_jar(jar_path)
    if source_jar:
        source_code = extract_source_from_jar(source_jar, class_name)
        if source_code:
            print(f"# Extracted from sources: {os.path.basename(source_jar)}", file=sys.stderr)
    
    # 如果没有源码 JAR，使用 CFR 反编译
    if not source_code:
        print("# Decompiling with CFR...", file=sys.stderr)
        
        # 创建临时目录
        temp_dir = tempfile.mkdtemp(prefix="java-class-analyzer-")
        try:
            class_file = extract_class_file(jar_path, class_name, temp_dir)
            source_code = decompile_with_cfr(class_file)
        finally:
            # 清理临时目录
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    # 保存缓存
    if use_cache and source_code:
        try:
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            cache_path.write_text(source_code, encoding='utf-8')
            print(f"# Cached to: {cache_path}", file=sys.stderr)
        except Exception as e:
            print(f"# Warning: Failed to cache: {e}", file=sys.stderr)
    
    return source_code


def main():
    parser = argparse.ArgumentParser(
        description="Decompile Java class to source code",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s com.alibaba.fastjson2.JSON /path/to/my-project
  %(prog)s org.springframework.web.bind.annotation.RequestMapping /path/to/my-project --no-cache

Note:
  Run scan_dependencies.py first to build the class index.
  Install CFR for best results: brew install cfr-decompiler (macOS)
        """
    )
    parser.add_argument(
        "class_name",
        help="Full class name (e.g., com.example.MyClass)"
    )
    parser.add_argument(
        "project_path",
        help="Maven project root directory"
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Don't use cache, always decompile"
    )
    
    args = parser.parse_args()
    
    # 验证路径
    if not os.path.isdir(args.project_path):
        print(f"Error: Directory not found: {args.project_path}", file=sys.stderr)
        sys.exit(1)
    
    try:
        source = decompile_class(args.class_name, args.project_path, not args.no_cache)
        print(source)
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

