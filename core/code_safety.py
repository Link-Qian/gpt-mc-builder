import ast
from typing import Tuple

class CodeSafetyChecker:
    """
    Minecraft 建筑专用安全检查器（V3.0）
    - 允许所有常见数学运算（包括 FloorDiv、Mod、Pow）
    - 允许任意变量名（cx、width、i 等）
    - 严格限制对象访问（只允许 mc 和 pos）
    - 禁止 import / exec / eval / open / os / sys
    - 禁止函数定义 / 类定义
    """

    ALLOWED_NODES = {
        'Module', 'Expr', 'Assign',

        # 表达式
        'BinOp', 'UnaryOp', 'BoolOp',
        'Add', 'Sub', 'Mult', 'Div', 'FloorDiv', 'Mod', 'Pow',
        'USub', 'UAdd', 'And', 'Or',

        # 值
        'Name', 'Constant', 'Tuple', 'List', 'Dict',

        # 控制结构
        'For', 'If', 'Compare',
        'Eq', 'NotEq', 'Lt', 'Gt', 'LtE', 'GtE',

        # 下标
        'Subscript', 'Index', 'Slice',

        # 调用
        'Call', 'keyword',

        # 加载方式
        'Load', 'Store',

        # 属性访问
        'Attribute'
    }

    ALLOWED_MC_ATTRS = {
        'setBlock', 'setBlocks',
        'getBlock', 'getBlockWithData',
        'getTilePos', 'getPos',
        'setTilePos', 'setPos',
        'getHeight', 'postToChat',
        'getPlayerEntityIds'
    }

    ALLOWED_POS_ATTRS = {'x', 'y', 'z'}

    @staticmethod
    def is_safe(code_str: str) -> Tuple[bool, str]:
        code_str = code_str.strip()
        if not code_str:
            return False, "空代码"

        if code_str.startswith("```") or code_str.endswith("```"):
            return False, "包含代码块标记"

        try:
            tree = ast.parse(code_str, mode='exec')
        except SyntaxError as e:
            return False, f"语法错误: {e}"

        for node in ast.walk(tree):
            node_type = type(node).__name__

            # 禁止函数定义 / 类定义
            if node_type in ["FunctionDef", "AsyncFunctionDef", "ClassDef"]:
                return False, f"禁止定义函数或类: {node_type}"

            # 检查节点类型
            if node_type not in CodeSafetyChecker.ALLOWED_NODES:
                return False, f"禁止语法: {node_type}"

            # 检查属性访问
            if isinstance(node, ast.Attribute):
                value = node.value
                attr = node.attr

                # mc.xxx
                if isinstance(value, ast.Name) and value.id == 'mc':
                    if attr not in CodeSafetyChecker.ALLOWED_MC_ATTRS:
                        return False, f"禁止方法: mc.{attr}"

                # pos.xxx
                elif isinstance(value, ast.Name) and value.id == 'pos':
                    if attr not in CodeSafetyChecker.ALLOWED_POS_ATTRS:
                        return False, f"禁止属性: pos.{attr}"

                else:
                    return False, f"禁止属性访问: {ast.dump(value)}.{attr}"

            # 禁止危险函数
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    if node.func.id in ["eval", "exec", "open", "compile"]:
                        return False, f"禁止函数: {node.func.id}"

                if isinstance(node.func, ast.Attribute):
                    if isinstance(node.func.value, ast.Name):
                        if node.func.value.id in ["os", "sys"]:
                            return False, f"禁止模块调用: {node.func.value.id}"

        return True, "安全"