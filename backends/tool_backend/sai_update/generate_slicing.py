import json


def convert_to_final_format(save_file_path: str):
    final_data = []
    with open(
        "articles/result.jsonl",
        "r",
        encoding="utf-8",
    ) as file:
        for line in file:
            line_data = json.loads(line)

            final_data.append(
                {
                    "title": line_data["input"]["meta_info"]["title"],
                    "author": line_data["input"]["meta_info"]["author"],
                    "url": line_data["input"]["meta_info"]["url"],
                    "summary": line_data["extracted"]["summary"],
                    "content": line_data["extracted"]["content"],
                    "publish_time": line_data["input"]["meta_info"]["publish_time"],
                    "original_content": line_data["input"]["user_prompt_kwargs"][
                        "raw_content"
                    ],
                }
            )

    with open(save_file_path, "w", encoding="utf-8") as file:
        json.dump(final_data, file, ensure_ascii=False, indent=2)

    return final_data


if __name__ == "__main__":
    final_data = convert_to_final_format(
        "/Users/xiyuanyang/Desktop/Dev/IntelliSearch-v2/articles/articles.json"
    )
    print(f"The Length of the data: {len(final_data)}")
