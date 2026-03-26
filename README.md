# Java Class Analyzer

A Python-based tool for analyzing Maven project dependencies and decompiling Java classes. Designed for AI Agents working with Java codebases.

## Overview

This tool provides three main capabilities:

1. **Scan Dependencies** - Build an index of all classes in your Maven project dependencies
2. **Search Classes** - Find classes by name in the dependency index
3. **Decompile Classes** - View source code from compiled `.class` files using CFR or source JARs

## Installation

```bash
# Clone or copy the repository
cd java-class-analyser

# Install dependencies (uses Python standard library only)
pip install -r scripts/requirements.txt

# Optional: Install CFR decompiler for better results
# macOS:
brew install cfr-decompiler

# Or download from: https://www.benf.org/other/cfr/
```

## Requirements

- Python 3.8+
- Maven (or a project with `mvnw` wrapper)
- Java (optional, only needed for CFR decompilation)
- CFR decompiler (optional, recommended)

## Usage

### 1. Scan Maven Dependencies

Build a class index from all JAR dependencies in your Maven project:

```bash
python scripts/scan_dependencies.py /path/to/maven-project
```

Options:
- `--force-refresh` - Rebuild the index even if a cached version exists

**Output:** Index saved to `~/analyser-mcp/{project_name}/class_index.json`

### 2. Search Classes

Find classes by keyword (supports partial matching):

```bash
python scripts/search_class.py JSON /path/to/maven-project
python scripts/search_class.py RequestMapping /path/to/maven-project --limit 20
```

### 3. Decompile Classes

View source code for a fully qualified class name:

```bash
python scripts/decompile_class.py com.alibaba.fastjson2.JSON /path/to/maven-project
python scripts/decompile_class.py org.springframework.web.bind.annotation.RequestMapping /path/to/maven-project --no-cache
```

The decompiler tries these sources in order:
1. **Source JAR** (`*-sources.jar`) - original source code
2. **CFR decompiler** - decompiles `.class` bytecode
3. **javap** - bytecode disassembly (fallback)

## Typical Workflow

```bash
# 1. Build the index (run once per project)
python scripts/scan_dependencies.py /path/to/my-project

# 2. Search for a class
python scripts/search_class.py JSON /path/to/my-project

# 3. Decompile to view source
python scripts/decompile_class.py com.alibaba.fastjson2.JSON /path/to/my-project
```

## Cache Locations

- **Class index:** `~/analyser-mcp/{project_name}/class_index.json`
- **Decompiled sources:** `~/analyser-mcp/{project_name}/mcp-decompile-cache/`

## Index Format

The class index is a JSON file containing:

```json
{
  "jarCount": 150,
  "classCount": 25000,
  "indexPath": "/Users/xxx/analyser-mcp/my-project/class_index.json",
  "lastUpdated": "2025-03-26T10:30:00",
  "classIndexes": [
    {
      "className": "com.example.MyClass",
      "jarPath": "/path/to/dependency.jar",
      "packageName": "com.example",
      "simpleName": "MyClass"
    }
  ]
}
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `M2_HOME` | `~/.m2` | Maven local repository path |
| `CFR_JAR` | `cfr.jar` | Path to CFR decompiler JAR |

## Limitations

- Only supports Maven projects (not Gradle)
- Only indexes `.jar` dependencies (skips `pom`, `war`, etc.)
- Internal classes (containing `$`) are excluded from the index

## Troubleshooting

### "Index not found" error

Run `scan_dependencies.py` first to build the class index.

### Decompilation fails

Ensure CFR is installed:
```bash
brew install cfr-decompiler  # macOS
```

Or set `CFR_JAR` environment variable to point to the CFR JAR file.

### Empty index

- Check Maven is installed: `mvn -v`
- Verify the project has a valid `pom.xml`
- Check that dependencies exist in `~/.m2/repository`

## License

MIT
