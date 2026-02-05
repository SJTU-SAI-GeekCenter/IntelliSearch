"""
12306 Train Search MCP Server

Provides MCP tools for searching Chinese train tickets via 12306 API.
"""

import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from dateutil import tz

from mcp.server.fastmcp import FastMCP
from api_client import (
    get_stations,
    get_lcquery_path,
    get_cookie,
    make_12306_request,
    parse_tickets_data,
    parse_tickets_info,
    check_date,
    format_cookies,
    API_BASE,
    SEARCH_API_BASE,
)
from utils import format_ticket_status, TicketInfo, StationData


# Initialize MCP server
mcp = FastMCP("12306-train-search")

# Global cache
_STATIONS: Optional[Dict[str, StationData]] = None
_CITY_STATIONS: Optional[Dict[str, List[Dict[str, str]]]] = None
_CITY_CODES: Optional[Dict[str, Dict[str, str]]] = None
_NAME_STATIONS: Optional[Dict[str, Dict[str, str]]] = None
_LCQUERY_PATH: Optional[str] = None


async def _init_data():
    """Initialize global data caches."""
    global _STATIONS, _CITY_STATIONS, _CITY_CODES, _NAME_STATIONS, _LCQUERY_PATH

    if _STATIONS is None:
        _STATIONS = await get_stations()

        # Build city stations mapping
        _CITY_STATIONS = {}
        for station in _STATIONS.values():
            city = station.city
            if city not in _CITY_STATIONS:
                _CITY_STATIONS[city] = []
            _CITY_STATIONS[city].append(
                {
                    "station_code": station.station_code,
                    "station_name": station.station_name,
                }
            )

        # Build city codes mapping (main station per city)
        _CITY_CODES = {}
        for city, stations in _CITY_STATIONS.items():
            for station in stations:
                if station["station_name"] == city:
                    _CITY_CODES[city] = station
                    break

        # Build name stations mapping
        _NAME_STATIONS = {}
        for station in _STATIONS.values():
            name = station.station_name.replace("站", "")
            _NAME_STATIONS[name] = {
                "station_code": station.station_code,
                "station_name": station.station_name,
            }

    if _LCQUERY_PATH is None:
        _LCQUERY_PATH = await get_lcquery_path()


@mcp.tool()
async def get_current_date() -> str:
    """
    Get current date in Shanghai timezone (Asia/Shanghai, UTC+8).

    Returns:
        Current date in "yyyy-MM-dd" format
    """
    try:
        shanghai_tz = tz.gettz("Asia/Shanghai")
        now = datetime.now(shanghai_tz)
        return now.strftime("%Y-%m-%d")
    except Exception as e:
        return f"Error: Failed to get current date - {str(e)}"


@mcp.tool()
async def get_stations_code_in_city(city: str) -> str:
    """
    Get all train station codes and names for a given city.

    Args:
        city: Chinese city name, e.g., "北京", "上海"

    Returns:
        JSON string containing all stations in the city
    """
    await _init_data()

    if city not in _CITY_STATIONS:
        return "Error: City not found."

    return json.dumps(_CITY_STATIONS[city], ensure_ascii=False, indent=2)


@mcp.tool()
async def get_station_code_of_citys(citys: str) -> str:
    """
    Get representative station codes for given cities.

    Args:
        citys: City names separated by |, e.g., "北京|上海"

    Returns:
        JSON string mapping cities to their station codes
    """
    await _init_data()

    result = {}
    for city in citys.split("|"):
        if city not in _CITY_CODES:
            result[city] = {"error": "City not found"}
        else:
            result[city] = _CITY_CODES[city]

    import json

    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool()
async def get_station_code_by_names(station_names: str) -> str:
    """
    Get station codes by specific station names.

    Args:
        stationNames: Station names separated by |, e.g., "北京南|上海虹桥"

    Returns:
        JSON string mapping station names to their codes
    """
    await _init_data()

    result = {}
    for name in station_names.split("|"):
        clean_name = name.replace("站", "")
        if clean_name not in _NAME_STATIONS:
            result[name] = {"error": "Station not found"}
        else:
            result[name] = _NAME_STATIONS[clean_name]

    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool()
