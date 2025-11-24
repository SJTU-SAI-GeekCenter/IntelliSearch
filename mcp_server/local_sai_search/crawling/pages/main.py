# crawling tzgg
import requests
import os

def crawl_tzgg_pages(base_url, page_indices, output_dir="./crawling/pages/notice_raw/"):
    """
    爬取指定页码的通知公告页面，并将 HTML 内容存储到本地文件。

    Args:
        base_url (str): 基础 URL (例如: "https://soai.sjtu.edu.cn/cn/list/tzgg/")。
        page_indices (list): 需要爬取的页码列表 (例如: [1, 2, 3, 4])。
        output_dir (str): 存储 HTML 文件的目录名。
    """
    # 确保输出目录存在
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"创建目录: {output_dir}")

    for index in page_indices:
        url = base_url + str(index)
        print(url)
        file_name = f"news_page_{index}.html"
        file_path = os.path.join(output_dir, file_name)
        
        print(f"正在爬取: {url}...")
        
        try:
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                response.encoding = response.apparent_encoding
                html_content = response.text
                
                # 将内容写入文件
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                
                print(f"成功保存到: {file_path}")
            else:
                print(f"请求失败，状态码: {response.status_code}，URL: {url}")
                
        except requests.exceptions.RequestException as e:
            print(f"爬取 {url} 时发生错误: {e}")

if __name__ == "__main__":
    target_url = "https://soai.sjtu.edu.cn/cn/news/xwdt#page="
    index_list = list(range(1, 10)) 
    
    crawl_tzgg_pages(target_url, index_list)
