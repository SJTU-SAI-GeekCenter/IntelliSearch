#!/usr/bin/env python3
"""Quick test for Code Backend using OpenAI SDK."""

import os

os.environ['no_proxy'] = 'localhost,127.0.0.1'

from openai import OpenAI

client = OpenAI(
    api_key="sk-intellisearch-dev-001",
    base_url="http://localhost:8002/v1"
)

response = client.chat.completions.create(
    model="intellisearch",
    messages=[{"role": "user", "content": "帮我讲解一下claude skills是什么？"}],
    temperature=0.7,
)

print(response.choices[0].message.content)
print("\n[Full response]:")
print(response.model_dump_json(indent=2))