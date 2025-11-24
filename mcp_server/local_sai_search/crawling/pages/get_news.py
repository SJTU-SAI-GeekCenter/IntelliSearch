import requests
from bs4 import BeautifulSoup
import re
import os
import json

def parse_sjtu_ai_news_dynamic_new_html(html_content):
    """
    解析上海交通大学人工智能学院“新闻动态”页面的 HTML 内容，
    提取新闻标题、日期和链接。
    
    Args:
        html_content (str): 页面的 HTML 文本内容。
        
    Returns:
        list: 包含新闻信息的字典列表，每个字典包含 'title', 'date', 'link'。
    """
    
    # 使用 BeautifulSoup 解析 HTML
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # 查找所有新闻列表项
    # 根据提供的HTML，新闻项位于 <div class="imgList" id="divresult"> 下的 <ul> 里的 <li>
    news_items = soup.select('div.imgList > ul > li')
    
    news_list = []
    
    for item in news_items:
        # 提取链接 <a> 标签
        anchor_tag = item.find('a', class_='pd')
        
        # 提取标题
        # 标题位于 <div class="h3"> 标签内
        title_tag = item.find('div', class_='h3')
        title = title_tag.get_text(strip=True) if title_tag else 'N/A'
        
        # 提取日期
        # 日期位于 <div class="em"> 标签内的 <em> 标签内
        date_tag = item.find('div', class_='em')
        date = date_tag.find('em').get_text(strip=True) if date_tag and date_tag.find('em') else 'N/A'
        
        # 提取链接
        # 链接是 <a> 标签的 href 属性
        link = anchor_tag.get('href') if anchor_tag else 'N/A'
        
        base_url = 'https://soai.sjtu.edu.cn'
        if link and link.startswith('/'):
            link = base_url + link
            
        news_list.append({
            'title': title,
            'date': date,
            'link': link
        })
        
    return news_list

if __name__ == "__main__":
    # 执行函数并获取 JSON 结果
    final_result = []
    index_list = list(range(1, 2))
    for index in index_list:
        file_path = os.path.join(
            "./crawling", "pages", "notice_raw", f"news_page_{index}.html"
        )
        with open(file_path, "r", encoding="utf-8") as file:
            html_content = file.read()
        json_output = parse_sjtu_ai_news_dynamic_new_html(html_content=html_content)
        final_result.extend(json_output)
    
    with open("./crawling/data/news.json", "w", encoding="utf-8") as file:
        json.dump(final_result, file, ensure_ascii=False, indent=2)
