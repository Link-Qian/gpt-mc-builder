import time
from mcpi import connection
from .config_loader import CONFIG

__author__ = "Link-Qian"
__version__ = "1.0.1"

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

connection.Connection.receive = _patched_receive

def create_minecraft_connection():
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
