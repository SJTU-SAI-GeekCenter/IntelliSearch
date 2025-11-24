import json
import os
from datetime import datetime
from typing import List, Dict, Any
from tqdm import tqdm


def get_articles(data: dict) -> List[Dict[str, Any]]:
    """
    从单个数据文件中提取文章信息

    Args:
        data: 包含文章数据的字典

    Returns:
        文章信息列表
    """
    articles = []

    # 检查数据结构是否存在
    if "publish_page" not in data or "publish_list" not in data["publish_page"]:
        print("警告: 数据格式不正确，缺少 publish_page 或 publish_list")
        return articles

    publish_list = data["publish_page"]["publish_list"]

    for publish in publish_list:
        # 检查 publish_info 和 appmsg_info 是否存在
        if (
            "publish_info" in publish
            and "appmsg_info" in publish["publish_info"]
            and len(publish["publish_info"]["appmsg_info"]) > 0
        ):

            publish_info = publish["publish_info"]["appmsgex"][0]

            # 提取文章信息
            article = {
                "title": publish_info.get("title", ""),
                "id": publish_info.get("appmsgid", -1),
                "link": publish_info.get("link", ""),
                "update_time": datetime.fromtimestamp(
                    publish_info.get("update_time", 0)
                ).strftime("%Y-%m-%d %H:%M:%S"),
                "author": publish_info.get("author_name", ""),
                "digest": publish_info.get("digest", ""),
                "cover_url": publish_info.get("cover_url", ""),
            }
            articles.append(article)

    return articles


def merge_and_save_articles(
    target_dir: str = "./result", output_file: str = "merged_articles.json"
):
    """
    合并多个JSON文件中的文章数据并保存

    Args:
        target_dir: 包含JSON文件的目录
        output_file: 输出文件名
    """
    all_articles = []

    # 获取文件列表并按文件名升序排列
    try:
        files = [int(f[:-5]) for f in os.listdir(target_dir) if f.endswith(".json")]
        files.sort()
        for file_index in tqdm(files, total=len(files)):
            filename = f"{file_index}.json"
            file_path = os.path.join(target_dir, filename)

            try:
                with open(file_path, "r", encoding="utf-8") as file:
                    data = json.load(file)
                    articles = get_articles(data)
                    all_articles.extend(articles)

            except json.JSONDecodeError as e:
                print(f"错误: 文件 {filename} JSON格式错误 - {e}")
            except Exception as e:
                print(f"错误: 处理文件 {filename} 时发生错误 - {e}")

        # 保存合并后的数据
        output_path = os.path.join(target_dir, "..", output_file)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(
                all_articles, f, ensure_ascii=False, indent=2, separators=(",", ": ")
            )

        print(f"\n合并完成! 总共 {len(all_articles)} 篇文章")

    except FileNotFoundError:
        print(f"错误: 目录 {target_dir} 不存在")
    except Exception as e:
        print(f"错误: 处理过程中发生未知错误 - {e}")


if __name__ == "__main__":
    account_lists = ["SAI青年号","上海交通大学人工智能学院"]
    for account_name in account_lists:
        target_dir = os.path.join("./articles", account_name, "json_origin")
        merge_and_save_articles(target_dir, "all_articles.json")
