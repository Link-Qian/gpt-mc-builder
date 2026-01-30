from typing import Any
from .code_safety import CodeSafetyChecker

def execute_code_safely(code: str, mc: Any, player_name: str = "玩家"):
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

    try:
        pos = mc.player.getPos()
    except Exception as e:
        mc.postToChat("❌ 无法获取玩家位置，请稍后再试。")
        print(f"获取位置失败: {e}")
        return

    safe_globals = {
        "mc": mc,
        "pos": pos,
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
