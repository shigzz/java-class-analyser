---
name: java-class-analyzer
description: 分析 Java 项目的 Maven 依赖，建立类索引，反编译 JAR 包中的类获取源码。当用户需要查看第三方库源码、查找某个类在哪个 JAR 包、反编译 class 文件、分析 Maven 依赖时使用。适用于「反编译 Java 类」「查看 JAR 包源码」「分析 Maven 依赖」「查找类所在的 JAR」等场景。
---

# Java Class Analyzer

为 AI Agent 提供 Java 类分析能力，支持扫描 Maven 依赖并反编译 class 文件获取源码。

## 依赖安装

首次使用前需安装依赖：

```bash
pip install -r scripts/requirements.txt
```

## 核心功能

### 1. 扫描 Maven 依赖

扫描项目的 Maven 依赖树，提取所有 JAR 包并建立类索引：

```bash
python scripts/scan_dependencies.py <project_path> [--force-refresh]
```

**参数**：
- `project_path`: Maven 项目的根目录（绝对路径）
- `--force-refresh`: 强制刷新，忽略缓存

**输出**：生成类索引文件到 `~/analyser-mcp/{project_name}/class_index.json`

### 2. 反编译 Java 类

根据完整类名反编译获取源代码：

```bash
python scripts/decompile_class.py <class_name> <project_path> [--no-cache]
```

**参数**：
- `class_name`: 完整类名，如 `com.alibaba.fastjson2.JSON`
- `project_path`: Maven 项目的根目录
- `--no-cache`: 不使用缓存

**输出**：打印反编译后的 Java 源代码

### 3. 搜索类名

在已建立的索引中搜索类名：

```bash
python scripts/search_class.py <keyword> <project_path>
```

**参数**：
- `keyword`: 搜索关键词（支持部分匹配）
- `project_path`: Maven 项目的根目录

## 使用流程

1. **首次使用**：先运行 `scan_dependencies.py` 建立类索引
2. **搜索类名**：使用 `search_class.py` 查找目标类
3. **查看源码**：使用 `decompile_class.py` 反编译指定类

## 典型场景

### 场景一：查看第三方库的实现

```bash
# 1. 建立索引（仅首次需要）
python scripts/scan_dependencies.py /path/to/my-project

# 2. 搜索类
python scripts/search_class.py JSON /path/to/my-project

# 3. 反编译查看源码
python scripts/decompile_class.py com.alibaba.fastjson2.JSON /path/to/my-project
```

### 场景二：排查依赖冲突

先建立索引，然后搜索同名类查看来自哪些 JAR 包。

## 详细说明

参见 [reference.md](reference.md) 了解索引文件格式、缓存机制和高级配置。

