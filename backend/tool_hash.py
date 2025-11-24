import difflib
from typing import List, Dict, Any, Optional, Tuple, AsyncGenerator
ToolSchema = Dict[str, Any]

SIMILARITY_THRESHOLD = 0.2

def get_similarity(s1: str, s2: str) -> float:
    """计算两个字符串之间的相似度 (基于 SequenceMatcher)。"""
    return difflib.SequenceMatcher(None, s1, s2).ratio()


def fix_tool_args(
    tools: Dict[str, ToolSchema], tool_args: Dict[str, Any], tool_name: str
) -> Dict[str, Any]:
    """
    尝试智能修复工具调用参数中可能存在的命名不匹配问题。

    Args:
        tools: 包含所有工具 Schema 的字典。
        tool_args: 原始传入的参数字典。
        tool_name: 待调用的工具名称。

    Returns:
        修复后的参数字典，如果无法修复则返回原始字典。
    """
    tools_schema = tools.get(tool_name)

    if tools_schema is None:
        return tool_args

    required_params: List[str] = tools_schema.get("input_schema", {}).get(
        "required", []
    )

    if not required_params or not tool_args:
        return tool_args
    is_required_present = all(param in tool_args for param in required_params)
    if is_required_present:
        return tool_args

    if len(required_params) == 1 and len(tool_args) == 1:
        required_param_name = required_params[0]

        input_param_key = list(tool_args.keys())[0]
        input_param_value = list(tool_args.values())[0]

        if input_param_key != required_param_name:
            print(
                f"[FIX] 尝试将参数 '{input_param_key}' 映射到必需参数 '{required_param_name}'..."
            )

            fixed_args = {required_param_name: input_param_value}
            print(f"[FIX] 修复成功：{tool_args} -> {fixed_args}")
            return fixed_args
    elif len(required_param_name) == len(tool_args):
        pass

    print(f"[INFO] 无法进行智能修复，返回原始参数：{tool_args}")
    return tool_args


def fix_tool_args(
    tools: Dict[str, ToolSchema], tool_args: Dict[str, Any], tool_name: str
) -> Dict[str, Any]:
    """
    尝试智能修复工具调用参数中可能存在的命名不匹配问题。
    """
    tools_schema = tools.get(tool_name)

    if tools_schema is None:
        return tool_args

    # 获取所有期望的参数名 (必填 + 可选)
    all_expected_params: List[str] = list(
        tools_schema.get("input_schema", {}).get("properties", {}).keys()
    )
    # 提取必需的参数列表
    required_params: List[str] = tools_schema.get("input_schema", {}).get(
        "required", []
    )

    if not all_expected_params or not tool_args:
        return tool_args
        
    # 1. 检查是否完全满足要求
    is_required_present = all(param in tool_args for param in required_params)
    if is_required_present:
        # 参数名匹配，无需修复
        return tool_args

    # --- 阶段 2: 简单单参数映射 ---
    if len(required_params) == 1 and len(tool_args) == 1:
        required_param_name = required_params[0]
        input_param_key = list(tool_args.keys())[0]
        input_param_value = list(tool_args.values())[0]

        if input_param_key != required_param_name:
            # 只有在相似度足够高时才进行映射，增加健壮性
            if get_similarity(input_param_key, required_param_name) >= SIMILARITY_THRESHOLD:
                print(
                    f"[FIX] 尝试将参数 '{input_param_key}' 映射到必需参数 '{required_param_name}'..."
                )
                fixed_args = {required_param_name: input_param_value}
                print(f"[FIX] 修复成功：{tool_args} -> {fixed_args}")
                return fixed_args
            else:
                print(f"[INFO] 单参数名称不匹配且相似度不足，无法修复。")

    # --- 阶段 3: 多参数模糊匹配（补充的部分） ---
    
    # 核心逻辑：如果单参数映射失败，或者有多个参数，则进入多参数模糊匹配流程

    fixed_args: Dict[str, Any] = {}
    
    # 追踪已被成功匹配的期望参数（防止重复映射）
    matched_expected_params: set = set()

    # 临时字典，用于存放未能精确匹配的输入参数，等待模糊匹配
    temp_input_args: Dict[str, Any] = {}

    # 3.1 预处理：精确匹配优先
    for input_key, input_value in tool_args.items():
        if input_key in all_expected_params:
            fixed_args[input_key] = input_value
            matched_expected_params.add(input_key)
        else:
            temp_input_args[input_key] = input_value
    
    # 3.2 模糊匹配剩余参数
    
    # 我们将剩余的待匹配输入参数和未使用的期望参数进行匹配
    remaining_input_keys = list(temp_input_args.keys())
    unmatched_expected_params = [p for p in all_expected_params if p not in matched_expected_params]
    
    if remaining_input_keys and unmatched_expected_params:
        print(f"[INFO] 进入多参数模糊匹配模式...")
        
        # 构建可能的匹配对，并计算相似度
        potential_matches: List[Tuple[float, str, str]] = [] # (相似度, 期望参数, 输入参数)
        
        for input_key in remaining_input_keys:
            for expected_param in unmatched_expected_params:
                similarity = get_similarity(input_key, expected_param)
                if similarity >= SIMILARITY_THRESHOLD:
                    potential_matches.append((similarity, expected_param, input_key))

        # 按相似度从高到低排序，优先处理最相似的匹配
        potential_matches.sort(key=lambda x: x[0], reverse=True)

        # 遍历排序后的匹配，进行最终修复
        used_input_keys = set()
        
        for similarity, expected_param, input_key in potential_matches:
            # 确保该输入键和期望参数都没有被使用过
            if expected_param not in matched_expected_params and input_key not in used_input_keys:
                
                fixed_args[expected_param] = temp_input_args[input_key]
                matched_expected_params.add(expected_param)
                used_input_keys.add(input_key)
                print(f"[FUZZY FIX] 键 '{input_key}' (相似度: {similarity:.2f}) 修复为 '{expected_param}'。")
                
    # 3.3 最终检查和返回
    
    # 检查必需参数是否仍然缺失
    is_required_fixed = all(param in fixed_args for param in required_params)
    
    if is_required_fixed:
        print(f"[SUCCESS] 参数修复完成，所有必需参数已找到。")
        return fixed_args
    else:
        # 如果修复后仍不完整，或者没有进入修复逻辑，则打印信息并返回原始参数
        print(f"[INFO] 无法进行智能修复，或修复后仍缺失必需参数。返回原始参数：{tool_args}")
        return tool_args

