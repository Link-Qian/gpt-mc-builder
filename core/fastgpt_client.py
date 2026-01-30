import time
import requests
from typing import Optional
from .config_loader import CONFIG

def call_fastgpt(prompt: str) -> Optional[str]:
    headers = {
        "Authorization": f"Bearer {CONFIG['fastgpt']['api_key']}",
        "Content-Type": "application/json"
    }

    data = {
        "model": CONFIG['fastgpt']['model'],
        "messages": [{"role": "user", "content": prompt}],
        "stream": False
    }
    if CONFIG['fastgpt'].get('app_id'):
        data['appId'] = CONFIG['fastgpt']['app_id']

    for i in range(CONFIG['system']['max_retries']):
        try:
            print(f"📤 发送请求 (第 {i+1} 次): {prompt[:50]}...")
            response = requests.post(
                CONFIG['fastgpt']['url'],
                json=data,
                headers=headers,
                timeout=20
            )
            print(f"📥 响应状态码: {response.status_code}")

            if response.status_code == 200:
                result = response.json()
                content = result["choices"][0]["message"]["content"].strip()
                print(f"💡 AI 返回:\n{content}")
                return content
            elif response.status_code == 401:
                error = "❌ 授权失败：API Key 错误"
                print(error)
                return error
            elif response.status_code == 404:
                error = "❌ 接口未找到：检查 URL 是否正确"
                print(error)
                return error
            else:
                error = f" 错误 {response.status_code}: {response.text[:100]}"
                print(error)

        except requests.exceptions.ConnectionError:
            error = "❌ 无法连接、，请检查服务是否运行"
            print(error)
        except requests.exceptions.Timeout:
            print(f"⏳ 第 {i+1} 次请求超时，{CONFIG['system']['retry_delay']} 秒后重试...")
        except Exception as e:
            error = f"⚠️ 请求异常: {str(e)}"
            print(error)

        if i < CONFIG['system']['max_retries'] - 1:
            time.sleep(CONFIG['system']['retry_delay'])

    return "❌ AI 请求失败：已达最大重试次数"
