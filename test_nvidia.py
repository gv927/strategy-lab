from openai import OpenAI
import os

client = OpenAI(
  base_url = "https://integrate.api.nvidia.com/v1",
  api_key = "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"
)

try:
    completion = client.chat.completions.create(
      model="openai/gpt-oss-120b",
      messages=[{"role":"user","content":"Hello! Can you help me with a coding task?"}],
      temperature=1,
      top_p=1,
      max_tokens=100,
      stream=False
    )

    reasoning = getattr(completion.choices[0].message, "reasoning_content", None)
    if reasoning:
      print("Reasoning:", reasoning)
    print("Content:", completion.choices[0].message.content)
except Exception as e:
    print(f"Error: {e}")