def fix_tool_args_similarity(
    tools: Dict[str, Any], tool_args: Dict[str, Any], tool_name: str
) -> Dict[str, Any]:
    """
    尝试使用字符串相似度智能修复工具调用参数中的命名不匹配问题，支持多个参数。

    Args:
        tools: 包含所有工具 Schema 的字典。
        tool_args: 原始传入的参数字典。
        tool_name: 待调用的工具名称。

    Returns:
        修复后的参数字典。
    """
    tools_schema = tools.get(tool_name)
    if tools_schema is None:
        print(f"[ERROR] Tool '{tool_name}' not found.")
        return tool_args

    required_params: List[str] = tools_schema.get("input_schema", {}).get(
        "required", []
    )

    # 获取所有期望的参数名 (必填 + 可选)
    all_expected_params: List[str] = list(
        tools_schema.get("input_schema", {}).get("properties", {}).keys()
    )

    if not all_expected_params or not tool_args:
        return tool_args

    fixed_args: Dict[str, Any] = {}
    remaining_input_keys = list(tool_args.keys())

    print(f"[INFO] 期望参数: {all_expected_params}")
    print(f"[INFO] 原始输入: {tool_args}")


    for input_key, input_value in tool_args.items():
        if input_key in all_expected_params:
            fixed_args[input_key] = input_value
            print(f"[MATCH] 键 '{input_key}' 精确匹配，已接受。")

        else:
            # --- 阶段 2: 相似度匹配 ---
            best_match: Optional[str] = None
            max_similarity: float = 0.0

            # 找到与当前输入键最相似的期望参数名
            for expected_param in all_expected_params:
                # 跳过已经被成功匹配的参数，避免多对一的错误匹配
                if expected_param in fixed_args:
                    continue

                similarity = get_similarity(input_key, expected_param)

                # 设定相似度阈值 (例如 0.7)
                if similarity > 0.7 and similarity > max_similarity:
                    max_similarity = similarity
                    best_match = expected_param

            # 找到最佳匹配，并且这个最佳匹配还没有被使用
            if best_match is not None:
                # 检查这个最佳匹配是否已经被 fixed_args 中的其他键使用
                # 这一步是为了避免两个写错的键都映射到同一个目标键
                if best_match not in fixed_args.keys():

                    # 修复：将输入键映射到最相似的期望参数名
                    fixed_args[best_match] = input_value
                    print(
                        f"[FIXED] 键 '{input_key}' ({max_similarity:.2f}) 修复为 '{best_match}'。"
                    )
                else:
                    print(
                        f"[WARN] 键 '{input_key}' 最佳匹配为 '{best_match}'，但该参数已被其他输入键占用。跳过修复。"
                    )
            else:
                # 没有找到足够相似的匹配，作为冗余参数丢弃或保留
                print(f"[SKIP] 键 '{input_key}' 未找到足够相似的匹配。已忽略。")
                # 如果是宽松模式，可以保留在 fixed_args 中：
                # fixed_args[input_key] = input_value

    # --- 阶段 3: 检查缺失的必需参数 ---
    for required_param in required_params:
        if required_param not in fixed_args:
            print(f"[ERROR] 必需参数 '{required_param}' 缺失，无法继续调用。")
            # 实际应用中，这里应该抛出异常或返回错误状态
            # 为演示目的，我们返回不完整的 fixed_args

    print("\n--- 修复后的参数字典 ---")
    return fixed_args

