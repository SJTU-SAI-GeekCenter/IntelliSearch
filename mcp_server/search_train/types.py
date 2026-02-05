"""
Data models for 12306 train search MCP server.

Defines the structure for train tickets, stations, and related information.
"""
from dataclasses import dataclass
from typing import List, Optional


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
