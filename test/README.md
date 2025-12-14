# IntelliSearch 后端API测试

这个文件夹包含了用于测试IntelliSearch后端API的工具和脚本。

## 文件说明

### 1. `quick_test.py`
快速测试脚本，用于检查后端API的基础功能是否正常。

**功能：**
- 健康检查
- 工具列表获取
- 简单聊天接口测试

**使用方法：**
```bash
python3 test/quick_test.py
```

### 2. `test_backend_api.py`
详细的API测试脚本，包含同步和异步接口的全面测试。

**功能：**
- 同步接口测试（健康检查、API文档访问）
- 异步接口测试（流式聊天、工具列表、非流式聊天）
- 详细的错误报告和结果统计

**使用方法：**
```bash
# 使用默认URL (http://localhost:8000)
python3 test/test_backend_api.py

# 指定自定义URL
python3 test/test_backend_api.py --url http://localhost:9000

# 显示帮助
python3 test/test_backend_api.py --help
```

### 3. `run_tests.sh`
自动化测试运行脚本，会检查环境并运行所有测试。

**功能：**
- 自动检查Python环境和依赖
- 检查后端服务是否运行
- 按顺序运行快速测试和详细测试
- 提供测试总结和故障排除建议

**使用方法：**
```bash
# 直接运行
./test/run_tests.sh

# 或
bash test/run_tests.sh
```

## 使用前提条件

### 1. 后端服务运行
确保后端服务正在运行：
```bash
# 方式1：使用启动脚本
python3 scripts/start_backend.py

# 方式2：直接使用uvicorn
uvicorn backend.main_fastapi:app --reload --host 0.0.0.0 --port 8000
```

### 2. Python依赖
安装必要的Python包：
```bash
pip3 install requests aiohttp
```

### 3. 端口确认
确认后端服务运行在正确的端口（默认8000）。

## 测试内容说明

### 基础功能测试
- **健康检查**：验证服务是否响应
- **API文档**：检查Swagger文档是否可访问
- **工具列表**：验证MCP工具是否正确加载

### 聊天功能测试
- **非流式聊天**：测试基本的问答功能
- **流式聊天**：测试实时响应功能
- **工具调用**：验证MCP工具的调用和响应

### 错误处理测试
- **网络超时**：测试服务的响应时间
- **错误输入**：验证异常情况的处理
- **服务不可用**：测试故障转移机制

## 故障排除

### 常见问题

1. **连接被拒绝**
   - 检查后端服务是否启动
   - 确认端口配置是否正确

2. **工具列表为空**
   - 检查`config.json`配置
   - 确认MCP服务器是否正常启动

3. **聊天请求超时**
   - 检查网络连接
   - 查看后端日志了解具体错误

4. **依赖包缺失**
   - 运行`pip3 install -r requirements.txt`
   - 或单独安装`requests`和`aiohttp`

### 调试建议

1. 查看后端日志：
```bash
# 如果使用uvicorn启动，日志会直接显示在终端
# 如果使用启动脚本，可以查看日志文件
tail -f logs/backend.log
```

2. 测试网络连接：
```bash
curl http://localhost:8000/
```

3. 检查进程：
```bash
ps aux | grep uvicorn
```

## 扩展测试

### 自定义测试用例
可以在`test_backend_api.py`中添加更多测试用例：

```python
async def test_custom_feature(self) -> bool:
    """自定义测试功能"""
    # 添加你的测试逻辑
    return True
```

### 压力测试
可以使用`locust`或其他工具进行压力测试：

```bash
pip3 install locust
locust -f test/locustfile.py
```

## 贡献指南

如果发现问题或有改进建议：
1. 检查现有issue
2. 创建详细的bug报告
3. 提供复现步骤和环境信息
4. 提交Pull Request

## 许可证

测试工具遵循项目整体的许可证条款。