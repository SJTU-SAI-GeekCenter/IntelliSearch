
# Agent Architecture Usage Guide (After Refactoring)


## 核心组件

### 1. BaseAgent (抽象基类)

所有 Agent 都必须继承 `BaseAgent` 并实现 `inference` 方法：

```python
from core.base import BaseAgent
from core.schema import AgentRequest, AgentResponse

class MyCustomAgent(BaseAgent):
    def __init__(self, name: str):
        super().__init__(name=name)

    def inference(self, request: AgentRequest) -> AgentResponse:
        # 实现推理逻辑
        return AgentResponse(
            status="success",
            answer="Response text",
            metadata={}
        )
```

### 2. AgentRequest & AgentResponse (统一数据格式)

所有 Agent 使用统一的输入输出格式：

```python
from core.schema import AgentRequest, AgentResponse

# 创建请求
request = AgentRequest(
    prompt="搜索最新的AI论文",
    metadata={
        "max_iterations": 10,
        "search_engine": "google"
    }
)

# 响应格式
response = AgentResponse(
    status="success",
    answer="我找到了5篇相关论文...",
    metadata={
        "iterations_used": 3,
        "tools_called": ["web_search", "scholar_search"]
    }
)
```

### 3. AgentFactory (工厂模式)

使用工厂创建 Agent 实例，避免硬编码依赖：

```python
from core.factory import AgentFactory

# 创建 Agent
agent = AgentFactory.create_agent(
    agent_type="mcp_base",
    name="MySearchAgent",
    model_name="deepseek-chat",
    max_tool_call=15
)

# 执行推理
request = AgentRequest(prompt="搜索Python教程")
response = agent.inference(request)
print(response.answer)
```

## 使用示例

### 示例 1: 直接使用 MCPBaseAgent

```python
from agents.mcp_agent import MCPBaseAgent
from core.schema import AgentRequest

# 初始化 Agent
agent = MCPBaseAgent(
    name="SearchAgent",
    model_name="deepseek-chat",
    system_prompt="You are a helpful search assistant",
    server_config_path="./config/config.example.json",
    max_tool_call=10
)

# 执行查询
request = AgentRequest(
    prompt="搜索最新的深度学习论文",
    metadata={"max_iterations": 5}
)

response = agent.inference(request)

# 查看结果
print(f"Status: {response.status}")
print(f"Answer: {response.answer}")
print(f"Metadata: {response.metadata}")
```

### 示例 2: 使用工厂模式创建 Agent

```python
from core import AgentFactory, AgentRequest

# 通过工厂创建
agent = AgentFactory.create_agent(
    agent_type="mcp_base",
    name="FactoryAgent",
    model_name="glm-4.5"
)

# 执行推理
request = AgentRequest(prompt="搜索北京天气")
response = agent.inference(request)
```

### 示例 3: 注册自定义 Agent

```python
from core import BaseAgent, AgentRequest, AgentResponse, AgentFactory

# 定义自定义 Agent
class SimpleAgent(BaseAgent):
    def __init__(self, name: str):
        super().__init__(name=name)

    def inference(self, request: AgentRequest) -> AgentResponse:
        # 简单的回显逻辑
        return AgentResponse(
            status="success",
            answer=f"Echo: {request.prompt}",
            metadata={"agent": self.name}
        )

# 注册到工厂
AgentFactory.register_agent("simple_echo", SimpleAgent)

# 使用自定义 Agent
agent = AgentFactory.create_agent(
    agent_type="simple_echo",
    name="EchoBot"
)

response = agent.inference(AgentRequest(prompt="Hello"))
print(response.answer)  # 输出: Echo: Hello
```


## 扩展新 Agent

### 步骤 1: 创建 Agent 类

在 `agents/` 目录下创建新的 Agent 文件：

```python
# agents/react_agent.py
from core.base import BaseAgent
from core.schema import AgentRequest, AgentResponse

class ReActSearchAgent(BaseAgent):
    """
    ReAct-style search agent with reasoning and acting loops.
    """

    def __init__(self, name: str = "ReActAgent", **kwargs):
        super().__init__(name=name)
        # 初始化逻辑
        pass

    def inference(self, request: AgentRequest) -> AgentResponse:
        # 实现 ReAct 推理循环
        thoughts = []
        actions = []

        # 推理逻辑
        thought = self._think(request.prompt)
        thoughts.append(thought)

        action = self._act(thought)
        actions.append(action)

        # 生成最终回答
        answer = self._generate_answer(thoughts, actions)

        return AgentResponse(
            status="success",
            answer=answer,
            metadata={
                "thoughts": thoughts,
                "actions": actions
            }
        )
```

### 步骤 2: 导出 Agent

在 `agents/__init__.py` 中添加导出：

```python
from agents.mcp_agent import MCPBaseAgent
from agents.react_agent import ReActSearchAgent  # 新增

__all__ = [
    "MCPBaseAgent",
    "ReActSearchAgent",  # 新增
]
```

### 步骤 3: 注册到工厂

在应用启动时注册：

```python
from agents import ReActSearchAgent
from core import AgentFactory

AgentFactory.register_agent("react_search", ReActSearchAgent)
```

### 步骤 4: 使用新 Agent

```python
agent = AgentFactory.create_agent(
    agent_type="react_search",
    name="MyReActAgent"
)

response = agent.inference(AgentRequest(prompt="Search query"))
```
