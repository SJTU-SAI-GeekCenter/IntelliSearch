# 豆瓣 MCP 服务器

[English](README.md) | [中文](README.zh-CN.md)

这个 MCP 服务器提供了与豆瓣内容交互的功能，包括图书、电影、电视剧和小组讨论等。

## 功能特性

- 书籍：搜索、查看图书评论
- 电影、电视剧：搜索、查看评论
- 小组讨论：列出话题、查看话题详情

## 组件

### 工具

- **search-book**
  - 从豆瓣搜索图书信息
  - 输入参数:
    - `isbn` (字符串, 可选): 图书的 ISBN 编号
    - `q` (字符串, 可选): 图书标题的搜索关键词

- **list-book-reviews**
  - 获取豆瓣图书评论
  - 输入参数:
    - `id` (字符串): 豆瓣图书 ID

- **search-movie**
  - 从豆瓣搜索电影、电视剧信息
  - 输入参数:
    - `q` (字符串): 电影、电视剧标题的搜索关键词

- **list-movie-reviews**
  - 获取豆瓣电影评论
  - 输入参数:
    - `id` (字符串): 豆瓣电影 ID

- **list-tv-reviews**
  - 获取豆瓣电视剧评论
  - 输入参数:
    - `id` (字符串): 豆瓣电视剧 ID

- **browse**
  - 在默认浏览器中打开图书详情页
  - 输入参数:
    - `id` (字符串): 豆瓣图书 ID

- **list-group-topics**
  - 列出豆瓣小组话题
  - 输入参数:
    - `id` (字符串, 可选): 豆瓣小组 ID (默认为 '732764')
    - `tags` (字符串数组, 可选): 按标签筛选话题
    - `from_date` (字符串, 可选): 按日期筛选话题 (格式: "YYYY-MM-DD")

- **get-group-topic-detail**
  - 获取特定话题的详情
  - 输入参数:
    - `id` (字符串): 豆瓣话题 ID

## 开始使用

1. 克隆仓库
2. 安装依赖: `npm install`
3. 构建服务器: `npm run build`
4. 启动服务器: `npm start`

### 与桌面应用集成

要将此服务器与桌面应用集成，请将以下内容添加到应用的服务器配置中，部分API需要用到COOKIE，请自行获取。:

```json
{
  "mcpServers": {
    "douban-mcp": {
      "command": "node",
      "args": [
        "{文件的绝对路径}/dist/index.js"
      ],
      "env": {
        "COOKIE": "bid=;ck=;dbcl2=;frodotk_db=;" // 从网站获取 cookie 值
      }
    }
  }
}
```

## 开发

- 构建: `npm run build`
- 监视模式: `npm run dev`
- 启动: `npm start`
- 测试: `npm test`

## 依赖项

- [@modelcontextprotocol/sdk](https://github.com/modelcontextprotocol/sdk): MCP SDK
- [dayjs](https://day.js.org/): 日期库
- [json2md](https://github.com/IonicaBizau/json2md): JSON 转 Markdown 转换器
- [turndown](https://github.com/domchristie/turndown): HTML 转 Markdown 转换器
- [zod](https://github.com/colinhacks/zod): TypeScript 优先的模式验证

## 资源

- [豆瓣 API 文档](https://www.doubanapi.com/)
- [豆瓣 API 文档](https://goddlts.github.io/douban-api-docs/)

## 许可证

本项目采用 MIT 许可证。