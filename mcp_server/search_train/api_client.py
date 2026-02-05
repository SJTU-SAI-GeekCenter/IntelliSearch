"""
12306 API client for train search.

Handles communication with 12306 APIs including authentication and data retrieval.
"""

import re
import requests
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dateutil import tz

from utils import (
    TicketData,
    TicketInfo,
    StationData,
    Price,
    extract_prices,
    extract_dw_flags,
)


# API endpoints
API_BASE = "https://kyfw.12306.cn"
SEARCH_API_BASE = "https://search.12306.cn"
WEB_URL = "https://www.12306.cn/index/"
LCQUERY_INIT_URL = "https://kyfw.12306.cn/otn/lcQuery/init"

# Missing stations that need to be added manually
MISSING_STATIONS = [
    StationData(
        station_id="@cdd",
        station_name="成  都东",
        station_code="WEI",
        station_pinyin="chengdudong",
        station_short="cdd",
        station_index="",
        code="1707",
        city="成都",
        r1="",
        r2="",
    )
]

# Global cache for stations and LCQuery path
_STATIONS_CACHE: Optional[Dict[str, StationData]] = None
_LCQUERY_PATH: Optional[str] = None


class TrainSearchAPIError(Exception):
    """Custom exception for train search API errors."""

    pass


def parse_cookies(cookies: List[str]) -> Dict[str, str]:
    """
    Parse cookie strings into dictionary.

    Args:
        cookies: List of cookie strings

    Returns:
        Dictionary of cookie key-value pairs
    """
    cookie_record = {}
    for cookie in cookies:
        key_value_part = cookie.split(";")[0]
        if "=" in key_value_part:
            key, value = key_value_part.split("=", 1)
            cookie_record[key.strip()] = value.strip()
    return cookie_record


def format_cookies(cookies: Dict[str, str]) -> str:
    """
    Format cookie dictionary into string.

    Args:
        cookies: Dictionary of cookies

    Returns:
        Formatted cookie string
    """
    return "; ".join([f"{k}={v}" for k, v in cookies.items()])


async def get_cookie() -> Optional[Dict[str, str]]:
    """
    Get cookies from 12306 for authentication.

    Returns:
        Cookie dictionary or None if failed
    """
    url = f"{API_BASE}/otn/leftTicket/init"
    try:
        response = requests.get(url)
        set_cookie_headers = response.headers.get("Set-Cookie", "")
        if set_cookie_headers:
            return parse_cookies(set_cookie_headers.split(", "))
        return None
    except Exception as e:
        print(f"Error getting cookie: {e}")
        return None


