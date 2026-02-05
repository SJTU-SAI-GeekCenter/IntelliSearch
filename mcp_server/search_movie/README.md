# 豆瓣 MCP 服务器 (Python 版本)

这是一个基于 Python 实现的豆瓣 MCP 服务器,提供了与豆瓣内容交互的功能,包括图书、电影、电视剧和小组讨论等。

## 功能特性

- **书籍**: 搜索、查看图书评论、在浏览器中打开图书详情
- **电影、电视剧**: 搜索、查看评论
- **小组讨论**: 列出话题、查看话题详情

## 工具列表

### 图书相关工具

#### `search_book`
从豆瓣搜索图书信息

**参数:**
- `q` (字符串, 可选): 图书标题的搜索关键词,例如 "python"
- `isbn` (字符串, 可选): 图书的 ISBN 编号,例如 "9787501524044"

**返回:** 格式化的图书搜索结果表格,包含出版日期、标题、作者、评分、ID、ISBN 等信息

#### `list_book_reviews`
获取豆瓣图书评论

**参数:**
- `id` (字符串): 豆瓣图书 ID,例如 "1234567890"

**返回:** 格式化的图书评论列表,包含标题、评分、摘要、ID 等信息

#### `browse`
在默认浏览器中打开图书详情页

**参数:**
- `id` (字符串): 豆瓣图书 ID,例如 "1234567890"

**返回:** 确认消息

### 电影/电视剧相关工具

#### `search_movie`
从豆瓣搜索电影、电视剧信息

**参数:**
- `q` (字符串): 电影、电视剧标题的搜索关键词,例如 "python"

**返回:** 格式化的电影/电视剧搜索结果表格,包含标题、副标题、发布日期、评分、ID 等信息

#### `list_movie_reviews`
获取豆瓣电影评论

**参数:**
- `id` (字符串): 豆瓣电影 ID,例如 "1234567890"

**返回:** 格式化的电影评论列表,包含标题、评分、摘要、ID 等信息

#### `list_tv_reviews`
获取豆瓣电视剧评论

**参数:**
- `id` (字符串): 豆瓣电视剧 ID,例如 "1234567890"

**返回:** 格式化的电视剧评论列表,包含标题、评分、摘要、ID 等信息

### 小组相关工具

#### `list_group_topics`
列出豆瓣小组话题

**参数:**
- `id` (字符串, 可选): 豆瓣小组 ID (默认为 '732764')
- `tags` (字符串数组, 可选): 按标签筛选话题,例如 ["python"]
- `from_date` (字符串, 可选): 按日期筛选话题 (格式: "YYYY-MM-DD"),例如 "2024-01-01"

**返回:** 格式化的小组话题列表,包含发布日期、标签、标题、ID 等信息

#### `get_group_topic_detail`
获取特定话题的详情

**参数:**
- `id` (字符串): 豆瓣话题 ID,例如 "1234567890"

**返回:** 话题详细信息,包含标题、标签、内容等

## 安装

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

部分功能需要从豆瓣网站获取 Cookie。请设置 `COOKIE` 环境变量:

```bash
export COOKIE="bid=;ck=;dbcl2=;frodotk_db=;"
```

**获取 Cookie 的方法:**
1. 在浏览器中打开豆瓣网站并登录
2. 打开浏览器开发者工具 (F12)
3. 切换到 "Network" 标签
4. 刷新页面,点击任意请求
5. 在 "Headers" 中找到 "Cookie" 字段
6. 复制完整的 Cookie 值

## 使用

### 直接运行

```bash
python server.py
```

### 与桌面应用集成

要将此服务器与桌面应用集成,请将以下内容添加到应用的服务器配置中:

```json
{
  "mcpServers": {
    "douban-mcp": {
      "command": "python",
      "args": [
        "/path/to/douban_search/server.py"
      ],
      "env": {
        "COOKIE": "bid=;ck=;dbcl2=;frodotk_db=;"
      }
    }
  }
}
```

## 架构说明

### 主要组件

1. **API 请求函数**
   - `request_frodo_api()`: 通用的 Frodo API 请求函数
   - `get_frodo_sign()`: 生成 API 签名
   - `get_user_agent()`: 获取随机用户代理

2. **工具函数**
   - `format_table()`: 格式化数据为 Markdown 表格

3. **MCP 工具**
   - 所有工具都使用 `@mcp.tool()` 装饰器注册
   - 工具函数返回格式化的字符串或错误信息

### API 签名机制

豆瓣的 Frodo API 使用 HMAC-SHA1 签名:

```python
raw_sign = f"{method}&{url_path}&{date}"
signature = hmac_sha1(raw_sign, secret_key)
```

### Cookie 的作用

部分 API (如小组话题、电影/电视剧评论等) 需要登录才能访问。通过设置 Cookie,服务器可以模拟已登录用户的访问。

## 与 TypeScript 版本的差异

1. **语言**: Python 3.x 替代 TypeScript
2. **MCP SDK**: 使用 `mcp` Python SDK 而非 `@modelcontextprotocol/sdk`
3. **HTTP 请求**: 使用 `requests` 库而非 `fetch`
4. **依赖管理**: 使用 `requirements.txt` 而非 `package.json`
5. **表格格式**: 直接生成 Markdown 表格而非使用 `json2md` 库

## 常见问题

### 1. Cookie 过期

如果遇到认证错误,请重新获取 Cookie 并更新环境变量。

### 2. API 限流

豆瓣 API 可能有访问频率限制。如果遇到限流,请稍后重试。

### 3. 搜索无结果

某些搜索可能需要提供 Cookie 才能返回完整结果。

## 开发

### 测试工具

可以使用 MCP 客户端测试各个工具:

```python
# 测试图书搜索
search_book(q="python")

# 测试小组话题
list_group_topics(id="732764", tags=["编程"])
```

### 添加新工具

1. 使用 `@mcp.tool()` 装饰器定义函数
2. 添加类型提示和文档字符串
3. 调用相应的 API 函数
4. 格式化返回结果

## 资源

- [豆瓣 API 文档](https://www.doubanapi.com/)
- [豆瓣 API 文档](https://goddlts.github.io/douban-api-docs/)
- [MCP 协议规范](https://modelcontextprotocol.io/)

## 许可证

本项目采用 MIT 许可证。
