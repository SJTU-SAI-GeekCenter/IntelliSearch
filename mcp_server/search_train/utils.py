"""
Utility functions for 12306 train search.

Provides constants, filters, and helper functions for ticket processing.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass


@dataclass
class TicketData:
    """Raw ticket data from 12306 API."""

    secret_Sstr: str
    button_text_info: str
    train_no: str
    station_train_code: str
    start_station_telecode: str
    end_station_telecode: str
    from_station_telecode: str
    to_station_telecode: str
    start_time: str
    arrive_time: str
    lishi: str
    canWebBuy: str
    yp_info: str
    start_train_date: str
    train_seat_feature: str
    location_code: str
    from_station_no: str
    to_station_no: str
    is_support_card: str
    controlled_train_flag: str
    gg_num: str
    gr_num: str
    qt_num: str
    rw_num: str
    rz_num: str
    tz_num: str
    wz_num: str
    yb_num: str
    yw_num: str
    yz_num: str
    ze_num: str
    zy_num: str
    swz_num: str
    srrb_num: str
    yp_ex: str
    seat_types: str
    exchange_train_flag: str
    houbu_train_flag: str
    houbu_seat_limit: str
    yp_info_new: str
    dw_flag: str
    stopcheckTime: str
    country_flag: str
    local_arrive_time: str
    local_start_time: str
    bed_level_info: str
    seat_discount_info: str
    sale_time: str


@dataclass
class Price:
    """Price information for a seat type."""

    seat_name: str
    short: str
    seat_type_code: str
    num: str
    price: float
    discount: Optional[float] = None


@dataclass
class TicketInfo:
    """Parsed ticket information."""

    train_no: str
    start_train_code: str
    start_date: str
    start_time: str
    arrive_date: str
    arrive_time: str
    lishi: str
    from_station: str
    to_station: str
    from_station_telecode: str
    to_station_telecode: str
    prices: List[Price]
    dw_flag: List[str]


@dataclass
class StationData:
    """Station information."""

    station_id: str
    station_name: str
    station_code: str
    station_pinyin: str
    station_short: str
    station_index: str
    code: str
    city: str
    r1: str
    r2: str


@dataclass
class RouteStationData:
    """Route station data."""

    arrive_day_str: str
    arrive_time: str
    station_train_code: str
    station_name: str
    arrive_day_diff: str
    start_time: str
    wz_num: str
    station_no: str
    running_time: str
    train_class_name: Optional[str] = None
    is_start: Optional[str] = None
    service_type: Optional[str] = None
    end_station_name: Optional[str] = None


@dataclass
class RouteStationInfo:
    """Parsed route station information."""

    station_name: str
    station_train_code: str
    arrive_time: str
    start_time: str
    lishi: str
    arrive_day_str: str
    train_class_name: Optional[str] = None
    service_type: Optional[str] = None
    end_station_name: Optional[str] = None


@dataclass
class InterlineTicketData:
    """Interline (transfer) ticket data."""

    arrive_time: str
    bed_level_info: str
    controlled_train_flag: str
    country_flag: str
    day_difference: str
    dw_flag: str
    end_station_name: str
    end_station_telecode: str
    from_station_name: str
    from_station_no: str
    from_station_telecode: str
    gg_num: str
    gr_num: str
    is_support_card: str
    lishi: str
    local_arrive_time: str
    local_start_time: str
    qt_num: str
    rw_num: str
    rz_num: str
    seat_discount_info: str
    seat_types: str
    srrb_num: str
    start_station_name: str
    start_station_telecode: str
    start_time: str
    start_train_date: str
    station_train_code: str
    swz_num: str
    to_station_name: str
    to_station_no: str
    to_station_telecode: str
    train_no: str
    train_seat_feature: str
    trms_train_flag: str
    tz_num: str
    wz_num: str
    yb_num: str
    yp_info: str
    yw_num: str
    yz_num: str
    ze_num: str
    zy_num: str


@dataclass
class InterlineInfo:
    """Parsed interline (transfer) ticket information."""

    lishi: str
    start_time: str
    start_date: str
    middle_date: str
    arrive_date: str
    arrive_time: str
    from_station_code: str
    from_station_name: str
    middle_station_code: str
    middle_station_name: str
    end_station_code: str
    end_station_name: str
    start_train_code: str
    first_train_no: str
    second_train_no: str
    train_count: int
    ticket_list: List[TicketInfo]
    same_station: bool
    same_train: bool
    wait_time: str


@dataclass
class TrainSearchData:
    """Train search result data."""

    date: str
    from_station: str
    station_train_code: str
    to_station: str
    total_num: str
    train_no: str


# Seat type mappings
SEAT_SHORT_TYPES = {
    "swz": "商务座",
    "tz": "特等座",
    "zy": "一等座",
    "ze": "二等座",
    "gr": "高软卧",
    "srrb": "动卧",
    "rw": "软卧",
    "yw": "硬卧",
    "rz": "软座",
    "yz": "硬座",
    "wz": "无座",
    "qt": "其他",
    "gg": "",
    "yb": "",
}

SEAT_TYPES = {
    "9": {"name": "商务座", "short": "swz"},
    "P": {"name": "特等座", "short": "tz"},
    "M": {"name": "一等座", "short": "zy"},
    "D": {"name": "优选一等座", "short": "zy"},
    "O": {"name": "二等座", "short": "ze"},
    "S": {"name": "二等包座", "short": "ze"},
    "6": {"name": "高级软卧", "short": "gr"},
    "A": {"name": "高级动卧", "short": "gr"},
    "4": {"name": "软卧", "short": "rw"},
    "I": {"name": "一等卧", "short": "rw"},
    "F": {"name": "动卧", "short": "rw"},
    "3": {"name": "硬卧", "short": "yw"},
    "J": {"name": "二等卧", "short": "yw"},
    "2": {"name": "软座", "short": "rz"},
    "1": {"name": "硬座", "short": "yz"},
    "W": {"name": "无座", "short": "wz"},
    "WZ": {"name": "无座", "short": "wz"},
    "H": {"name": "其他", "short": "qt"},
}

DW_FLAGS = [
    "智能动车组",
    "复兴号",
    "静音车厢",
    "温馨动卧",
    "动感号",
    "支持选铺",
    "老年优惠",
]


def format_ticket_status(num: str) -> str:
    """
    Format ticket availability status.

    Args:
        num: Ticket quantity number or status string

    Returns:
        Formatted ticket status description
    """
    if num.isdigit():
        count = int(num)
        if count == 0:
            return "无票"
        else:
            return f"剩余{count}张票"

    status_map = {
        "有": "有票",
        "充足": "有票",
        "无": "无票",
        "--": "无票",
        "": "无票",
        "候补": "无票需候补",
    }
    return status_map.get(num, f"{num}票")


def extract_lishi(all_lishi: str) -> str:
    """
    Extract duration in HH:MM format from Chinese text.

    Args:
        all_lishi: Duration string like "H小时M分钟" or "M分钟"

    Returns:
        Duration in "HH:MM" format
    """
    import re

    match = re.match(r"(?:(\d+)小时)?(\d+?)分钟", all_lishi)
    if not match:
        raise ValueError("extract_lishi failed: no match found")

    hours = match.group(1)
    minutes = match.group(2)

    if not hours:
        return f"00:{minutes}"
    return f"{hours.zfill(2)}:{minutes}"


def extract_prices(
    yp_info: str, seat_discount_info: str, ticket_data: Any
) -> List[Dict[str, Any]]:
    """
    Extract price information from ticket data.

    Args:
        yp_info: Price information string
        seat_discount_info: Seat discount information string
        ticket_data: Ticket data object

    Returns:
        List of price information dictionaries
    """
    PRICE_STR_LENGTH = 10
    DISCOUNT_STR_LENGTH = 5
    prices = []
    discounts = {}

    # Parse discounts
    for i in range(len(seat_discount_info) // DISCOUNT_STR_LENGTH):
        discount_str = seat_discount_info[
            i * DISCOUNT_STR_LENGTH : (i + 1) * DISCOUNT_STR_LENGTH
        ]
        discounts[discount_str[0]] = int(discount_str[1:])

    # Parse prices
    for i in range(len(yp_info) // PRICE_STR_LENGTH):
        price_str = yp_info[i * PRICE_STR_LENGTH : (i + 1) * PRICE_STR_LENGTH]

        # Determine seat type code
        price_value = int(price_str[6:10])
        if price_value >= 3000:
            seat_type_code = "W"  # No seat
        elif price_str[0] not in SEAT_TYPES:
            seat_type_code = "H"  # Other seat
        else:
            seat_type_code = price_str[0]

        seat_type = SEAT_TYPES.get(seat_type_code, {"name": "其他", "short": "qt"})
        price = int(price_str[1:6]) / 10
        discount = discounts.get(seat_type_code)

        # Get ticket quantity
        short = seat_type["short"]
        num = getattr(ticket_data, f"{short}_num", "")

        prices.append(
            {
                "seat_name": seat_type["name"],
                "short": short,
                "seat_type_code": seat_type_code,
                "num": num,
                "price": price,
                "discount": discount,
            }
        )

    return prices


def extract_dw_flags(dw_flag_str: str) -> List[str]:
    """
    Extract train feature flags from flag string.

    Args:
        dw_flag_str: Flag string from ticket data

    Returns:
        List of feature flag names
    """
    if not dw_flag_str:
        return []

    dw_flag_list = dw_flag_str.split("#")
    result = []

    if len(dw_flag_list) > 0 and dw_flag_list[0] == "5":
        result.append(DW_FLAGS[0])  # Intelligent EMU

    if len(dw_flag_list) > 1 and dw_flag_list[1] == "1":
        result.append(DW_FLAGS[1])  # Fuxing Hao

    if len(dw_flag_list) > 2:
        if dw_flag_list[2].startswith("Q"):
            result.append(DW_FLAGS[2])  # Quiet carriage
        elif dw_flag_list[2].startswith("R"):
            result.append(DW_FLAGS[3])  # Warm sleeper

    if len(dw_flag_list) > 5 and dw_flag_list[5] == "D":
        result.append(DW_FLAGS[4])  # 动感号

    if len(dw_flag_list) > 6 and dw_flag_list[6] != "z":
        result.append(DW_FLAGS[5])  # Support berth selection

    if len(dw_flag_list) > 7 and dw_flag_list[7] != "z":
        result.append(DW_FLAGS[6])  # Senior discount

    return result


def filter_tickets_info(
    tickets_info: List[Any],
    train_filter_flags: str = "",
    earliest_start_time: int = 0,
    latest_start_time: int = 24,
    sort_flag: str = "",
    sort_reverse: bool = False,
    limited_num: int = 0,
) -> List[Any]:
    """
    Filter and sort ticket information.

    Args:
        tickets_info: List of ticket information
        train_filter_flags: Train type filter flags (e.g., 'GD')
        earliest_start_time: Earliest departure hour (0-24)
        latest_start_time: Latest departure hour (0-24)
        sort_flag: Sort method ('startTime', 'arriveTime', 'duration')
        sort_reverse: Whether to reverse sort order
        limited_num: Maximum number of results (0 for unlimited)

    Returns:
        Filtered and sorted list of ticket information
    """
    result = tickets_info

    # Apply train type filters
    if train_filter_flags:
        result = [
            ticket
            for ticket in tickets_info
            if any(_match_train_filter(ticket, flag) for flag in train_filter_flags)
        ]

    # Filter by start time
    result = [
        ticket
        for ticket in result
        if earliest_start_time
        <= int(ticket.start_time.split(":")[0])
        < latest_start_time
    ]

    # Sort results
    if sort_flag:
        result.sort(key=lambda x: _get_sort_key(x, sort_flag))
        if sort_reverse:
            result.reverse()

    # Limit results
    if limited_num > 0:
        result = result[:limited_num]

    return result


def _match_train_filter(ticket: Any, flag: str) -> bool:
    """Check if ticket matches train filter flag."""
    code = (
        ticket.start_train_code
        if hasattr(ticket, "start_train_code")
        else ticket.start_train_code
    )

    flag_map = {
        "G": lambda: code.startswith("G") or code.startswith("C"),
        "D": lambda: code.startswith("D"),
        "Z": lambda: code.startswith("Z"),
        "T": lambda: code.startswith("T"),
        "K": lambda: code.startswith("K"),
        "O": lambda: not any(
            code.startswith(x) for x in ["G", "C", "D", "Z", "T", "K"]
        ),
        "F": lambda: (
            "复兴号" in ticket.dw_flag if hasattr(ticket, "dw_flag") else False
        ),
        "S": lambda: (
            "智能动车组" in ticket.dw_flag if hasattr(ticket, "dw_flag") else False
        ),
    }

    return flag_map.get(flag, lambda: False)()


def _get_sort_key(ticket: Any, sort_flag: str) -> Any:
    """Get sort key for ticket based on sort flag."""
    if sort_flag == "startTime":
        start_date = datetime.strptime(ticket.start_date, "%Y-%m-%d")
        start_time = ticket.start_time.split(":")
        return start_date.replace(hour=int(start_time[0]), minute=int(start_time[1]))

    elif sort_flag == "arriveTime":
        arrive_date = datetime.strptime(ticket.arrive_date, "%Y-%m-%d")
        arrive_time = ticket.arrive_time.split(":")
        return arrive_date.replace(hour=int(arrive_time[0]), minute=int(arrive_time[1]))

    elif sort_flag == "duration":
        duration = ticket.lishi.split(":")
        return int(duration[0]) * 60 + int(duration[1])

    return ticket
