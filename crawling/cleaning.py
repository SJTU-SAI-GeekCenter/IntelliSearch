import sys
import os
import json
import re

sys.path.append(os.path.join(os.getcwd()))
sys.path.append(os.path.join(os.getcwd(), "agentoolkit"))
from agentoolkit.data_generation import DataGenerationPipeline
from typing import Dict


def load_data():
    data_path = "data/clean_data_pool.json"
    if os.path.exists(data_path):
        with open(data_path, "r", encoding="utf-8") as file:
            data_pool = json.load(file)
            return data_pool

    base_dirs = ["articles/上海交通大学人工智能学院", "articles/SAI青年号"]
    for base_dir in base_dirs:
        article_dir = os.path.join(base_dir, "article_content")
        data_pool = []
        for id in os.listdir(article_dir):
            raw_content_path = os.path.join(article_dir, id, "content.txt")
            meta_info_path = os.path.join(article_dir, id, "meta_info.json")
            with open(meta_info_path, "r", encoding="utf-8") as file:
                meta_info: Dict = json.load(file)
            with open(raw_content_path, "r", encoding="utf-8") as file:
                raw_content = file.read()

            data_pool.append(
                {
                    "user_prompt_kwargs": {"raw_content": raw_content},
                    "system_prompt_kwargs": {},
                    "meta_info": {
                        "title": meta_info.get("title", "Fetching Title Failed"),
                        "author": meta_info.get("author", None),
                        "publish_time": meta_info.get("publish_time", None),
                        "url": meta_info.get("url", None),
                    },
                }
            )

    print(f"Length of the database: {len(data_pool)}")
    with open("./data/clean_data_pool.json", "w", encoding="utf-8") as file:
        json.dump(data_pool, file, ensure_ascii=False, indent=2)
    return data_pool


def extract_urls(text: str) -> list[str]:
    """
    从任意字符串中提取所有网页链接，返回 list[str]
    """
    url_pattern = r"(https?://[^\s\"'<>]+|www\.[^\s\"'<>]+)"

    urls = re.findall(url_pattern, text)
    return urls


def extractor(content: str):
    content_pattern = r"<content>\s*(.*?)\s*</content>"
    summary_pattern = r"<summary>\s*(.*?)\s*</summary>"
    content_match = re.search(content_pattern, content, flags=re.S)
    summary_match = re.search(summary_pattern, content, flags=re.S)
    urls = extract_urls(content)

    content_text = content_match.group(1) if content_match else ""
    summary_text = summary_match.group(1) if summary_match else ""

    return {"content": content_text, "summary": summary_text, "urls": urls}


def main():
    pipeline = DataGenerationPipeline(config_path="config/data_generation.yaml")

    data_pool = load_data()
    results = pipeline.run(
        data_pool=data_pool, concurrency_limit=20, extract_function=extractor
    )

    print(results)


if __name__ == "__main__":
    main()
