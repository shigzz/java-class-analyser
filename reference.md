# Reference

## 索引文件格式

类索引文件 `class_index.json` 的结构：

```json
{
  "jarCount": 150,
  "classCount": 25000,
  "indexPath": "/Users/xxx/analyser-mcp/my-project/class_index.json",
  "sampleEntries": [
    "com.example.MyClass -> /path/to/jar"
  ],
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

## 缓存机制

### 索引缓存

- 位置：`~/analyser-mcp/{project_name}/class_index.json`
- 首次扫描后自动缓存
- 使用 `--force-refresh` 强制重建

### 反编译缓存

- 位置：`~/analyser-mcp/{project_name}/mcp-decompile-cache/`
- 按包路径组织：`{package_path}/{ClassName}.java`
- 使用 `--no-cache` 跳过缓存

## 源码获取策略

反编译时按以下顺序尝试获取源码：

1. **源码 JAR**：查找 `*-sources.jar`，直接提取 `.java` 文件
2. **CFR 反编译**：若无源码 JAR，使用 CFR 反编译 `.class` 文件

## 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `M2_HOME` | `~/.m2` | Maven 本地仓库根目录 |
| `CFR_JAR` | `cfr.jar` | CFR 反编译器 JAR 路径（备用） |

## 依赖要求

- Python 3.8+
- Maven（用于解析依赖树）
- Java（可选，CFR 需要）

## 限制说明

1. **内部类**：索引不包含内部类（含 `$` 符号的类）
2. **非 JAR 依赖**：仅处理 `jar` 类型依赖，跳过 `pom`、`war` 等
3. **Maven 项目**：目前仅支持 Maven 项目，不支持 Gradle

## 故障排除

### 索引为空

- 检查 Maven 是否正确安装：`mvn -v`
- 检查项目路径是否正确
- 查看是否有 `pom.xml`

### 反编译失败

- 确保已先运行 `scan_dependencies.py`
- 检查类名是否完整（包含包名）
- 尝试使用 `--no-cache` 重新反编译