async def get_tickets(
    date: str,
    fromStation: str,
    toStation: str,
    format: str = "text",
) -> str:
    """
    Query 12306 ticket information.

    Args:
        date: Query date in "yyyy-MM-dd" format
        fromStation: Departure station code (use get-station-code-by-names or get-station-code-of-citys)
        toStation: Arrival station code (use get-station-code-by-names or get-station-code-of-citys)
        format: Output format ('text', 'csv', 'json')

    Returns:
        Formatted ticket information
    """
    await _init_data()

    # Validate date
    if not check_date(date):
        return "Error: The date cannot be earlier than today."

    # Validate stations
    if fromStation not in _STATIONS or toStation not in _STATIONS:
        return "Error: Station not found."

    params = {
        "leftTicketDTO.train_date": date,
        "leftTicketDTO.from_station": fromStation,
        "leftTicketDTO.to_station": toStation,
        "purpose_codes": "ADULT",
    }

    cookies = await get_cookie()
    if not cookies:
        return "Error: Failed to get cookies. Check your network."

    response = make_12306_request(
        f"{API_BASE}/otn/leftTicket/query",
        params=params,
        headers={"Cookie": format_cookies(cookies)},
    )

    if not response or response.get("httpstatus") != "200":
        return "Error: Failed to query ticket data."

    try:
        tickets_data = parse_tickets_data(response["data"]["result"])
        tickets_info = parse_tickets_info(tickets_data, response["data"]["map"])
    except Exception as e:
        return f"Error: Failed to parse ticket data - {str(e)}"

    # Format output
    if format == "csv":
        return format_tickets_info_csv(tickets_info)
    elif format == "json":
        return json.dumps(
            [_ticket_to_dict(t) for t in tickets_info], ensure_ascii=False, indent=2
        )
    else:
        return format_tickets_info_text(tickets_info)


@mcp.tool()
async def get_interline_tickets(
    date: str,
    fromStation: str,
    toStation: str,
    middleStation: str = "",
    showWZ: bool = False,
    limitedNum: int = 10,
) -> str:
    """
    Query 12306 interline (transfer) ticket information.

    Args:
        date: Query date in "yyyy-MM-dd" format
        fromStation: Departure station code
        toStation: Arrival station code
        middleStation: Transfer station code (optional)
        showWZ: Whether to show trains with no seats
        limitedNum: Limit number of results (default 10)

    Returns:
        Formatted interline ticket information in JSON format
    """
    await _init_data()

    if not check_date(date):
        return "Error: The date cannot be earlier than today."

    if fromStation not in _STATIONS or toStation not in _STATIONS:
        return "Error: Station not found."

    cookies = await get_cookie()
    if not cookies:
        return "Error: Failed to get cookies. Check your network."

    params = {
        "train_date": date,
        "from_station_telecode": fromStation,
        "to_station_telecode": toStation,
        "middle_station": middleStation,
        "result_index": "0",
        "can_query": "Y",
        "isShowWZ": "Y" if showWZ else "N",
        "purpose_codes": "00",
        "channel": "E",
    }

    interline_data = []
    while len(interline_data) < limitedNum:
        response = make_12306_request(
            f"{API_BASE}{_LCQUERY_PATH}",
            params=params,
            headers={"Cookie": format_cookies(cookies)},
        )

        if not response:
            return "Error: Failed to query interline tickets."

        if isinstance(response.get("data"), str):
            return f'No interline tickets found. ({response.get("errorMsg", "Unknown error")})'

        interline_data.extend(response["data"].get("middleList", []))

        if response["data"].get("can_query") == "N":
            break

        params["result_index"] = str(response["data"].get("result_index", 0))

    return json.dumps(interline_data[:limitedNum], ensure_ascii=False, indent=2)


