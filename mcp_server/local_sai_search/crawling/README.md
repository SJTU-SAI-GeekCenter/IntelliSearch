# 微信公众号爬虫指南

## Dependencies

- 安装相关依赖库
- 需要安装 chrome 和 chromedriver 并写入环境变量（必须）

## Workflow

- 浏览器登录得到 token 和 cookie 等认证信息（需要手动抓包完成）
- 使用查询公众号文章的 API 查询得到特定公众号的 fakeid 并且得到公众号文章列表的详细信息
    - 代码：`get_original_link.py`
- 从爬虫得到的 json 数据清洗得到**特定公众号的所有历史文章信息、作者、摘要、时间**等信息
    - 代码：`extract_info.py`
- 利用链接实现二次爬虫，利用 chromedriver 实现从链接得到特定文章的文字内容和图片内容
    - 代码：`crawl_wechat.py`

## 数据

```data
.
├── articles
│   ├── SAI青年号
│   │   ├── all_articles.json
│   │   ├── article_content
│   │   │   ├── 2247485772
│   │   │   │   ├── content.txt
│   │   │   │   └── meta_info.json
│   │   │   └── 2247486657
│   │   │       ├── content.txt
│   │   │       └── meta_info.json
│   │   └── json_origin
│   │       ├── 0.json
│   │       ├── 100.json
│   │       ├── 10.json
│   │       ├── 110.json
│   │       └── 90.json
```

每一个 articles 下面的文件夹代表公众号的详细信息，其中 `json_origin` 是第一次爬虫得到的原始接口数据，在经过数据清洗和整理后得到的有用数据是 `all_articles.json`。`article_content` 文件夹下存储每一篇推文的具体内容，文件夹名是推文具有的唯一的推文 id 号，内部文件有 `meta_info.json`（存储一些额外的元数据）和 `content.txt`（公众号的文字数据）