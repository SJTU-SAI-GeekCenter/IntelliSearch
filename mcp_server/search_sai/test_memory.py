import os
import sys
import uuid
import json
import requests

# Add parent directory to path to import config_loader
sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))
import config.config_loader as config_loader

# Load environment variables from config.yaml
config_loader.config


def query_memory(query: str, conversation_id: str = None):
    if not conversation_id:
        conversation_id = str(uuid.uuid4())

    data = {
        "query": query,
        "user_id": "memos_user_geekcenter",
        "conversation_id": conversation_id,
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Token {os.environ['MEMOS_API_KEY']}",
    }
    url = f"{os.environ['MEMOS_BASE_URL']}/search/memory"
    res = requests.post(url=url, headers=headers, data=json.dumps(data))
    print(f"Result:\n{json.dumps(res.json(), ensure_ascii=False, indent=2)}")

if __name__ == "__main__":
    query_memory("上海交通大学 人工智能学院 素拓")
