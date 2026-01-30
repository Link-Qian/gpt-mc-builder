from core.mc_connection import create_minecraft_connection
from core.event_handler import start_event_loop

def main():
    mc = create_minecraft_connection()
    if mc is None:
        print("初始化失败，退出程序。")
        return
    start_event_loop(mc)

if __name__ == "__main__":
    main()