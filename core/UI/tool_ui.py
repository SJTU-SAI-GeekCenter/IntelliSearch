"""
Tool UI Manager for displaying MCP tool calls with styled output.

This module provides a singleton manager for displaying tool execution
information with a consistent visual style across the application.
"""

import json
import time
import random
from typing import Optional, Dict, Any
from rich.text import Text
from rich.panel import Panel
from rich.table import Table
from rich.style import Style
from core.UI.live import live, start_live
from core.UI.console import console
from .theme import ThemeColors
from .status_manager import get_status_manager


class ToolUIManager:
    """
    Singleton manager for displaying tool calls with styled UI.

    This class provides a centralized way to display tool execution
    information throughout the application.
    """

    _instance: Optional["ToolUIManager"] = None
    _enabled: bool = True
    _last_dynamic_msg_ts: float = 0.0
    _last_dynamic_msg: str = ""

    _dynamic_messages = [
        "在宣怀大道上逆风骑车，试图跑赢校车...",
        "在思源湖边发呆，顺便数了数第 13 只鸽子...",
        "在电院群楼的实验室里，和 Bug 彻夜长谈...",
        "在学生事务中心刷脸，结果系统说我长得太学术了...",
        "在石楠花丛旁屏住呼吸，火速通过物理攻击区...",
        "在11号线交大站的挤压中，艰难地保持连接...",
        "在东下院后排疯狂重连 jAccount，试图签个到...",
        "在仰思坪躺平，思考百卅校庆到底有没有假放...",
        "在鹿苑附近蹲守，看哪只小鹿今天又要越狱...",
        "在涵泽湖畔看黑天鹅吵架，逻辑架构重组中...",
        "在南体看台吹风，试图让绩点焦虑归0...",
        "在主图的中庭里，进行一场无声的头脑风暴...",
        "在物理实验楼里，等待一个不一定会出的结果...",
        "在包图的考研气氛组里，机械地整理笔记...",
        "在船建水池旁观察波浪，顺便同步了一下数据...",
        "在玉兰苑门口排队，盯着阿姨奶茶的进度条...",
        "在北区外卖柜前徘徊，寻找那个失踪的工位伴侣...",
        "在西70快递站的包裹堆里，进行深度优先搜索...",
        "在绕过西区那个拆了又盖的脚手架，寻找近路...",
        "在菁菁堂前排队，打听今晚是不是有重磅演出...",
        "在淮扬快餐附近感受碳水的召唤，检索中...",
        "在研究生食堂里，思考算法逻辑...",
        "在一餐教工餐厅假装很成熟，顺便查下资料...",
        "在四餐门口躲避人群，进行小范围路径规划...",
        "在五六餐之间漫步，纠结中午到底吃哪家...",
        "在七餐研究生食堂，寻找传说中的隐藏菜单...",
        "在哈乐餐厅门口，回忆上一次聚餐的干饭量...",
        "在留园餐厅外，感受高端学术会议的气息...",
        "在教师活动中心门口，打听最新的教务变动...",
        "在校内巴士站，目送第三辆挤不上去的校车...",
        "在凯旋门前饮水思源，顺便合个影...",
        "在庙门下，感受五千亩地的辽阔...",
        "在拖鞋门外，等待那个迟到的外卖...",
        "在霍英东体育中心，模拟百卅校庆的入场动线...",
        "在校医院门口排队，思考熬夜对绩点的影响...",
        "在捭阖塘边看水波，试图让思维进入递归状态...",
        "在南区生态林里迷路，顺便采集了一下环境信息...",
        "在校园瑞幸店门口，等待那杯续命的冰美式...",
        "在东区宿舍楼下，看外卖小哥表演漂移...",
        "在西区翻新工地旁，计算这波装修的完成日期...",
        "在陈瑞球楼的台阶上，等一个迟到的面试通知...",
        "在媒体与传播学院演播厅外，寻找信号接入点...",
        "在法学院凯原楼前，进行一场严肃的逻辑推理...",
        "在机动学院的齿轮轰鸣声中，重构代码底层...",
        "在李政道图书馆，感受科艺结合的降维打击...",
        "在微电子学院楼下，思考芯片与人生的关联...",
        "在材料学院的实验炉旁，等待数据冷却...",
        "在农业与生物学院的温室外，观察植物生长...",
        "在凯源法学院的石柱下，整理待会儿要用的陈述...",
        "在校史馆的展板前，穿越回 1896 年打听消息...",
        "在光彪楼的乒乓球声中，快速检索关键信息...",
        "在铁生馆门口，看看今天有什么有趣的社招...",
        "在南体看大佬们刷圈，内心毫无波澜...",
        "在网球场外，被一颗流弹网球打断了思路...",
        "在致远游泳馆门口，感受空气中淡淡的氯气味...",
        "在东区大草坪，看社团招新留下的满地热情...",
        "在宣怀大道的减速带上，颠出了人生的节奏感...",
        "在思源北路的长椅上，坐看云卷云舒...",
        "在淡水河畔，思考校区间通勤的最优解...",
        "在安泰经管学院，计算这波搜索的 ROI...",
        "在凯原法学院的模拟法庭，进行自我辩护...",
        "在环境学院的采样瓶里，寻找纯净的数据...",
        "在数学科学学院，推导一个不存在的公式...",
        "在外国语学院楼下，练习用三门语言说‘Bug’...",
        "在设计学院的工坊里，打磨界面的每一个像素...",
        "在马克思主义学院，思考历史叙事的必然性...",
        "在体育系办公室门口，申请这学期的体测补考...",
        "在空天学院的机库旁，梦想着代码能飞上天...",
        "在人工智能研究院，和未来的自己打个招呼...",
        "在转化医学中心，试图把冷数据转化为热结果...",
        "在综合实验楼的电梯里，信号陷入了量子叠加态...",
        "在东区新寝室阳台，俯瞰整个闵大荒的灯火...",
        "在菁菁堂的后台，准备一场关于 AI 的脱口秀...",
        "在水源 BBS 的水区，寻找失散多年的灵感...",
        "在交我办 App 的进度条前，保持虔诚的姿态...",
        "在闵行校区的第 48 个围挡旁，重新规划路线...",
        "在学术活动中心，等一场不一定能听懂的讲座...",
        "在致远游泳馆，试图让思路像鱼一样丝滑...",
        "在校友林里找寻，那一棵刻着学长名字的树...",
        "在西大门的喷泉旁，洗涤一下疲惫的算法...",
        "在东区足球场的草皮上，找寻失落的射门靴...",
        "在南体育馆的羽毛球场，进行高频数据交换...",
        "在研究生院窗口，咨询如何让毕设不挂科...",
        "在保卫处监控室外，寻找丢失的校园卡线索...",
        "在后勤集团办公室，打听空调费什么时候充值...",
        "在校园巴士的后排，强行打开电脑改个 Bug...",
        "在石楠花最盛开的路口，屏息冲刺 100 米...",
        "在思源湖的拱桥上，看水里的锦鲤拒绝干活...",
        "在霍体门口，回忆当年的开学典礼...",
        "在菁菁堂剧院的红色座椅上，陷入深度思考...",
        "在淡水河的木栈道，避开正在拍婚纱照的新人...",
        "在交大密西根学院楼下，纠结要不要喝杯咖啡...",
        "在巴黎高科卓越工程师学院，感受法式逻辑...",
        "在百卅校庆的倒计时牌前，默默许了个愿...",
        "在闵大荒的星空下，完成了最后一次数据对齐...",
    ]

    def __new__(cls):
        """Implement singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def get_instance(cls) -> "ToolUIManager":
        """
        Get the singleton instance of ToolUIManager.

        Returns:
            ToolUIManager instance
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def enable(cls) -> None:
        """Enable tool UI output."""
        cls._enabled = True

    @classmethod
    def disable(cls) -> None:
        """Disable tool UI output."""
        cls._enabled = False

    def display_tool_call(self, tool_name: str) -> None:
        """
        Display tool call header.

        Args:
            tool_name: Name of the tool being called
        """
        if not self._enabled:
            return
        start_live()
        console.print()  # Add newline for spacing

        header = Text()
        header.append("", style=Style(color=ThemeColors.TOOL_ACCENT, bold=True))
        header.append("Tool Call: ", style=Style(color=ThemeColors.TOOL_SECONDARY))
        header.append(tool_name, style=Style(color=ThemeColors.TOOL_ACCENT, bold=True))

        console.print(
            Panel(
                header,
                border_style=Style(color=ThemeColors.TOOL_BORDER),
                padding=(0, 1),
            )
        )

    def display_tool_input(self, tool_name: str, arguments: Dict[str, Any]) -> None:
        """
        Display tool input parameters.

        Args:
            tool_name: Full tool name
            arguments: Tool arguments dictionary
        """
        if not self._enabled:
            return
        start_live()
        # Create title
        title = Text()
        title.append("", style=Style(color=ThemeColors.TOOL_ACCENT))
        title.append("Tool Input", style=Style(color=ThemeColors.TOOL_SECONDARY))

        # Create content table
        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_column("Key", style=Style(color=ThemeColors.TOOL_SECONDARY))
        table.add_column("Value", style=Style(color=ThemeColors.FG))

        table.add_row("Tool", tool_name)
        args_str = json.dumps(arguments, indent=2, ensure_ascii=False)
        table.add_row("Arguments", Text(args_str, style=Style(color=ThemeColors.DIM)))

        console.print(
            Panel(
                table,
                title=title,
                title_align="left",
                border_style=Style(color=ThemeColors.TOOL_PRIMARY),
                padding=(0, 1),
            )
        )
        console.print()

    def display_execution_status(
        self, status: str = "executing", message: str = ""
    ) -> None:
        """
        Display tool execution status using unified status manager.

        Args:
            status: Either 'executing' or 'completed'
            message: Optional status message
        """
        if not self._enabled:
            return

        status_mgr = get_status_manager()

        def _dynamic_executing_message() -> str:
            now = time.time()
            if self._last_dynamic_msg and now - self._last_dynamic_msg_ts < 5:
                return self._last_dynamic_msg

            dynamic_msg = random.choice(self._dynamic_messages)

            self._last_dynamic_msg = dynamic_msg
            self._last_dynamic_msg_ts = now
            return dynamic_msg

        if status == "executing":
            msg = message or _dynamic_executing_message()
            status_mgr.set_executing(msg)
        elif status == "completed":
            msg = message or "成功"
            status_mgr.set_success(msg)
            time.sleep(0.3)
            status_mgr.clear()

    def display_tool_result(self, result: str, max_length: int = 500) -> None:
        """
        Display tool execution result.

        Args:
            result: Result text from tool execution
            max_length: Maximum length to display before truncating
        """
        if not self._enabled:
            return
        console.print()  # Add newline for spacing
        start_live()
        # Create title
        title = Text()
        title.append("", style=Style(color=ThemeColors.TOOL_ACCENT))
        title.append("Result", style=Style(color=ThemeColors.TOOL_SECONDARY))

        # Truncate if too long
        if len(result) > max_length:
            truncated = (
                result[:max_length]
                + f"...(truncated, full length: {len(result)} chars)"
            )
            result_text = Text(truncated, style=Style(color=ThemeColors.FG))
        else:
            result_text = Text(result, style=Style(color=ThemeColors.FG))

        console.print(
            Panel(
                result_text,
                title=title,
                title_align="left",
                border_style=Style(color=ThemeColors.TOOL_PRIMARY),
                padding=(0, 1),
            )
        )
        console.print()

    def display_tool_error(self, error_msg: str) -> None:
        """
        Display tool execution error.

        Args:
            error_msg: Error message to display
        """
        if not self._enabled:
            return
        console.print()  # Add newline for spacing
        start_live()
        error_text = Text()
        error_text.append("✗ ", style=Style(color=ThemeColors.ERROR))
        error_text.append(error_msg, style=Style(color=ThemeColors.ERROR))

        console.print(
            Panel(
                error_text,
                border_style=Style(color=ThemeColors.ERROR),
                padding=(0, 1),
            )
        )
        console.print()


# Global instance
tool_ui = ToolUIManager()
