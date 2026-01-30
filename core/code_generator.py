import re
from pathlib import Path
from .ai_client import AIClient

BASE_DIR = Path(__file__).resolve().parents[1]
PROMPT_PATH = BASE_DIR / "prompts" / "minecraft_prompt.txt"

ai = AIClient()


def extract_python_code(text: str) -> str:
    """
    从大模型返回的文本中提取纯 Python 代码：
    1. 优先匹配 ```python ... ```
    2. 其次匹配 ``` ... ```
    3. 否则认为整段就是代码
    """
    match = re.search(r"```python\n?(.*?)\n?```", text, re.DOTALL)
    if match:
        return match.group(1).strip()

    match = re.search(r"```(.*?)```", text, re.DOTALL)
    if match:
        return match.group(1).strip()

    return text.strip()

def load_prompt_template() -> str:
    """
    从 prompts/minecraft_prompt.txt 读取提示词模板。
    模板里包含 {instruction} 占位符，用来插入用户指令。
    """
    with open(PROMPT_PATH, "r", encoding="utf-8") as f:
        return f.read()
def generate_minecraft_code(instruction: str) -> str:
    """
    核心函数：
    1. 读取提示词模板
    2. 把用户指令填充进模板
    3. 调用通用 AI 客户端（AIClient）
    4. 从返回内容中提取 Python 代码
    """
    template = load_prompt_template()

    prompt = template.format(instruction=instruction)

    raw = ai.ask(prompt)

    if not raw:
        return ""
    return extract_python_code(raw)