def parse_stations_data(raw_data: str) -> Dict[str, StationData]:
    """
    Parse station data from raw string.

    Args:
        raw_data: Raw station data string

    Returns:
        Dictionary mapping station codes to StationData objects
    """
    result = {}
    data_array = raw_data.split("|")
    data_list = []

    for i in range(len(data_array) // 10):
        data_list.append(data_array[i * 10 : (i + 1) * 10])

    for group in data_list:
        if len(group) < 10:
            continue

        station = StationData(
            station_id=group[0],
            station_name=group[1],
            station_code=group[2],
            station_pinyin=group[3],
            station_short=group[4],
            station_index=group[5],
            code=group[6],
            city=group[7],
            r1=group[8],
            r2=group[9],
        )

        if station.station_code:
            result[station.station_code] = station

    return result


async def get_stations() -> Dict[str, StationData]:
    """
    Fetch all station data from 12306.

    Returns:
        Dictionary mapping station codes to StationData objects
    """
    global _STATIONS_CACHE
    if _STATIONS_CACHE:
        return _STATIONS_CACHE

    try:
        # Fetch main page
        response = requests.get(WEB_URL)
        html = response.text

        # Extract station JS file path
        match = re.search(r"\.(/script/core/common/station_name.+?\.js)", html)
        if not match:
            raise TrainSearchAPIError("Failed to find station name JS file")

        js_file_path = match.group(0)
        js_url = f'{WEB_URL.rstrip("/")}/{js_file_path.lstrip(".")}'

        # Fetch and parse station data
        js_response = requests.get(js_url)
        js_content = js_response.text

        # Extract station data variable
        var_match = re.search(r"var station_names =\'(.+?)\'", js_content)
        if not var_match:
            raise TrainSearchAPIError("Failed to parse station data")

        raw_data = var_match.group(1)
        stations = parse_stations_data(raw_data)

        # Add missing stations
        for station in MISSING_STATIONS:
            if station.station_code not in stations:
                stations[station.station_code] = station

        _STATIONS_CACHE = stations
        return stations

    except Exception as e:
        raise TrainSearchAPIError(f"Failed to get stations: {str(e)}")


async def get_lcquery_path() -> str:
    """
    Get the LCQuery API path.

    Returns:
        LCQuery API path
    """
    global _LCQUERY_PATH
    if _LCQUERY_PATH:
        return _LCQUERY_PATH

    try:
        response = requests.get(LCQUERY_INIT_URL)
        html = response.text

        match = re.search(r" var lc_search_url = '(.+?)'", html)
        if not match:
            raise TrainSearchAPIError("Failed to get LCQuery path")

        _LCQUERY_PATH = match.group(1)
        return _LCQUERY_PATH

    except Exception as e:
        raise TrainSearchAPIError(f"Failed to get LCQuery path: {str(e)}")


def make_12306_request(
    url: str,
    params: Optional[Dict[str, str]] = None,
    headers: Optional[Dict[str, str]] = None,
) -> Optional[Any]:
    """
    Make HTTP request to 12306 API.

    Args:
        url: Request URL
        params: Query parameters
        headers: Request headers

    Returns:
        Response JSON data or None if failed
    """
    try:
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error making 12306 request: {e}")
        return None


def parse_tickets_data(raw_data: List[str]) -> List[TicketData]:
    """
    Parse raw ticket data strings into TicketData objects.

    Args:
        raw_data: List of raw ticket data strings

    Returns:
        List of TicketData objects
    """
    result = []
    for item in raw_data:
        values = item.split("|")
        if len(values) < 57:
            continue

        ticket = TicketData(
            secret_Sstr=values[0],
            button_text_info=values[1],
            train_no=values[2],
            station_train_code=values[3],
            start_station_telecode=values[4],
            end_station_telecode=values[5],
            from_station_telecode=values[6],
            to_station_telecode=values[7],
            start_time=values[8],
            arrive_time=values[9],
            lishi=values[10],
            canWebBuy=values[11],
            yp_info=values[12],
            start_train_date=values[13],
            train_seat_feature=values[14],
            location_code=values[15],
            from_station_no=values[16],
            to_station_no=values[17],
            is_support_card=values[18],
            controlled_train_flag=values[19],
            gg_num=values[20],
            gr_num=values[21],
            qt_num=values[22],
            rw_num=values[23],
            rz_num=values[24],
            tz_num=values[25],
            wz_num=values[26],
            yb_num=values[27],
            yw_num=values[28],
            yz_num=values[29],
            ze_num=values[30],
            zy_num=values[31],
            swz_num=values[32],
            srrb_num=values[33],
            yp_ex=values[34],
            seat_types=values[35],
            exchange_train_flag=values[36],
            houbu_train_flag=values[37],
            houbu_seat_limit=values[38],
            yp_info_new=values[39],
            dw_flag=values[40],
            stopcheckTime=values[41],
            country_flag=values[42],
            local_arrive_time=values[43],
            local_start_time=values[44],
            bed_level_info=values[45],
            seat_discount_info=values[46],
            sale_time=values[47],
        )
        result.append(ticket)

    return result


def parse_tickets_info(
    tickets_data: List[TicketData], station_map: Dict[str, str]
) -> List[TicketInfo]:
    """
    Parse ticket data into ticket info with prices and dates.

    Args:
        tickets_data: List of TicketData objects
        station_map: Mapping from station codes to names

    Returns:
        List of TicketInfo objects
    """
    result = []

    for ticket in tickets_data:
        prices_list = extract_prices(
            ticket.yp_info_new, ticket.seat_discount_info, ticket
        )
        dw_flag = extract_dw_flags(ticket.dw_flag)

        # Convert price dicts to Price objects
        prices = [
            Price(
                seat_name=p["seat_name"],
                short=p["short"],
                seat_type_code=p["seat_type_code"],
                num=p["num"],
                price=p["price"],
                discount=p.get("discount"),
            )
            for p in prices_list
        ]

        # Parse dates and times
        start_hours, start_minutes = map(int, ticket.start_time.split(":"))
        duration_hours, duration_minutes = map(int, ticket.lishi.split(":"))

        start_date = datetime.strptime(ticket.start_train_date, "%Y%m%d")
        start_date = start_date.replace(hour=start_hours, minute=start_minutes)

        arrive_date = start_date + timedelta(
            hours=duration_hours, minutes=duration_minutes
        )

        ticket_info = TicketInfo(
            train_no=ticket.train_no,
            start_train_code=ticket.station_train_code,
            start_date=start_date.strftime("%Y-%m-%d"),
            arrive_date=arrive_date.strftime("%Y-%m-%d"),
            start_time=ticket.start_time,
            arrive_time=ticket.arrive_time,
            lishi=ticket.lishi,
            from_station=station_map.get(
                ticket.from_station_telecode, ticket.from_station_telecode
            ),
            to_station=station_map.get(
                ticket.to_station_telecode, ticket.to_station_telecode
            ),
            from_station_telecode=ticket.from_station_telecode,
            to_station_telecode=ticket.to_station_telecode,
            prices=prices,
            dw_flag=dw_flag,
        )
        result.append(ticket_info)

    return result


def check_date(date_str: str) -> bool:
    """
    Check if date is not earlier than today (in Shanghai timezone).

    Args:
        date_str: Date string in 'YYYY-MM-DD' format

    Returns:
        True if date is valid (not in the past)
    """
    shanghai_tz = tz.gettz("Asia/Shanghai")
    now = datetime.now(shanghai_tz).replace(hour=0, minute=0, second=0, microsecond=0)
    input_date = datetime.strptime(date_str, "%Y-%m-%d")
    input_date = input_date.replace(tzinfo=shanghai_tz)
    input_date = input_date.replace(hour=0, minute=0, second=0, microsecond=0)

    return input_date >= now
