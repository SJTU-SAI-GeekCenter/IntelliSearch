import os
import requests
import json
import uuid
from typing import List

# TODO refactor
# and for admin only


def update_memory(conversation_id: str, messages: List[dict]):
    data = {
        "user_id": "memos_user_geekcenter",
        "conversation_id": conversation_id,
        "messages": messages,
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Token {os.environ['MEMOS_API_KEY']}",
    }

    print(f"Adding Messages:\n{json.dumps(messages, ensure_ascii=False, indent=2)}")
    url = f"{os.environ['MEMOS_BASE_URL']}/add/message"
    res = requests.post(url=url, headers=headers, data=json.dumps(data))
    print(f"Result:\n{json.dumps(res.json(), ensure_ascii=False, indent=2)}")


def split_text_into_n_parts(text: str, n: int) -> List[str]:
    length = len(text)
    part_size = length // n
    parts = []

    for i in range(n):
        start = i * part_size
        # 最后一段吃掉剩余内容
        end = None if i == n - 1 else (i + 1) * part_size
        parts.append(text[start:end])

    return parts


if __name__ == "__main__":
    SUTUO_DATA_PATH = "/Users/xiyuanyang/Desktop/Dev/IntelliSearch/mcp_server/local_sai_search/crawling/data/sutuo.md"

    with open(SUTUO_DATA_PATH, "r", encoding="utf-8") as file:
        sutuo_md = file.read()

    conversation_id = str(uuid.uuid4())

    # 先上传用户问题
    update_memory(
        conversation_id=conversation_id,
        messages=[
            {
                "role": "user",
                "content": "上海交通大学人工智能学院的素拓条例是什么？",
            }
        ],
    )

    # 切成四段并依次上传
    parts = split_text_into_n_parts(sutuo_md, 4)

    for idx, part in enumerate(parts, start=1):
        update_memory(
            conversation_id=conversation_id,
            messages=[
                {
                    "role": "assistant",
                    "content": f"（第 {idx}/4 部分）\n{part}",
                }
            ],
        )
