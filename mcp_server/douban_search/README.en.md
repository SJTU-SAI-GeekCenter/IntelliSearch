# Douban MCP Server

[English](README.md) | [中文](README.zh-CN.md)

This MCP server provides functionality to search and interact with Douban (a Chinese social networking service) content including books, movies, and group discussions.

## Features

- Search books by title keywords or ISBN
- View book reviews
- Search movies by title
- View movie reviews
- Browse book details in default browser
- List group topics with filtering options
- View group topic details

## Components

### Tools

- **search-book**
  - Search book info from Douban
  - Input:
    - `isbn` (string, optional): ISBN of the book to fetch
    - `q` (string, optional): Search keyword of the book title

- **list-book-reviews**
  - Get book reviews from Douban
  - Input:
    - `id` (string): Douban book ID

- **search-movie**
  - Search movie info from Douban
  - Input:
    - `q` (string): Search keyword of the movie title

- **list-movie-reviews**
  - Get movie reviews from Douban
  - Input:
    - `id` (string): Douban movie ID

- **browse**
  - Open book detail page in default browser
  - Input:
    - `id` (string): Douban book ID

- **list-group-topics**
  - List topics from Douban groups
  - Input:
    - `id` (string, optional): Douban group ID (defaults to '732764')
    - `tags` (string[], optional): Filter topics by tags
    - `from_date` (string, optional): Filter topics by date (format: "YYYY-MM-DD")

- **get-group-topic-detail**
  - Get details of a specific topic
  - Input:
    - `id` (string): Douban topic ID

## Getting started

1. Clone the repository
2. Install dependencies: `npm install`
3. Build the server: `npm run build`
4. Start the server: `npm start`

### Usage with Desktop App

To integrate this server with a desktop app, add the following to your app's server configuration:

```json
{
  "mcpServers": {
    "douban-mcp": {
      "command": "node",
      "args": [
        "{ABSOLUTE PATH TO FILE HERE}/dist/index.js"
      ],
      "env": {
        "COOKIE": "bid=;ck=;dbcl2=;frodotk_db=;" // get cookie value from website
      }
    }
  }
}
```

## Development

- Build: `npm run build`
- Watch mode: `npm run dev`
- Start: `npm start`
- Test: `npm test`

## Dependencies

- [@modelcontextprotocol/sdk](https://github.com/modelcontextprotocol/sdk): MCP SDK
- [dayjs](https://day.js.org/): Date library
- [json2md](https://github.com/IonicaBizau/json2md): JSON to Markdown converter
- [turndown](https://github.com/domchristie/turndown): HTML to Markdown converter
- [zod](https://github.com/colinhacks/zod): TypeScript-first schema validation

## Resources

- [Douban API Documentation](https://www.doubanapi.com/)

## License

This project is licensed under the MIT License.
