#!/usr/bin/env node

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js"
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  ErrorCode,
  McpError,
} from "@modelcontextprotocol/sdk/types.js";
import { TOOL } from "./types.js";
import { getBookReviews, getGroupTopicDetail, getGroupTopics, getMovieReviews, getTVReviews, searchBooks, searchMovies } from "./api.js";
import json2md from 'json2md'
import open from 'open'
import dayjs from "dayjs";
import TurndownService from "turndown";
import { z } from "zod";

const server = new McpServer(
  {
    name: "L-Chris/douban-mcp",
    version: "0.2.0",
  }
);

// 搜索图书
server.tool(
  TOOL.SEARCH_BOOK,
  'search books from douban, either by ISBN or by query',
  {
    q: z.string().optional().describe('query string, e.g. "python"'),
    isbn: z.string().optional().describe('ISBN number, e.g. "9787501524044"')
  },
  async (args) => {
    if (!args.isbn && !args.q) {
      throw new McpError(ErrorCode.InvalidParams, "Either q or isbn must be provided")
    }
    const books = await searchBooks(args)
    const text = json2md({
      table: {
        headers: ['publish_date', 'title', 'author', 'rating' ,'id', 'isbn'],
        rows: books.map(_ => ({
          id: _.id || '',
          title: _.title || '',
          author: (_.author || []).join('、'),
          publish_date: _.pubdate,
          isbn: _.isbn13 || '',
          rating: `${_.rating?.average || 0} (${_.rating?.numRaters || 0}人)`
        }))
      }
    })

    return {
      content: [{ type: 'text', text }]
    }
  }
);

// 获取图书长评列表
server.tool(
  TOOL.LIST_BOOK_REVIEWS,
  "list book reviews",
  {
    id: z.string().describe('douban book id, e.g. "1234567890"')
  },
  async (args) => {
    if (!args.id) {
      throw new McpError(ErrorCode.InvalidParams, "douban book id must be provided")
    }

    const reviews = await getBookReviews({ id: args.id })
    const text = json2md({
      table: {
        headers: ['title', 'rating', 'summary', 'id'],
        rows: reviews.reviews.map(_ => ({
          id: _.id,
          title: _.title,
          rating: `${_.rating?.value || 0} (${_.rating?.count || 0}人)`,
          summary: _.abstract
        }))
      }
    })

    return {
      content: [{ type: 'text', text }]
    }
  }
)

// 搜索电影或电视剧
server.tool(
  TOOL.SEARCH_MOVIE,
  'search movies or tvs from douban by query',
  {
    q: z.string().describe('query string, e.g. "python"')
  },
  async (args) => {
    if (!args.q) {
      throw new McpError(ErrorCode.InvalidParams, "q must be provided")
    }

    const movies = await searchMovies(args)
    const text = json2md({
      table: {
        headers: ['title', 'subtitle', 'publish_date', 'rating', 'id'],
        rows: movies.map(_ => ({
          id: _.id,
          title: _.title,
          subtitle: _.card_subtitle,
          publish_date: _.year,
          rating: `${_.rating?.value || '0'} (${_.rating?.count || 0}人)`,
        }))
      }
    })

    return {
      content: [{ type: 'text', text }]
    }
  }
);

// 获取电影长评列表
server.tool(
  TOOL.LIST_MOVIE_REVIEWS,
  "list movie reviews",
  {
    id: z.string().describe('douban movie id, e.g. "1234567890"')
  },
  async (args) => {
    if (!args.id) {
      throw new McpError(ErrorCode.InvalidParams, "douban movie id must be provided")
    }

    const reviews = await getMovieReviews({ id: args.id })
    const text = json2md({
      table: {
        headers: ['title', 'rating', 'summary', 'id'],
        rows: reviews.map(_ => ({
          id: _.id,
          title: _.title,
          rating: `${_.rating?.value || 0} (有用：${_.useful_count || 0}人)`,
          summary: _.abstract
        }))
      }
    })

    return {
      content: [{ type: "text", text }]
    }
  }
)

// 获取电视剧长评列表
server.tool(
  'list-tv-reviews',
  "list tv reviews",
  {
    id: z.string().describe('douban tv id, e.g. "1234567890"')
  },
  async (args) => {
    if (!args.id) {
      throw new McpError(ErrorCode.InvalidParams, "douban tv id must be provided")
    }

    const reviews = await getTVReviews({ id: args.id })
    const text = json2md({
      table: {
        headers: ['title', 'rating', 'summary', 'id'],
        rows: reviews.map(_ => ({
          id: _.id,
          title: _.title,
          rating: `${_.rating?.value || 0} (有用：${_.useful_count || 0}人)`,
          summary: _.abstract
        }))
      }
    })

    return {
      content: [{ type: "text", text }]
    }
  }
)

// 浏览图书详情
server.tool(
  TOOL.BROWSE,
  "open default browser and browse douban book detail",
  {
    id: z.string().describe('douban book id, e.g. "1234567890"')
  },
  async (args) => {
    if (!args.id) {
      throw new McpError(ErrorCode.InvalidParams, "douban book id must be provided")
    }

    await open(`https://book.douban.com/subject/${args.id}/`);

    return {
      content: [{
        type: "text",
        text: `The Douban Book Page has been opened in your default browser`,
      }]
    }
  }
);

// 获取小组话题列表
server.tool(
  TOOL.LIST_GROUP_TOPICS,
  "list group topics",
  {
    id: z.string().optional().describe('douban group id'),
    tags: z.array(z.string()).optional().describe('tags, e.g. ["python"]'),
    from_date: z.string().optional().describe('from date, e.g. "2024-01-01"')
  },
  async (args) => {
    const id = args.id || '732764'
    const topics = await getGroupTopics({ id, tags: args.tags, from_date: args.from_date })

    const text = json2md({
      table: {
        headers: ['publish_date', 'tags', 'title', 'id'],
        rows: topics.map(_ => ({
          id: _.id,
          tags: _.topic_tags.map(_ => _.name).join('、'),
          title: `[${_.title}](${_.url})`,
          publish_date: dayjs(_.create_time).format('YYYY/MM/DD'),
        }))
      }
    })

    return {
      content: [{ type: "text", text }]
    }
  }
);

// 获取小组话题详情
server.tool(
  TOOL.GET_GROUP_TOPIC_DETAIL,
  "get group topic detail",
  {
    id: z.string().describe('douban group topic id, e.g. "1234567890"')
  },
  async (args) => {
    if (!args.id) {
      throw new McpError(ErrorCode.InvalidParams, "douban group topic id must be provided")
    }

    const topic = await getGroupTopicDetail({ id: args.id })
    if (!topic?.id) throw new McpError(ErrorCode.InvalidRequest, "request failed")

    const tService = new TurndownService()
    const text = `title: ${topic.title}
tags: ${topic.topic_tags.map(_ => _.name).join('|')}
content:
${tService.turndown(topic.content)}
`
    return {
      content: [{ type: "text", text }]
    }
  }
);

async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
}

main().catch((error) => {
  console.error("Fatal error in main():", error);
  process.exit(1);
});
