# 12306 Train Search MCP Server

Python implementation of 12306 train search MCP server, converted from the original TypeScript version.

## 功能特性

- 查询12306余票信息
- 过滤列车信息 (G/D/Z/T/K/O/F/S)
- 查询列车经停站信息
- 中转查询 (transfer tickets)
- 车站信息查询

## 安装

```bash
pip install -r requirements.txt
```

## 使用

### 作为 MCP 服务器运行

```bash
python server.py
```

### 可用工具

#### 1. `get_current_date`
获取当前日期 (上海时区)

**返回:** "yyyy-MM-dd" 格式的当前日期

#### 2. `get_stations_code_in_city`
查询指定城市的所有火车站代码

**参数:**
- `city`: 中文城市名 (如 "北京", "上海")

**返回:** JSON 格式的车站列表

#### 3. `get_station_code_of_citys`
查询城市的代表性车站代码

**参数:**
- `citys`: 城市名，用 | 分隔 (如 "北京|上海")

**返回:** JSON 格式的车站代码映射

#### 4. `get_station_code_by_names`
通过具体车站名查询车站代码

**参数:**
- `stationNames`: 车站名，用 | 分隔 (如 "北京南|上海虹桥")

**返回:** JSON 格式的车站代码映射

#### 5. `get_tickets`
查询12306余票信息

**参数:**
- `date`: 查询日期 (格式: "yyyy-MM-dd")
- `fromStation`: 出发站代码
- `toStation`: 到达站代码
- `trainFilterFlags`: 车次筛选标志 (可选: G/D/Z/T/K/O/F/S)
- `earliestStartTime`: 最早出发时间 0-24 (默认: 0)
- `latestStartTime`: 最迟出发时间 0-24 (默认: 24)
- `sortFlag`: 排序方式 (可选: startTime/arriveTime/duration)
- `sortReverse`: 是否逆向排序 (默认: False)
- `limitedNum`: 返回结果数量限制 (默认: 0, 不限制)
- `format`: 返回格式 (text/csv/json, 默认: text)

**返回:** 格式化的余票信息

#### 6. `get_interline_tickets`
查询12306中转余票信息

**参数:**
- `date`: 查询日期 (格式: "yyyy-MM-dd")
- `fromStation`: 出发站代码
- `toStation`: 到达站代码
- `middleStation`: 中转站代码 (可选)
- `showWZ`: 是否显示无座车 (默认: False)
- `trainFilterFlags`: 车次筛选标志
- `earliestStartTime`: 最早出发时间 (默认: 0)
- `latestStartTime`: 最迟出发时间 (默认: 24)
- `sortFlag`: 排序方式
- `sortReverse`: 是否逆向排序 (默认: False)
- `limitedNum`: 返回结果数量限制 (默认: 10)
- `format`: 返回格式 (text/json, 默认: text)

**返回:** 格式化的中转票信息

#### 7. `get_train_route_stations`
查询特定列车的经停站信息

**参数:**
- `trainCode`: 车次代码 (如 "G1033")
- `departDate`: 出发日期 (格式: "yyyy-MM-dd")
- `format`: 返回格式 (text/json, 默认: text)

**返回:** 格式化的经停站信息

## MCP 配置示例

在 MCP 客户端配置文件中添加:

```json
{
  "mcpServers": {
    "12306-train-search": {
      "command": "python",
      "args": ["/path/to/train_search/server.py"]
    }
  }
}
```

## 项目结构

```
train_search/
├── server.py          # MCP 服务器主文件
├── types.py           # 数据模型定义
├── utils.py           # 工具函数
├── api_client.py      # 12306 API 客户端
├── requirements.txt   # Python 依赖
└── README.md          # 项目说明
```

## 数据模型

### TicketInfo
车票信息，包含车次、时间、票价等

### StationData
车站信息，包含车站名、代码、拼音等

### Price
票价信息，包含座席类型、价格、余票数量等

## 注意事项

1. 本项目仅用于学习目的
2. API 请求频率需要合理控制，避免对 12306 服务器造成压力
3. 部分功能可能需要 cookies 验证
4. 建议在合理使用范围内调用 API

## 从 TypeScript 迁移

本项目从原始的 TypeScript 版本 (https://github.com/Joooook/12306-mcp) 重写为 Python 版本，主要改动:

- 使用 dataclass 替代 TypeScript interface
- 使用 requests 库替代 axios
- 使用 FastMCP 框架实现 MCP 协议
- 保持与原版本相同的 API 功能

## 许可证

请参考原项目的许可证: https://github.com/Joooook/12306-mcp
