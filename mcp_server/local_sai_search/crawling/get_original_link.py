import requests
import json
import time
import os
from typing import List
from datetime import datetime
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def get_article_list(
    cookie: str,
    token: str,
    fakeid: str,
    begin: int = 0,
    name: str = None,
    save_dir: str = None,
) -> List:
    """
    获取微信公众号文章列表

    Args:
        cookie: 浏览器cookie
        token: 访问令牌
        fakeid: 公众号ID

    Returns:
        文章列表
    """
    if not name:
        print("Error! Name params should be set!")
        return []

    req_url = "https://mp.weixin.qq.com/cgi-bin/appmsgpublish"
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0"

    # 设置请求参数
    params = {
        "sub": "list",
        "search_field": "null",
        "begin": f"{begin}",
        "count": "10",
        "query": "",
        "fakeid": fakeid,
        "type": "101_1",
        "free_publish_type": "1",
        "sub_action": "list_ex",
        "token": token,
        "lang": "zh_CN",
        "f": "json",
        "ajax": "1",
    }

    # 设置请求头
    headers = {
        "User-Agent": user_agent,
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.5",
        "X-Requested-With": "XMLHttpRequest",
        "Connection": "keep-alive",
        "Referer": f"https://mp.weixin.qq.com/cgi-bin/appmsgtemplate?action=edit&lang=zh_CN&token={token}",
        "Cookie": cookie,
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "Priority": "u=1",
    }

    json_dir = os.path.join(save_dir, "json_origin")
    os.makedirs(json_dir, exist_ok=True)

    try:
        session = requests.Session()
        session.verify = False

        response = session.get(req_url, params=params, headers=headers, timeout=30)
        response.raise_for_status()

        response_text = response.text

        # 处理转义字符
        response_text = response_text.replace("\\\\", "")
        response_text = response_text.replace('\\"', '"')
        response_text = response_text.replace('"{', "{")
        response_text = response_text.replace('}"', "}")

        try:
            data = json.loads(response_text)
            with open(
                f"{json_dir}/{current_count}.json",
                "w",
                encoding="utf-8",
            ) as file:
                json.dump(data, file, indent=4, ensure_ascii=False)
            return data
        except json.JSONDecodeError as e:
            print("Error, found json decode error!")
            with open(f"{json_dir}/{current_count}.json", "w") as file:
                file.write(response_text)

            return response_text

    except Exception as e:
        print(f"Error: {e}")
        return []


if __name__ == "__main__":
    fake_id_dict = {
        "SAI青年号": "Mzk0Nzc0NTY1Mg==",
        "上海交通大学人工智能学院": "MzkwNTY3MjU0Nw==",
    }

    # several input settings
    # you can get cookie and token in the web browser settings
    # 每次浏览器如果提示需要重新登录则需要重新拿到 cookie 值和 token 值
    cookie = "pac_uid=0_sEMmntMniHc5A; omgid=0_sEMmntMniHc5A; _qimei_uuid42=195180e25091005b3fa71adc129d8e09407aebe3dd; _qimei_fingerprint=e9f3042c6ddb5a053710ce11a6cf5ce8; _qimei_h38=716d5d923fa71adc129d8e0902000005b19518; _qimei_q32=eb01843e8f197d8a7b52717727869af1; _qimei_q36=564f065445fbf22410506aa330001011861c; RK=VVfZdFo+42; ptcz=d066eeb9a9be4e0a8e8e1daa4c9364ffc966af03ee2cc48ecf47f651185790cb; wxuin=56391846451967; poc_sid=HI6P72ijMLYY5sNarJAQ1GmzF6NRirZyXKzZ8Z35; ua_id=XV4QKSGwZqaRemHbAAAAAA3IaMBRmY_NleIOY-OwpEo=; xid=4f378bcd3ca5abb6ecfa4dbbaac356d5; mm_lang=zh_CN; markHashId_L=477d402d-3286-478c-844e-afc81483c464; markHashId_D=1e1f837a-c75f-40f3-8096-a6fb65c7c51c; markHashId=2aeef6f4; uuid=b2b34166adac71c20d3a769bd7088492; _clck=1o5rquu%5E2%5Eg0e%5E0%5E2122|1|g0e|0; cert=dLafIh1m_MA9Yu1p0DEt7Xox4GwMG841; data_bizuin=3640112677; bizuin=3640112677; master_user=gh_26e54f1cbbbe; master_sid=WXg3eUpleDUyR2ozNzBkcjJFZ3o5V1hjSThlVGw2MDhLbVNOTW9VM090dUF4b1ZMSXFVaDhqT2pLNEpGQzhsM3pjQWZ4WmxJMmZhU3ZFc1NINmhyMGtTNnRKc0MzcEs3MUo1NmFuSmZIWldNbl9SYVZvT3U4a0NtM0V5RTJrUHhRTTJUOUNrRnhqeUJuSTVp; master_ticket=ab383c0e542c2f01bf46f904b3e6a3ad; data_ticket=GVK1xBfev7wkxV7a3TR3oE9aXAu77LI0z54UPCUq75j1u8h4CMK2/KO3t0/FKSv8; rand_info=CAESIESNgH16ODkWd1vZgns536CpyOZtz2QCqyHxpVfjjQ85; slave_bizuin=3640112677; slave_user=gh_26e54f1cbbbe; slave_sid=VWpGb3VxN09HdUdzMXIxdGxDSGsxSW05bEZTNmowX2FFMVdTdDV6THFXckVHNmtESUx1dXdKcnBDMkJiNWdudzZrRjNuWjQ2TjFzT0x2eTg2c0NzSEZ6c1E3QUxrbXQ2SlVJOGpqRTd5TUUzbGE2ak9PczNiZmpoWllQa1pkY1oybnc4TWt6Sk9ZTlNXa1Z6; _clsk=18set19|1761236203157|2|1|mp.weixin.qq.com/weheat-agent/payload/record"
    token = "1091199122"

    # getting fakeid:
    name = "上海交通大学人工智能学院"
    fakeid = fake_id_dict[name]
    base_dir = os.path.join("./articles", name)
    os.makedirs(base_dir, exist_ok=True)

    current_count = 0
    while True:
        # 防止爬虫速率过快
        time.sleep(3)
        list_data = get_article_list(
            cookie, token, fakeid, begin=current_count, name=name, save_dir=base_dir
        )
        if list_data and type(list_data) is not str:
            article_list = list_data["publish_page"]["publish_list"]
            if not article_list:
                break
        current_count += 10

    print(f"Count: {current_count}")
