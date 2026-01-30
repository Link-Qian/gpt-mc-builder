"""
AI Minecraft 助手
作者: Link-Qian
版权: © 2025 Link-Qian. 保留所有权利。
许可证: 本项目基于 MIT License 开源，详见 LICENSE 文件。
"""
import requests
import time
import ast
import socket
import re
import json
from typing import Tuple, Optional

with open('config.json', 'r') as config_file:
    CONFIG = json.load(config_file)

HELP_MESSAGE = (
    "🤖 AI Minecraft 助手\n"
    "💡 使用 \"\\ai <指令>\" 让 AI 帮你建方块、造建筑\n"
    "➡️ 示例：\n"
    "   \\ai 在我面前放一个钻石块\n"
    "   \\ai 以我为中心建一个 5x5 的石头平台\n"
    "   \\ai 显示我的坐标\n"
    "🔒 安全机制：所有代码经过严格检查\n"
    f"🔧 当前模型: {CONFIG['fastgpt']['model']}\n"
    "ℹ️ 输入 \"\\ai help\" 查看帮助"
)
__author__ = "Link-Qian"
__version__ = "1.0.0"
def _patched_receive(self):
    buf = b""
    try:
        while True:
            char = self.socket.recv(1)
            if char == b"\n" or not char:
                break
            buf += char
        return buf.decode("utf-8").rstrip("\n")
    except Exception as e:
        print(f"[MCPI Patch] Receive error: {e}")
        raise

from mcpi import connection
connection.Connection.receive = _patched_receive
class CodeSafetyChecker:
    # 允许的 AST 节点类型（基本控制流和表达式）
    ALLOWED_NODES = {
        'Expression', 'Module', 'Expr', 'Call', 'Load', 'Store',
        'Name', 'Attribute', 'Constant', 'List', 'Tuple',
        'arguments', 'arg', 'keyword', 'BinOp', 'Add', 'Sub', 'Mult', 'Div',
        'For', 'If', 'Compare', 'Eq', 'NotEq', 'Lt', 'Gt', 'LtE', 'GtE',
        'Index', 'Slice', 'Subscript', 'Dict', 'BoolOp', 'And', 'Or',
        'UnaryOp', 'USub', 'UAdd'  # 支持负数如 -1
    }

    # 允许直接使用的变量名（如 range, len）
    ALLOWED_NAMES = {
        'range', 'len', 'print', 'abs', 'min', 'max', 'sum', 'True', 'False', 'None'
    }

    # 允许通过 mc 调用的方法
    ALLOWED_MC_ATTRS = {
        'setBlock', 'setBlocks', 'getBlock', 'getBlockWithData',
        'getTilePos', 'getPos', 'setTilePos', 'setPos', 'getHeight',
        'postToChat', 'getPlayerEntityIds'
    }

    # 允许通过 pos 访问的属性
    ALLOWED_POS_ATTRS = {'x', 'y', 'z'}

    @staticmethod
    def is_safe(code_str: str) -> Tuple[bool, str]:
        code_str = code_str.strip()
        if not code_str:
            return False, "空代码"

        # 防止 Markdown 代码块
        if code_str.startswith("```") or code_str.endswith("```"):
            return False, "包含代码块标记"

        try:
            tree = ast.parse(code_str, mode='exec')
        except SyntaxError as e:
            return False, f"语法错误: {e}"

        for node in ast.walk(tree):
            node_type = type(node).__name__
            if node_type not in CodeSafetyChecker.ALLOWED_NODES:
                return False, f"禁止语法: {node_type}"

            # 检查变量读取（如 pos, mc）
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                if node.id not in CodeSafetyChecker.ALLOWED_NAMES and node.id not in ['mc', 'pos']:
                    return False, f"禁止变量: {node.id}"

            # 检查属性访问：mc.setBlock 或 pos.x
            if isinstance(node, ast.Attribute):
                value = node.value
                attr = node.attr

                # 情况1：mc.xxx
                if isinstance(value, ast.Name) and value.id == 'mc':
                    if attr not in CodeSafetyChecker.ALLOWED_MC_ATTRS:
                        return False, f"禁止方法: mc.{attr}"
                # 情况2：pos.x, pos.y, pos.z
                elif isinstance(value, ast.Name) and value.id == 'pos':
                    if attr not in CodeSafetyChecker.ALLOWED_POS_ATTRS:
                        return False, f"禁止属性: pos.{attr}"
                # 其他属性访问都不允许（如 os.path, sys.exit）
                else:
                    return False, f"禁止属性访问: {ast.dump(value)}.{attr}"

        return True, "安全"
