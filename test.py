import os
from openai import OpenAI
import logging
logger = logging.getLogger("openai")

logger.addHandler(logging.StreamHandler())

logger.setLevel(logging.DEBUG)

# Initialize client pointing to your local vLLM server
# Defaults to http://localhost:8000/v1
client = OpenAI(
    base_url=os.environ.get("VLLM_HOST", "http://localhost:8000/v1"),
    api_key=os.environ.get("VLLM_API_KEY", "dummy-key-vllm-does-not-require-one"),
)

# Test chat completion
response = client.chat.completions.create(
    model="facebook/opt-125m",  # Must match the model hosted by your server
    messages=[
        {"role": "user", "content": "Why is the sky blue?"}
    ],
    temperature=0.7,
    max_tokens=100
)

print("Server Response:")
print(response.choices[0].message.content)
