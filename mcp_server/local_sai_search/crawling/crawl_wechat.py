import logging
import os

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

import json
from weixin_spider import WeixinSpiderWithImages
from typing import Optional

spider_instance: Optional[WeixinSpiderWithImages] = None


def get_spider_instance() -> WeixinSpiderWithImages:
    """获取爬虫实例（单例模式）"""
    global spider_instance
    if spider_instance is None:
        if WeixinSpiderWithImages is None:
            raise RuntimeError("爬虫模块未正确导入")
        try:
            spider_instance = WeixinSpiderWithImages(
                headless=True,  # MCP服务器中使用无头模式
                wait_time=10,
                download_images=True,
            )
            logger.info("爬虫实例初始化成功")
        except Exception as e:
            logger.error(f"爬虫实例初始化失败: {e}")
            raise RuntimeError(f"无法初始化爬虫实例: {e}")

    # 检查驱动是否仍然有效
    if spider_instance.driver is None:
        logger.warning("检测到驱动已失效，重新初始化...")
        try:
            spider_instance.setup_driver(headless=True)
            logger.info("驱动重新初始化成功")
        except Exception as e:
            logger.error(f"驱动重新初始化失败: {e}")
            # 创建新的爬虫实例
            try:
                spider_instance = WeixinSpiderWithImages(
                    headless=True, wait_time=10, download_images=True
                )
                logger.info("创建新的爬虫实例成功")
            except Exception as new_e:
                logger.error(f"创建新爬虫实例失败: {new_e}")
                raise RuntimeError(f"无法创建爬虫实例: {new_e}")

    return spider_instance


def crawl_weixin_article(
    url: str, download_images: bool = True, download_path: str = None
) -> str:
    """
    爬取微信公众号文章内容和图片

    Args:
        url: 微信公众号文章的URL链接
        download_images: 是否下载文章中的图片
        custom_filename: 自定义文件名（可选）

    Returns:
        爬取结果的JSON字符串
    """
    try:
        # 验证URL
        if (
            not url
            or not isinstance(url, str)
            or not url.startswith("https://mp.weixin.qq.com/")
        ):
            raise ValueError("无效的微信文章URL，必须以 https://mp.weixin.qq.com/ 开头")

        logger.info(f"开始爬取文章: {url}")

        # 获取爬虫实例
        spider = get_spider_instance()

        # 设置是否下载图片
        spider.download_images = download_images

        # 爬取文章
        article_data = spider.crawl_article_by_url(url)

        if not article_data:
            raise RuntimeError("无法获取文章内容")

        # 保存文章到文件
        success = spider.save_article_to_file(article_data, download_path)

        if success:
            # 构建返回结果
            result = {
                "status": "success",
                "message": "文章爬取成功",
                "article": {
                    "title": article_data.get("title", ""),
                    "author": article_data.get("author", ""),
                    "publish_time": article_data.get("publish_time", ""),
                    "url": article_data.get("url", ""),
                    "content_length": len(article_data.get("content", "")),
                    "images_count": len(article_data.get("images", [])),
                    "crawl_time": article_data.get("crawl_time", ""),
                },
                "files_saved": {"json": True, "txt": True, "images": download_images},
            }

            if download_images:
                images = article_data.get("images", [])
                success_count = sum(
                    1 for img in images if img.get("download_success", False)
                )
                result["article"][
                    "images_downloaded"
                ] = f"{success_count}/{len(images)}"

            return json.dumps(result, ensure_ascii=False, indent=2)
        else:
            raise RuntimeError("保存文件时出错")

    except Exception as e:
        logger.error(f"爬取文章失败: {e}")
        error_result = {"status": "error", "message": f"爬取失败: {str(e)}", "url": url}
        return json.dumps(error_result, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    account_lists = ["SAI青年号", "上海交通大学人工智能学院"]
    for account_name in account_lists:
        target_dir = os.path.join("./articles", account_name, "article_content")
        os.makedirs(target_dir, exist_ok=True)
        with open(
            os.path.join(target_dir, "..", "all_articles.json"), "r", encoding="utf-8"
        ) as file:
            data = json.load(file)
        for article in data:
            print(article["title"])
            save_dir = os.path.join(target_dir, str(article["id"]))
            crawl_weixin_article(article["link"], download_images=False, download_path=save_dir)