def call_fastgpt(prompt: str) -> Optional[str]:
    """调用 FastGPT 生成代码（带重试机制）"""
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
def extract_python_code(text: str) -> str:
    """从 AI 回复中提取纯 Python 代码"""
    # 优先匹配 ```python ... ```
    match = re.search(r"```python\n?(.*?)\n?```", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    # 其次匹配 ``` ... ```
    match = re.search(r"```(.*?)```", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    # 否则返回全文（假设是纯代码）
    return text.strip()

def generate_minecraft_code(instruction: str) -> str:
    """生成 Minecraft 代码的提示词"""
    prompt = f"""
你是一个 Minecraft 编程助手，使用 mcpi 库控制游戏世界。
根据用户指令生成可执行的Python代码。只输出代码，不解释，不加额外文本。
可用mc.setBlock(x,y,z,id)或mc.setBlocks(x1,y1,z1,x2,y2,z2,id)。玩家位置由pos提供，含pos.x,pos.y,pos.z。
所有坐标基于pos相对计算，如pos.x+1,pos.y,pos.z-1。禁止调用mc.getPos()等位置获取函数。
禁用import,eval,exec,while True,os,sys。
使用安全方块ID：1石头,2草方块,4圆石,9静水,17木头,20玻璃,42铁块,45红砖,49黑曜石,57金块,80雪块。
指令模糊时按最小安全操作执行，如放置一个石头方块。
确保y值合理，避免空中或过远建造。
可对简单命令智能扩展，如“建个平台”视为3x3地面平台，“放个柱子”为3格高柱体。
在输出代码之前自行检查代码的逻辑合理性，保证输出的代码可以正常符合用户要求。
示例：
用户：放个金块
AI：mc.setBlock(pos.x+1, pos.y, pos.z, 57)
用户：建个 3x3 石头平台
AI：mc.setBlocks(pos.x-1, pos.y-1, pos.z-1, pos.x+1, pos.y-1, pos.z+1, 1)
用户指令: {instruction}
""".strip()

    raw_code = call_fastgpt(prompt)
    if not raw_code or "❌" in raw_code or "⚠️" in raw_code or "错误" in raw_code:
        return ""

    # 🔧 提取代码
    clean_code = extract_python_code(raw_code)
    return clean_code
def execute_code_safely(code: str, player_name: str = "玩家"):
    global mc
    if not code.strip():
        mc.postToChat("⚠️ 未生成有效代码。")
        return

    is_safe, reason = CodeSafetyChecker.is_safe(code)
    if not is_safe:
        mc.postToChat(f"🚫 安全拒绝: {reason}")
        print(f"🚫 拒绝执行: {reason}")
        return

    mc.postToChat("⚙️ 正在执行...")
    print("⚙️ 执行代码:")
    print(code)

    # 1. 获取玩家当前位置
    try:
        pos = mc.player.getPos()  # 获取玩家坐标
    except Exception as e:
        mc.postToChat("❌ 无法获取玩家位置，请稍后再试。")
        print(f"获取位置失败: {e}")
        return

    # 2. 将 mc、pos 和安全函数注入执行环境
    safe_globals = {
        "mc": mc,
        "pos": pos,  # 注入 pos 对象，支持 pos.x, pos.y, pos.z
        "range": range,
        "len": len,
        "abs": abs,
        "min": min,
        "max": max,
        "sum": sum,
        "print": lambda x: mc.postToChat(f" {x}")
    }

    try:
        exec(code, safe_globals)
        mc.postToChat("执行成功！")
        print("执行成功")
    except Exception as e:
        error = f"执行失败: {type(e).__name__}: {e}"
        mc.postToChat(error)
        print(error)
def create_minecraft_connection():
    """连接 Minecraft，失败时自动重试（带最大重试次数）"""
    max_retries = 10 
    attempt = 0
    while attempt < max_retries:
        try:
            print(f"正在连接 Minecraft 服务器 {CONFIG['minecraft']['host']}:{CONFIG['minecraft']['port']}... (尝试 {attempt + 1})")
            from mcpi.minecraft import Minecraft
            mc = Minecraft.create(
                address=CONFIG['minecraft']['host'],
                port=CONFIG['minecraft']['port']
            )
            print("🟢 成功连接到 Minecraft 服务器！")
            print(f"作者: {__author__}")
            print(f"版本: {__version__}")
            mc.postToChat("作者:Link-Qian")
            mc.postToChat("版本号:1.0.0")
            mc.postToChat("🤖 AI 助手已启动，输入 \\ai <指令> 使用！")
            return mc
        except Exception as e:
            attempt += 1
            if attempt >= max_retries:
                print("❌达到最大重试次数，程序退出。")
                return None
            print(f"🔴连接失败: {e}，{CONFIG['system']['timeout_retry']} 秒后重试...")
            time.sleep(CONFIG['system']['timeout_retry'])
def main():
    global mc
    mc = create_minecraft_connection()
    if mc is None:
        print("初始化失败，退出程序。")
        return
    print("🚀 AI Minecraft 助手已启动，等待指令...")
    print(HELP_MESSAGE)
    mc.postToChat("✅ AI 助手已就绪，输入 \\ai help 查看帮助。")

    last_command_time = {} 

    while True:
        try:
            events = mc.events.pollChatPosts()
            current_time = time.time()

            for event in events:
                msg = event.message.strip()
                sender_name = "玩家" 

                if not msg.startswith(CONFIG['system']['command_prefix']):
                    continue

                command = msg[len(CONFIG['system']['command_prefix']):].strip()
                if not command:
                    mc.postToChat(f"📌 请输入指令内容。输入 `{CONFIG['system']['command_prefix']} help` 查看帮助。")
                    continue

                if command.lower() == "help":
                    mc.postToChat(HELP_MESSAGE)
                    continue

                if sender_name in last_command_time:
                    if current_time - last_command_time[sender_name] < CONFIG['system']['debounce_time']:
                        mc.postToChat("⏳ 请稍等，正在处理上一个请求...")
                        continue
                last_command_time[sender_name] = current_time

                if len(command) > CONFIG['system']['max_prompt_length']:
                    mc.postToChat("⚠️ 指令过长，请简化。")
                    continue

                mc.postToChat(f"🧠 正在处理: {command}")
                print(f"👤 用户请求: {command}")

                code = generate_minecraft_code(command)
                if code:
                    execute_code_safely(code, sender_name)
                else:
                    mc.postToChat("未能生成有效代码，请重试。")

        except socket.error as e:
            print(f"Minecraft 连接中断: {e}")
            mc = create_minecraft_connection()
            if mc is None:
                time.sleep(CONFIG['system']['timeout_retry'])
        except KeyboardInterrupt:
            print("\n程序被用户中断。")
            break
        except Exception as e:
            print(f"⚠主循环异常: {e}")
            time.sleep(1)

        time.sleep(CONFIG['system']['poll_interval'])

if __name__ == "__main__":

    main()
