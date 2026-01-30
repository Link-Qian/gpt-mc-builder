import requests
import time
from typing import Optional
from .config_loader import CONFIG


class AIClient:
    def __init__(self):
        self.provider = CONFIG["ai"]["provider"]
        self.api_key = CONFIG["ai"]["api_key"]
        self.model = CONFIG["ai"]["model"]
        self.base_url = CONFIG["ai"]["base_url"]
        self.max_retries = CONFIG["system"]["max_retries"]
        self.retry_delay = CONFIG["system"]["retry_delay"]

    def _build_headers(self):
        """构造请求头（兼容所有 OpenAI 格式 API，包括 DashScope）"""

        # 所有 OpenAI 兼容模式都使用相同的请求头
        if self.provider in ["openai", "deepseek", "moonshot", "fastgpt", "dashscope"]:
            return {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

        # 百度千帆
        if self.provider == "qianfan":
            return {
                "Content-Type": "application/json"
            }

        return {"Content-Type": "application/json"}

    def _build_payload(self, prompt: str):
        """构造请求体（DashScope 兼容模式必须使用 messages）"""

        # OpenAI / DeepSeek / Moonshot / FastGPT / DashScope（兼容模式）
        if self.provider in ["openai", "deepseek", "moonshot", "fastgpt", "dashscope"]:
            return {
                "model": self.model,
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "stream": False
            }

        # 百度千帆
        if self.provider == "qianfan":
            return {
                "model": self.model,
                "messages": [
                    {"role": "user", "content": prompt}
                ]
            }

        return {}

    def ask(self, prompt: str) -> Optional[str]:
        """统一的 AI 调用接口"""

        headers = self._build_headers()
        payload = self._build_payload(prompt)

        for i in range(self.max_retries):
            try:
                print(f"📤 发送请求 (第 {i+1} 次): {prompt[:50]}...")

                response = requests.post(
                    self.base_url,
                    json=payload,
                    headers=headers,
                    timeout=20
                )

                print(f"📥 响应状态码: {response.status_code}")

                if response.status_code == 200:
                    data = response.json()

                    # 所有兼容模式（包括 DashScope）都走 OpenAI 格式
                    if self.provider in ["openai", "deepseek", "moonshot", "fastgpt", "dashscope"]:
                        return data["choices"][0]["message"]["content"].strip()

                    # 百度千帆
                    if self.provider == "qianfan":
                        return data["result"].strip()

                else:
                    print(f"❌ 错误 {response.status_code}: {response.text[:200]}")

            except Exception as e:
                print(f"⚠️ 请求异常: {e}")

            time.sleep(self.retry_delay)

        return None