@mcp.tool()
async def get_train_route_stations(
    trainCode: str, departDate: str, format: str = "text"
) -> str:
    """
    Query route stations for a specific train.

    Args:
        trainCode: Train code, e.g., "G1033"
        departDate: Departure date in "yyyy-MM-dd" format
        format: Output format ('text', 'json')

    Returns:
        Formatted route station information
    """

    # Search for train
    search_params = {"keyword": trainCode, "date": departDate.replace("-", "")}

    search_response = make_12306_request(
        f"{SEARCH_API_BASE}/search/v1/train/search", params=search_params
    )

    if not search_response or not search_response.get("data"):
        return "No matching train found."

    train_data = search_response["data"][0]

    # Query route stations
    cookies = await get_cookie()
    if not cookies:
        return "Error: Failed to get cookies. Check your network."

    query_params = {
        "leftTicketDTO.train_no": train_data["train_no"],
        "leftTicketDTO.train_date": departDate,
        "rand_code": "",
    }

    query_response = make_12306_request(
        f"{API_BASE}/otn/queryTrainInfo/query",
        params=query_params,
        headers={"Cookie": format_cookies(cookies)},
    )

    if not query_response or not query_response.get("data"):
        return "Error: Failed to query route stations."

    route_data = query_response["data"]["data"]

    if format == "json":
        return json.dumps(route_data, ensure_ascii=False, indent=2)
    else:
        return format_route_stations_text(route_data)


def format_tickets_info_text(tickets: List[TicketInfo]) -> str:
    """Format ticket information as text."""
    if not tickets:
        return "No ticket information found."

    lines = ["车次|出发站 -> 到达站|出发时间 -> 到达时间|历时"]

    for ticket in tickets:
        info = (
            f"{ticket.start_train_code} "
            f"{ticket.from_station} -> {ticket.to_station} "
            f"{ticket.start_time} -> {ticket.arrive_time} "
            f"历时：{ticket.lishi}"
        )

        for price in ticket.prices:
            status = format_ticket_status(price.num)
            info += f"\n- {price.seat_name}: {status} {price.price}元"

        lines.append(info)

    return "\n".join(lines)


def format_tickets_info_csv(tickets: List[TicketInfo]) -> str:
    """Format ticket information as CSV."""
    if not tickets:
        return "No ticket information found."

    lines = ["车次,出发站,到达站,出发时间,到达时间,历时,票价,特色标签"]

    for ticket in tickets:
        prices = ",".join(
            [
                f"{p.seat_name}: {format_ticket_status(p.num)}{p.price}元"
                for p in ticket.prices
            ]
        )
        flags = "&".join(ticket.dw_flag) if ticket.dw_flag else "/"

        line = (
            f"{ticket.start_train_code},"
            f"{ticket.from_station},"
            f"{ticket.to_station},"
            f"{ticket.start_time},"
            f"{ticket.arrive_time},"
            f"{ticket.lishi},"
            f"[{prices}],"
            f"{flags}"
        )
        lines.append(line)

    return "\n".join(lines)


def format_route_stations_text(stations: List[Dict[str, Any]]) -> str:
    """Format route station information as text."""
    if not stations:
        return "No route station information found."

    first = stations[0]
    lines = [
        f"{first.get('station_train_code', '')}次列车",
        "站序|车站|车次|到达时间|出发时间|历时",
    ]

    for idx, station in enumerate(stations, 1):
        line = (
            f"{idx}|{station.get('station_name', '')}|"
            f"{station.get('station_train_code', '')}|"
            f"{station.get('arrive_time', '')}|"
            f"{station.get('start_time', '')}|"
            f"{station.get('arrive_day_str', '')} "
            f"{station.get('running_time', '')}"
        )
        lines.append(line)

    return "\n".join(lines)


def _ticket_to_dict(ticket: TicketInfo) -> Dict[str, Any]:
    """Convert TicketInfo to dictionary."""
    return {
        "train_no": ticket.train_no,
        "start_train_code": ticket.start_train_code,
        "start_date": ticket.start_date,
        "arrive_date": ticket.arrive_date,
        "start_time": ticket.start_time,
        "arrive_time": ticket.arrive_time,
        "lishi": ticket.lishi,
        "from_station": ticket.from_station,
        "to_station": ticket.to_station,
        "from_station_telecode": ticket.from_station_telecode,
        "to_station_telecode": ticket.to_station_telecode,
        "prices": [
            {
                "seat_name": p.seat_name,
                "short": p.short,
                "seat_type_code": p.seat_type_code,
                "num": p.num,
                "price": p.price,
                "discount": p.discount,
            }
            for p in ticket.prices
        ],
        "dw_flag": ticket.dw_flag,
    }


if __name__ == "__main__":
    mcp.run()
