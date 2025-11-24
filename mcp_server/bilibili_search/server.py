import os
import aiohttp
from datetime import datetime
from tabulate import tabulate
from bilibili_api import video, Credential, search
from mcp.server.fastmcp import FastMCP
from bcut_asr import get_audio_subtitle

# 从环境变量获取认证信息
SESSDATA = os.getenv("sessdata")
BILI_JCT = os.getenv("bili_jct")
BUVID3 = os.getenv("buvid3")

# 初始化 Credential
credential = Credential(sessdata=SESSDATA, bili_jct=BILI_JCT, buvid3=BUVID3)

mcp = FastMCP("bilibili-mcp")


@mcp.tool("search_video", description="搜索bilibili视频")
async def search_video(keyword: str, page: int = 1, page_size: int = 20) -> str:
    """
    keyword: 搜索关键词
    page: 页码，默认1
    page_size: 每页数量，默认20
    """
    search_result = await search.search_by_type(
        keyword,
        search_type=search.SearchObjectType.VIDEO,
        page=page,
        page_size=page_size,
    )

    # 准备表格数据
    table_data = []
    headers = ["发布日期", "标题", "UP主", "时长", "播放量", "点赞数", "类别", "bvid"]

    for video in search_result["result"]:
        # 转换发布时间
        pubdate = datetime.fromtimestamp(video["pubdate"]).strftime("%Y/%m/%d")

        # 将标题转换为Markdown链接格式
        title_link = f"[{video['title']}]({video['arcurl']})"

        table_data.append(
            [
                pubdate,
                title_link,
                video["author"],
                video["duration"],
                video["play"],
                video["like"],
                video["typename"],
                video["bvid"],
            ]
        )

    # 使用 tabulate 生成 Markdown 表格
    return tabulate(table_data, headers=headers, tablefmt="pipe")


@mcp.tool("get_video_subtitle", description="获取bilibili视频的字幕，需提供视频BV号")
async def get_video_subtitle(bvid: str) -> dict:
    """
    bvid: 视频BV号
    """
    v = video.Video(bvid=bvid, credential=credential)
    cid = await v.get_cid(page_index=0)
    info = await v.get_player_info(cid=cid)
    json_files = info["subtitle"]["subtitles"]

    # 过滤查找符合条件的字幕
    target_subtitle = None
    for subtitle in json_files:
        if subtitle["lan"] == "ai-zh" and subtitle["lan_doc"] == "中文（自动生成）":
            target_subtitle = subtitle
            break

    if not target_subtitle:
        url_res = await v.get_download_url(cid=cid)
        # 提取音频URL
        audio_arr = url_res.get("dash", {}).get("audio", [])
        if not audio_arr:
            return "没有找到AI生成的中文字幕"

        # 获取最后一个音频（通常质量最高）
        audio = audio_arr[-1]
        # 选择合适的音频URL
        audio_url = ""
        if ".mcdn.bilivideo.cn" in audio["baseUrl"]:
            audio_url = audio["baseUrl"]
        else:
            backup_url = audio.get("backupUrl", [])
            if backup_url and "upos-sz" in backup_url[0]:
                audio_url = audio["baseUrl"]
            else:
                audio_url = backup_url[0] if backup_url else audio["baseUrl"]

        asr_data = get_audio_subtitle(audio_url)
        return asr_data

    # 确保 URL 有 HTTPS 前缀
    subtitle_url = target_subtitle["subtitle_url"]
    if not subtitle_url.startswith(("http://", "https://")):
        subtitle_url = f"https:{subtitle_url}"

    # 使用 aiohttp 获取字幕内容
    async with aiohttp.ClientSession() as session:
        async with session.get(subtitle_url) as response:
            subtitle_content = await response.json()
            # 提取并拼接所有字幕文本
            if "body" in subtitle_content:
                subtitle_text = "".join(
                    item["content"] for item in subtitle_content["body"]
                )
                return subtitle_text
            else:
                return subtitle_content


@mcp.tool("get_video_info", description="获取bilibili视频信息，需提供视频BV号")
async def get_video_info(bvid: str) -> dict:
    """
    bvid: 视频BV号
    """
    v = video.Video(bvid=bvid, credential=credential)
    info = await v.get_info()
    return info


@mcp.tool(
    "get_media_subtitle", description="获取媒体文件的AI中文字幕，需提供媒体文件URL"
)
async def get_media_subtitle(url: str) -> dict:
    """
    url: 媒体文件URL
    """
    asr_data = get_audio_subtitle(url)
    return asr_data


if __name__ == "__main__":
    mcp.run()
