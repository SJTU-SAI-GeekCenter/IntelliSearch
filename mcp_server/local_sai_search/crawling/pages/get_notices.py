import json
import os
from bs4 import BeautifulSoup


def extract_articles_to_json(html_content, base_url="https://soai.sjtu.edu.cn"):
    """
    从 HTML 内容中提取文章信息（链接、标题、时间）并生成 JSON 格式。

    Args:
        html_content (str): 爬取到的 HTML 字符串。
        base_url (str): 网站的基础 URL，用于拼接相对链接。

    Returns:
        str: 包含文章信息的 JSON 字符串。
    """
    # 1. 初始化 BeautifulSoup 解析器
    soup = BeautifulSoup(html_content, "html.parser")

    # 2. 定位到文章列表容器
    # 列表在 <div class="noticeList" id="divresult"> 内部
    notice_list_container = soup.find("div", class_="noticeList")

    if not notice_list_container:
        return json.dumps(
            {"error": "未找到通知公告列表容器"}, ensure_ascii=False, indent=4
        )

    articles = []

    # 3. 遍历列表中的每个文章项 <li>
    for li_tag in notice_list_container.find_all("li"):
        a_tag = li_tag.find("a")

        # 确保找到 <a> 标签
        if a_tag and "href" in a_tag.attrs:
            # 提取链接
            relative_link = a_tag["href"].strip()
            # 拼接绝对链接。如果链接已经是 http/https 开头，则不再拼接 base_url
            if relative_link.startswith("http"):
                full_link = relative_link
            else:
                full_link = base_url + relative_link

            # 提取标题，标题在 <div class="h3"> 中
            title_tag = a_tag.find("div", class_="h3")
            title = title_tag.text.strip() if title_tag else "无标题"

            # 提取发布时间，时间在 <em> 中
            time_tag = a_tag.find("em")
            publish_time = time_tag.text.strip() if time_tag else "无时间"

            # 存储提取到的信息
            articles.append(
                {"link": full_link, "title": title, "publish_time": publish_time}
            )

    # 4. 将结果列表转换为 JSON 格式的字符串，设置 ensure_ascii=False 以正确显示中文
    json_database = json.dumps(articles, ensure_ascii=False, indent=4)
    return articles


if __name__ == "__main__":
    # 执行函数并获取 JSON 结果
    final_result = []
    index_list = list(range(1, 5))
    for index in index_list:
        file_path = os.path.join(
            "./crawling", "pages", "notice_raw", f"tzgg_page_{index}.html"
        )
        with open(file_path, "r", encoding="utf-8") as file:
            html_content = file.read()
        json_output = extract_articles_to_json(html_content=html_content)
        final_result.extend(json_output)
    
    with open("./crawling/data/notices.json", "w", encoding="utf-8") as file:
        json.dump(final_result, file, ensure_ascii=False, indent=2)
