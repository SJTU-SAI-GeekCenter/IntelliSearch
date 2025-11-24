import dayjs from "dayjs"
import crypto from 'crypto'
import { URL } from 'url'
import type { Douban } from "./types.ts"

const apiKey = '0ac44ae016490db2204ce0a042db2916'

// 书籍API
export async function searchBooks(params: {
  q?: string
  isbn?: string
}) {
  if (params.q) {
    return searchByKeyword(params.q)
  }
  if (params.isbn) {
    return searchByISBN(params.isbn)
  }
  return []
}

async function searchByKeyword (q: string) {
  const url = new URL('https://api.douban.com/v2/book/search')
  url.searchParams.set('q', q)
  url.searchParams.set('apikey', apiKey)
  const res: {
    count: number
    start: number
    total: number
    books: Douban.Book[]
  } = await (await fetch(url.toString(), {
    headers: FAKE_HEADERS
  })).json()

  return res?.books ? res.books.map(parseDoubanBook) : []
}

async function searchByISBN (isbn: string) {
  const url = new URL(`https://api.douban.com/v2/book/isbn/${isbn}`)
  url.searchParams.set('apikey', apiKey)
  const res: Douban.Book = await (await fetch(url.toString(), {
    headers: FAKE_HEADERS
  })).json()
  return res?.id ? [parseDoubanBook(res)] : []
}

// 获取图书长评列表
export async function getBookReviews(params: {
  id: string
}) {
  const res: {
    count: number
    start: number
    total: number
    reviews: Douban.BookReview[]
  } = await requestFrodoApi(`/book/${params.id}/reviews`)
  return res
}

// 搜索电影或电视剧API
export async function searchMovies(params: {
  q: string
}) {
  const res = await requestFrodoApi(`/search/movie?q=${params.q}`)
  return res?.items ? res.items.map(_ => _.target) : [];
}

// 获取电影长评列表
export async function getMovieReviews(params: {
  id: string
}) {
  const res = await requestFrodoApi(`/movie/${params.id}/reviews`);
  return res?.reviews ? res.reviews : []
}

// 获取电视剧长评列表
export async function getTVReviews(params: {
  id: string
}) {
  const res = await requestFrodoApi(`/tv/${params.id}/reviews`);
  return res?.reviews ? res.reviews : []
}

// 获取小组话题列表
export async function getGroupTopics(params: {
  id: string
  tags?: string[]
  from_date?: string
}) {
  const res = await requestFrodoApi(`/group/${params.id}/topics`)

  let topics = (res.topics as Douban.Topic[] || []).filter(_ => !_.is_ad)

  if (params.tags) {
    topics = topics.filter(_ => _.topic_tags.some(tag => params.tags?.includes(tag.name)))
  }

  if (params.from_date) {
    topics = topics.filter(_ => dayjs(_.create_time).isAfter(dayjs(params.from_date)))
  }


  return topics
}

// 获取小组话题详情
export async function getGroupTopicDetail(params: {
  id: string
}) {
  const res: Douban.TopicDetail = await requestFrodoApi(`/group/topic/${params.id}`)

  return res
}

const FAKE_HEADERS = {
    'Accept': 'application/json',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
    'accept-encoding': 'gzip, deflate, br, zstd',
    'Cache-Control': 'no-cache',
    'Cookie': '',
    'Pragma': 'no-cache',
    'Priority': 'u=0, i',
    'Sec-Ch-Ua': '"Not/A)Brand";v="8", "Chromium";v="126", "Microsoft Edge";v="126"',
    'Sec-Ch-Ua-Mobile': '?0',
    'Sec-Ch-Ua-Platform': '"Windows"',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-User': '?1',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36 Edg/126.0.0.0'
}

const parseDoubanBook = (_: Douban.Book): Douban.Book => {

  let pubdate = (_.pubdate || '').replace(/年|月/g, '-').replace(/日$/, '')
  if (pubdate) {
    pubdate = dayjs(pubdate).format('YYYY/MM')
  }

  return {
    ..._,
    pubdate
  }
}

const requestFrodoApi = async (url: string) => {
  const fullURL = 'https://frodo.douban.com/api/v2' + url;
  const date = dayjs().format('YYYYMMDD')

  const rParams = {
    os_rom: 'android',
    apiKey: '0dad551ec0f84ed02907ff5c42e8ec70',
    _ts: date,
    _sig: getFrodoSign(fullURL, date),
  };

  const oUrl = new URL(fullURL)

  for (let key in rParams) {
    // @ts-ignore
    oUrl.searchParams.set(key, rParams[key])
  }


  const req = await fetch(oUrl.toString(), {
    headers: {
      'user-agent': getUA(),
      cookie: process.env.COOKIE || ''
    }
  })

  return req.json()
}

const getFrodoSign = (url: string, date: string, method: string = 'GET') => {
  const urlParsed = new URL(url);
  const urlPath = urlParsed.pathname;
  const rawSign = [method.toUpperCase(), encodeURIComponent(urlPath), date].join('&');
  const hmac = crypto.createHmac('sha1', 'bf7dddc7c9cfe6f7');
  hmac.update(rawSign)
  return hmac.digest('base64');
}

const USER_AGENTS = [
  "api-client/1 com.douban.frodo/7.22.0.beta9(231) Android/23 product/Mate 40 vendor/HUAWEI model/Mate 40 brand/HUAWEI  rom/android  network/wifi  platform/AndroidPad",
  "api-client/1 com.douban.frodo/7.18.0(230) Android/22 product/MI 9 vendor/Xiaomi model/MI 9 brand/Android  rom/miui6  network/wifi  platform/mobile nd/1",
  "api-client/1 com.douban.frodo/7.1.0(205) Android/29 product/perseus vendor/Xiaomi model/Mi MIX 3  rom/miui6  network/wifi  platform/mobile nd/1",
  "api-client/1 com.douban.frodo/7.3.0(207) Android/22 product/MI 9 vendor/Xiaomi model/MI 9 brand/Android  rom/miui6  network/wifi platform/mobile nd/1"
]

const getUA = (() => {
  let i = -1
  return () => {
    i += 1
    if (i > 3) i = 0
    return USER_AGENTS[i]
  }
})()