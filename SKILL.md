---
name: java-class-analyzer
description: Analyze Maven dependencies in Java projects, build class indexes, and decompile classes from JAR files to retrieve source code. Use when you need to view third-party library source code, find which JAR contains a specific class, decompile class files, or analyze Maven dependencies. Applicable for scenarios like "decompile Java class", "view JAR source code", "analyze Maven dependencies", "find which JAR a class belongs to".
---

# Java Class Analyzer

Provides Java class analysis capabilities for AI Agents, supporting Maven dependency scanning and class file decompilation to retrieve source code.

## Dependency Installation

Install dependencies before first use:

```bash
pip install -r scripts/requirements.txt
```

## Core Features

### 1. Scan Maven Dependencies

Scan the project's Maven dependency tree, extract all JAR files, and build a class index:

```bash
python scripts/scan_dependencies.py <project_path> [--force-refresh]
```

**Parameters**:
- `project_path`: Root directory of the Maven project (absolute path)
- `--force-refresh`: Force refresh, ignore cache

**Output**: Generates class index file to `~/analyser-mcp/{project_name}/class_index.json`

### 2. Decompile Java Class

Decompile and retrieve source code by fully qualified class name:

```bash
python scripts/decompile_class.py <class_name> <project_path> [--no-cache]
```

**Parameters**:
- `class_name`: Fully qualified class name, e.g., `com.alibaba.fastjson2.JSON`
- `project_path`: Root directory of the Maven project
- `--no-cache`: Do not use cache

**Output**: Prints the decompiled Java source code

### 3. Search Class Name

Search for class names in the established index:

```bash
python scripts/search_class.py <keyword> <project_path>
```

**Parameters**:
- `keyword`: Search keyword (supports partial matching)
- `project_path`: Root directory of the Maven project

## Usage Workflow

1. **First Use**: Run `scan_dependencies.py` to build the class index
2. **Search Class**: Use `search_class.py` to find the target class
3. **View Source**: Use `decompile_class.py` to decompile the specified class

## Typical Scenarios

### Scenario 1: View Third-Party Library Implementation

```bash
# 1. Build index (only needed for first time)
python scripts/scan_dependencies.py /path/to/my-project

# 2. Search class
python scripts/search_class.py JSON /path/to/my-project

# 3. Decompile to view source code
python scripts/decompile_class.py com.alibaba.fastjson2.JSON /path/to/my-project
```

### Scenario 2: Troubleshoot Dependency Conflicts

Build the index first, then search for classes with the same name to see which JAR files they come from.

## Detailed Documentation

See [reference.md](reference.md) for index file format, caching mechanism, and advanced configuration.

