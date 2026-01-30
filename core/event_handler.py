import time
import socket
from .config_loader import CONFIG
from .code_generator import generate_minecraft_code
from .executor import execute_code_safely

HELP_MESSAGE = (
    "🤖 AI Minecraft 助手\n"
    "💡 使用 \"\\ai <指令>\" 让 AI 帮你建方块、造建筑\n"
    "➡️ 示例：\n"
    "   \\ai 在我面前放一个钻石块\n"
    "   \\ai 以我为中心建一个 5x5 的石头平台\n"
    "   \\ai 显示我的坐标\n"
    "🔒 安全机制：所有代码经过严格检查\n"
    f"🔧 当前模型: {CONFIG['ai']['model']}\n"
    "ℹ️ 输入 \"\\ai help\" 查看帮助"
)

def start_event_loop(mc):
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
                    execute_code_safely(code, mc, sender_name)
                else:
                    mc.postToChat("未能生成有效代码，请重试。")

        except socket.error as e:
            print(f"Minecraft 连接中断: {e}")
            from .mc_connection import create_minecraft_connection
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
