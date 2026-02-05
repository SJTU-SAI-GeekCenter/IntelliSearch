import json
import os
import requests
import time
from mcp.server.fastmcp import FastMCP
from typing import Any, Dict, List, Optional


def get_api_key() -> str:
    """Get the Amap Maps API key from environment variables"""
    api_key = os.getenv("AMAP_MAPS_API_KEY")
    return api_key


def print_data(line: str):
    """
    Parses and formats a single line of JSON data for printing.
    """
    try:
        line_data = json.loads(line)
        return json.dumps(line_data, indent=2, ensure_ascii=False)
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        return line


AMAP_MAPS_API_KEY = get_api_key()
mcp = FastMCP("amap-maps")


@mcp.tool()
def maps_get_from_coordinates(coordinates: str) -> str:
    """将一个高德经纬度坐标转换为行政区划地址信息

    Args:
        coordinates (str): 需要传入的经纬度坐标，传入内容规则：经度在前，纬度在后，经纬度间以“,”分割，经纬度小数点后不要超过 6 位。

    Returns:
        根据经纬度转换得到的具体的行政区划地址信息
    """
    try:
        response = requests.get(
            "https://restapi.amap.com/v3/geocode/regeo",
            params={"key": AMAP_MAPS_API_KEY, "location": coordinates},
        )
        response.raise_for_status()
        data = response.json()

        if data["status"] != "1":
            return {
                "error": f"RGeocoding failed: {data.get('info') or data.get('infocode')}"
            }
        regeocode = data.get("regeocode", {})
        formatted_address = regeocode.get(
            "formatted_address",
            "无可用地址信息，请检查经纬度信息，经纬度信息的返回格式：传入内容规则：经度在前，纬度在后，经纬度间以“,”分割，经纬度小数点后不要超过 6 位。",
        )

        return formatted_address
    except requests.exceptions.RequestException as e:
        return {"error": f"Request failed: {str(e)}"}


@mcp.tool()
def maps_get_adcode(address: str, city: Optional[str] = None) -> str:
    """得到特定地区的 adcode

    Args:
        address (str): 输出城市地名，例如南京、江苏南京、南京市等都是合法的输入
        city (Optional[str], optional): 约束城市. Defaults to None.

    Returns:
        str: 特定区域的 adcode 列表
    """
    try:
        params = {"key": AMAP_MAPS_API_KEY, "address": address}
        if city:
            params["city"] = city

        response = requests.get(
            "https://restapi.amap.com/v3/geocode/geo", params=params
        )
        response.raise_for_status()
        data = response.json()
        if data["status"] != "1":
            return (
                f"error, Geocoding failed: {data.get('info') or data.get('infocode')}"
            )

        geocodes = data.get("geocodes", [])
        results = [geo.get("adcode") for geo in geocodes]
        return results

    except requests.exceptions.RequestException as e:
        return f"error: Request failed: {str(e)}"


@mcp.tool()
def maps_get_from_location(address: str, city: Optional[str] = None) -> List[str]:
    """将详细的结构化地址转换为经纬度坐标。支持对地标性名胜景区、建筑物名称解析为经纬度坐标

    Args:
        address (str): 结构化地址（具体定义：地址肯定是一串字符，内含国家、省份、城市、区县、城镇、乡村、街道、门牌号码、屋邨、大厦等建筑物名称。按照由大区域名称到小区域名称组合在一起的字符。一个有效的地址应该是独一无二的。注意：针对大陆、港、澳地区的地理编码转换时可以将国家信息选择性的忽略，但省、市、城镇等级别的地址构成是不能忽略的。暂时不支持返回台湾省的详细地址信息。）
        city (Optional[str], optional): _description_. Defaults to None.

    Returns:
        List[str]: 返回结构化的经纬度坐标，经度在前，纬度在后，经纬度间以“,”分割
    """
    try:
        params = {"key": AMAP_MAPS_API_KEY, "address": address}
        if city:
            params["city"] = city

        response = requests.get(
            "https://restapi.amap.com/v3/geocode/geo", params=params
        )
        response.raise_for_status()
        data = response.json()
        if data["status"] != "1":
            return {
                "error": f"Geocoding failed: {data.get('info') or data.get('infocode')}"
            }

        geocodes = data.get("geocodes", [])
        results = [geo.get("location") for geo in geocodes]
        return results

    except requests.exceptions.RequestException as e:
        return [f"Request failed: {str(e)}"]


@mcp.tool()
def maps_get_structured_location(address: str, city: Optional[str] = None) -> List[str]:
    """得到搜索结果中结构化的地点信息

    Args:
        address (str): 模糊地名搜索（例如夫子庙）
        city (Optional[str], optional): 城市名约束. Defaults to None.

    Returns:
        List[str]: 返回一个得到的搜索结果字符串，例如"夫子庙"的返回结果是 ['四川省成都市大邑县安仁镇夫子庙', '重庆市北碚区静观镇夫子庙', '江苏省南京市秦淮区夫子庙街道贡院街江南贡院', '陕西省榆林市榆阳区新明楼街道夫子庙', '河南省洛阳市宜阳县锦屏镇夫子庙', '江苏省宿迁市泗阳县三庄镇夫子庙']
    """
    coordinates = maps_get_from_location(address, city)
    results = [maps_get_from_coordinates(coordinate) for coordinate in coordinates]
    return results


@mcp.tool()
def maps_weather(city: str) -> str:
    """根据城市名称或者标准adcode查询指定城市的天气

    Args:
        city (str): 城市名称或者 标准化 adcode 或者标准化地址

    Returns:
        str: 最近四天该城市的天气预报
    """
    try:
        adcode = maps_get_adcode(city)
        if "error" in adcode:
            # use original input
            adcode = city
        response = requests.get(
            "https://restapi.amap.com/v3/weather/weatherInfo",
            params={"key": AMAP_MAPS_API_KEY, "city": adcode, "extensions": "all"},
        )
        response.raise_for_status()
        data = response.json()

        if data["status"] != "1":
            return {
                "error": f"Get weather failed: {data.get('info') or data.get('infocode')}"
            }

        forecasts = data.get("forecasts", [])
        if not forecasts:
            return {"error": "No forecast data available"}

        city = forecasts[0]["city"]
        forecasts = forecasts[0]["casts"]
        result_str = f"{city} 的天气预报：\n"

        for forecast in forecasts:
            date = forecast.get("date", "N/A")
            day_weather = forecast.get("dayweather", "N/A")
            night_weather = forecast.get("nightweather", "N/A")
            day_temp = forecast.get("daytemp", "N/A")
            night_temp = forecast.get("nighttemp", "N/A")
            day_wind = forecast.get("daywind", "N/A")
            night_wind = forecast.get("nightwind", "N/A")

            result_str += f"--- {date} ---\n"
            result_str += (
                f"白 天：{day_weather}，温度 {day_temp} 摄氏度，风向 {day_wind}\n"
            )
            result_str += f"夜 晚：{night_weather}，温度 {night_temp} 摄氏度，风向 {night_wind}\n\n"

        return result_str
    except requests.exceptions.RequestException as e:
        return {"error": f"Request failed: {str(e)}"}


@mcp.tool()
def maps_bicycling_by_address(
    origin_address: str,
    destination_address: str,
    origin_city: Optional[str] = None,
    destination_city: Optional[str] = None,
) -> str:
    """Plans a bicycle route between two locations using addresses. Unless you have a specific reason to use coordinates, it's recommended to use this tool.

    Args:
        origin_address (str): Starting point address (e.g. "北京市朝阳区阜通东大街6号")
        destination_address (str): Ending point address (e.g. "北京市海淀区上地十街10号")
        origin_city (Optional[str]): Optional city name for the origin address to improve geocoding accuracy
        destination_city (Optional[str]): Optional city name for the destination address to improve geocoding accuracy

    Returns:
        str: Route information including distance, duration, and turn-by-turn instructions.
        Considers bridges, one-way streets, and road closures. Supports routes up to 500km.
    """
    try:
        # Convert origin address to coordinates
        origin_result = maps_get_from_location(origin_address, origin_city)
        if "error" in origin_result:
            return {
                "error": f"Failed to geocode origin address: {origin_result['error']}"
            }

        origin_location = origin_result[0]
        time.sleep(0.8)

        # Convert destination address to coordinates
        destination_result = maps_get_from_location(
            destination_address, destination_city
        )
        if "error" in destination_result:
            return {
                "error": f"Failed to geocode destination address: {destination_result['error']}"
            }

        destination_location = destination_result[0]
        time.sleep(0.8)
        if not destination_location:
            return {
                "error": "Could not extract coordinates from destination geocoding result"
            }

        # Use the coordinates to plan the bicycle route
        route_result = _maps_bicycling_by_coordinates(
            origin_location, destination_location
        )

        # Add address information to the result
        if "error" not in route_result:
            route_result["addresses"] = {
                "origin": {"address": origin_address, "coordinates": origin_location},
                "destination": {
                    "address": destination_address,
                    "coordinates": destination_location,
                },
            }

        origin_address = route_result["addresses"]["origin"]["address"]
        destination_address = route_result["addresses"]["destination"]["address"]
        total_distance_km = route_result["data"]["paths"][0]["distance"] / 1000
        total_duration_min = round(route_result["data"]["paths"][0]["duration"] / 60)

        # Start the navigation text with origin and destination information
        navigation_text = f"从 {origin_address} 骑行至 {destination_address}。\n\n"
        navigation_text += f"总距离：{total_distance_km:.2f} 公里，预计耗时：{total_duration_min} 分钟。\n\n"
        navigation_text += "详细路线：\n\n"

        # List each step
        for i, step in enumerate(route_result["data"]["paths"][0]["steps"], 1):
            instruction = step["instruction"]
            distance = step["distance"]

            navigation_text += f"{i}. {instruction} ({distance}米)\n"

        return navigation_text
    except Exception as e:
        return {"error": f"Route planning failed: {str(e)}"}


# utilities functions
def _maps_bicycling_by_coordinates(
    origin_coordinates: str, destination_coordinates: str
) -> Dict[str, Any]:
    """Plans a bicycle route between two coordinates.

    Args:
        origin_coordinates (str): Starting point coordinates in the format "longitude,latitude" (e.g. "116.434307,39.90909")
        destination_coordinates (str): Ending point coordinates in the format "longitude,latitude" (e.g. "116.434307,39.90909")

    Returns:
        Dict[str, Any]: Route information including distance, duration, and turn-by-turn instructions.
        Considers bridges, one-way streets, and road closures. Supports routes up to 500km.
    """
    try:
        response = requests.get(
            "https://restapi.amap.com/v4/direction/bicycling",
            params={
                "key": AMAP_MAPS_API_KEY,
                "origin": origin_coordinates,
                "destination": destination_coordinates,
            },
        )
        response.raise_for_status()
        data = response.json()

        if data.get("errcode") != 0:
            return {
                "error": f"Direction bicycling failed: {data.get('info') or data.get('infocode')}"
            }

        paths = []
        for path in data["data"]["paths"]:
            steps = []
            for step in path["steps"]:
                steps.append(
                    {
                        "instruction": step.get("instruction"),
                        "road": step.get("road"),
                        "distance": step.get("distance"),
                        "orientation": step.get("orientation"),
                        "duration": step.get("duration"),
                    }
                )
            paths.append(
                {
                    "distance": path.get("distance"),
                    "duration": path.get("duration"),
                    "steps": steps,
                }
            )

        return {
            "data": {
                "origin": data["data"]["origin"],
                "destination": data["data"]["destination"],
                "paths": paths,
            }
        }
    except requests.exceptions.RequestException as e:
        return {"error": f"Request failed: {str(e)}"}


@mcp.tool()
def maps_walking_by_address(
    origin_address: str,
    destination_address: str,
    origin_city: Optional[str] = None,
    destination_city: Optional[str] = None,
) -> str:
    """Plans a walking route between two locations using addresses. Unless you have a specific reason to use coordinates, it's recommended to use this tool.

    Args:
        origin_address (str): Starting point address (e.g. "北京市朝阳区阜通东大街6号")
        destination_address (str): Ending point address (e.g. "北京市海淀区上地十街10号")
        origin_city (Optional[str]): Optional city name for the origin address to improve geocoding accuracy
        destination_city (Optional[str]): Optional city name for the destination address to improve geocoding accuracy

    Returns:
        str: Route information including distance, duration, and turn-by-turn instructions.
        Supports routes up to 100km.
    """
    try:
        # Convert origin address to coordinates
        origin_result = maps_get_from_location(origin_address, origin_city)
        if "error" in origin_result:
            return {
                "error": f"Failed to geocode origin address: {origin_result['error']}"
            }

        origin_location = origin_result[0]
        time.sleep(0.8)

        # Convert destination address to coordinates
        destination_result = maps_get_from_location(
            destination_address, destination_city
        )
        if "error" in destination_result:
            return {
                "error": f"Failed to geocode destination address: {destination_result['error']}"
            }

        destination_location = destination_result[0]
        if not destination_location:
            return {
                "error": "Could not extract coordinates from destination geocoding result"
            }
        time.sleep(0.8)

        # Use the coordinates to plan the walking route
        route_result = _maps_direction_walking_by_coordinates(
            origin_location, destination_location
        )

        # Add address information to the result
        if "error" not in route_result:
            route_result["addresses"] = {
                "origin": {"address": origin_address, "coordinates": origin_location},
                "destination": {
                    "address": destination_address,
                    "coordinates": destination_location,
                },
            }

        route = route_result.get("route", {})
        addresses = route_result.get("addresses", {})

        if not route or not addresses:
            return "Invalid navigation data provided."

        origin_address = addresses.get("origin", {}).get("address", "Unknown Origin")
        destination_address = addresses.get("destination", {}).get(
            "address", "Unknown Destination"
        )

        paths = route.get("paths", [])
        if not paths:
            return "No paths found in the navigation data."

        # We'll format the first path found
        path = paths[0]
        total_distance_m = int(path.get("distance", 0))
        total_duration_s = int(path.get("duration", 0))

        # Convert total distance to kilometers and meters
        total_distance_km = total_distance_m / 1000

        # Convert total duration to minutes and seconds
        total_duration_min = total_duration_s // 60
        total_duration_sec = total_duration_s % 60

        output_string = f"导航路线：从 {origin_address} 到 {destination_address}\n"
        output_string += f"总距离：{total_distance_km:.2f} 公里\n"
        output_string += (
            f"预计步行时间：{total_duration_min} 分 {total_duration_sec} 秒\n"
        )
        output_string += "\n详细步骤：\n"

        steps = path.get("steps", [])
        for i, step in enumerate(steps, 1):
            instruction = step.get("instruction", "未知指令")
            distance = step.get("distance", "未知")

            # Check if a road name is provided
            road = step.get("road", [])
            if road:
                road_name = road[0] if isinstance(road, list) else road
                output_string += f"{i}. {instruction.replace('沿步行街', f'沿{road_name}')}，距离：{distance} 米\n"
            else:
                output_string += f"{i}. {instruction}，距离：{distance} 米\n"

        return output_string
    except Exception as e:
        return {"error": f"Route planning failed: {str(e)}"}


# utility functions
def _maps_direction_walking_by_coordinates(
    origin: str, destination: str
) -> Dict[str, Any]:
    """步行路径规划 API 可以根据输入起点终点经纬度坐标规划100km 以内的步行通勤方案，并且返回通勤方案的数据

    Args:
        origin (str): 起点经纬度坐标，格式为"经度,纬度" (例如："116.434307,39.90909")
        destination (str): 终点经纬度坐标，格式为"经度,纬度" (例如："116.434307,39.90909")

    Returns:
        Dict[str, Any]: 包含距离、时长和详细导航信息的路线数据
    """
    try:
        response = requests.get(
            "https://restapi.amap.com/v3/direction/walking",
            params={
                "key": AMAP_MAPS_API_KEY,
                "origin": origin,
                "destination": destination,
            },
        )
        response.raise_for_status()
        data = response.json()

        if data["status"] != "1":
            return {
                "error": f"Direction Walking failed: {data.get('info') or data.get('infocode')}"
            }

        paths = []
        for path in data["route"]["paths"]:
            steps = []
            for step in path["steps"]:
                steps.append(
                    {
                        "instruction": step.get("instruction"),
                        "road": step.get("road"),
                        "distance": step.get("distance"),
                        "orientation": step.get("orientation"),
                        "duration": step.get("duration"),
                    }
                )
            paths.append(
                {
                    "distance": path.get("distance"),
                    "duration": path.get("duration"),
                    "steps": steps,
                }
            )

        return {
            "route": {
                "origin": data["route"]["origin"],
                "destination": data["route"]["destination"],
                "paths": paths,
            }
        }
    except requests.exceptions.RequestException as e:
        return {"error": f"Request failed: {str(e)}"}


@mcp.tool()
def maps_driving_by_address(
    origin_address: str,
    destination_address: str,
    origin_city: Optional[str] = None,
    destination_city: Optional[str] = None,
) -> str:
    """Plans a driving route between two locations using addresses. Unless you have a specific reason to use coordinates, it's recommended to use this tool.

    Args:
        origin_address (str): Starting point address (e.g. "北京市朝阳区阜通东大街6号")
        destination_address (str): Ending point address (e.g. "北京市海淀区上地十街10号")
        origin_city (Optional[str]): Optional city name for the origin address to improve geocoding accuracy
        destination_city (Optional[str]): Optional city name for the destination address to improve geocoding accuracy

    Returns:
        str: Route information including distance, duration, and turn-by-turn instructions.
        Considers traffic conditions and road restrictions.
    """
    try:
        origin_result = maps_get_from_location(origin_address, origin_city)
        if "error" in origin_result:
            return {
                "error": f"Failed to geocode origin address: {origin_result['error']}"
            }

        origin_location = origin_result[0]
        time.sleep(0.8)

        # Convert destination address to coordinates
        destination_result = maps_get_from_location(
            destination_address, destination_city
        )
        if "error" in destination_result:
            return {
                "error": f"Failed to geocode destination address: {destination_result['error']}"
            }

        destination_location = destination_result[0]
        if not destination_location:
            return {
                "error": "Could not extract coordinates from destination geocoding result"
            }
        time.sleep(0.8)

        # Use the coordinates to plan the driving route
        route_result = _maps_direction_driving_by_coordinates(
            origin_location, destination_location
        )

        # Add address information to the result
        if "error" not in route_result:
            route_result["addresses"] = {
                "origin": {"address": origin_address, "coordinates": origin_location},
                "destination": {
                    "address": destination_address,
                    "coordinates": destination_location,
                },
            }

        route = route_result.get("route", {})
        addresses = route_result.get("addresses", {})

        if not route or not addresses:
            return "Invalid navigation data provided."

        origin_address = addresses.get("origin", {}).get("address", "Unknown Origin")
        destination_address = addresses.get("destination", {}).get(
            "address", "Unknown Destination"
        )

        paths = route.get("paths", [])
        if not paths:
            return "No paths found in the navigation data."

        # We'll format the first path found
        path = paths[0]
        total_distance_m = int(path.get("distance", 0))
        total_duration_s = int(path.get("duration", 0))

        # Convert total distance to kilometers and meters
        total_distance_km = total_distance_m / 1000

        # Convert total duration to minutes and seconds
        total_duration_min = total_duration_s // 60
        total_duration_sec = total_duration_s % 60

        output_string = f"导航路线：从 {origin_address} 到 {destination_address}\n"
        output_string += f"总距离：{total_distance_km:.2f} 公里\n"
        output_string += (
            f"预计步行时间：{total_duration_min} 分 {total_duration_sec} 秒\n"
        )
        output_string += "\n详细步骤：\n"

        steps = path.get("steps", [])
        for i, step in enumerate(steps, 1):
            instruction = step.get("instruction", "未知指令")
            distance = step.get("distance", "未知")

            # Check if a road name is provided
            road = step.get("road", [])
            if road:
                road_name = road[0] if isinstance(road, list) else road
                output_string += f"{i}. {instruction.replace('沿步行街', f'沿{road_name}')}，距离：{distance} 米\n"
            else:
                output_string += f"{i}. {instruction}，距离：{distance} 米\n"

        return output_string
    except Exception as e:
        return {"error": f"Route planning failed: {str(e)}"}


def _maps_direction_driving_by_coordinates(
    origin: str, destination: str
) -> Dict[str, Any]:
    """驾车路径规划 API 可以根据用户起终点经纬度坐标规划以小客车、轿车通勤出行的方案，并且返回通勤方案的数据

    Args:
        origin (str): 起点经纬度坐标，格式为"经度,纬度" (例如："116.434307,39.90909")
        destination (str): 终点经纬度坐标，格式为"经度,纬度" (例如："116.434307,39.90909")

    Returns:
        Dict[str, Any]: 包含距离、时长和详细导航信息的路线数据
    """
    try:
        response = requests.get(
            "https://restapi.amap.com/v3/direction/driving",
            params={
                "key": AMAP_MAPS_API_KEY,
                "origin": origin,
                "destination": destination,
            },
        )
        response.raise_for_status()
        data = response.json()

        if data["status"] != "1":
            return {
                "error": f"Direction Driving failed: {data.get('info') or data.get('infocode')}"
            }

        paths = []
        for path in data["route"]["paths"]:
            steps = []
            for step in path["steps"]:
                steps.append(
                    {
                        "instruction": step.get("instruction"),
                        "road": step.get("road"),
                        "distance": step.get("distance"),
                        "orientation": step.get("orientation"),
                        "duration": step.get("duration"),
                    }
                )
            paths.append(
                {
                    "path": path.get("path"),
                    "distance": path.get("distance"),
                    "duration": path.get("duration"),
                    "steps": steps,
                }
            )

        return {
            "route": {
                "origin": data["route"]["origin"],
                "destination": data["route"]["destination"],
                "paths": paths,
            }
        }
    except requests.exceptions.RequestException as e:
        return {"error": f"Request failed: {str(e)}"}


@mcp.tool()
def maps_direction(
    origin_address: str,
    destination_address: str,
    origin_city: str,
    destination_city: str,
) -> str:
    """Plans a public transit route between two locations using addresses. Unless you have a specific reason to use coordinates, it's recommended to use this tool.

    Args:
        origin_address (str): Starting point address (e.g. "北京市朝阳区阜通东大街6号")
        destination_address (str): Ending point address (e.g. "北京市海淀区上地十街10号")
        origin_city (str): City name for the origin address (required for cross-city transit)
        destination_city (str): City name for the destination address (required for cross-city transit)

    Returns:
        str: Route information including distance, duration, and detailed transit instructions.
        Considers various public transit options including buses, subways, and trains.
    """
    try:
        origin_result = maps_get_from_location(origin_address, origin_city)
        if "error" in origin_result:
            return {
                "error": f"Failed to geocode origin address: {origin_result['error']}"
            }

        origin_location = origin_result[0]
        time.sleep(0.8)

        # Convert destination address to coordinates
        destination_result = maps_get_from_location(
            destination_address, destination_city
        )
        if "error" in destination_result:
            return {
                "error": f"Failed to geocode destination address: {destination_result['error']}"
            }

        destination_location = destination_result[0]
        if not destination_location:
            return {
                "error": "Could not extract coordinates from destination geocoding result"
            }
        time.sleep(0.8)

        # Use the coordinates to plan the driving route
        route_result = _maps_direction_by_coordinates(
            origin_location, destination_location, origin_city, destination_city
        )

        # Add address information to the result
        if "error" not in route_result:
            route_result["addresses"] = {
                "origin": {"address": origin_address, "coordinates": origin_location},
                "destination": {
                    "address": destination_address,
                    "coordinates": destination_location,
                },
            }

        route = route_result.get("route", {})
        address = route_result.get("addresses", {})
        origin_coords = address.get("origin", {}).get(
            "address", "Original address invalid"
        )
        destination_coords = address.get("destination", {}).get(
            "address", "Destination address invalid"
        )

        transits = route.get("transits", [])

        if not transits:
            return "No transit routes found."

        output = f"导航路线：\n从 {origin_coords} 到 {destination_coords}\n\n"

        # We will only format the first three transit options for brevity and clarity
        for i, transit in enumerate(transits[:3], 1):
            duration_s = int(transit.get("duration", 0))
            duration_min = duration_s // 60
            duration_sec = duration_s % 60

            output += f"--- 方案 {i} ---\n"
            output += f"总用时：约 {duration_min} 分 {duration_sec} 秒\n"

            segments = transit.get("segments", [])
            for segment in segments:
                # Handle walking segments
                walking_data = segment.get("walking")
                if walking_data and walking_data.get("distance"):
                    dist_m = int(walking_data["distance"])
                    dist_km = dist_m / 1000
                    output += f" - 步行：{dist_m} 米\n"
                    # Add detailed walking steps if available
                    steps = walking_data.get("steps", [])
                    for step in steps:
                        instruction = step.get("instruction", "未知指令")
                        output += f"    -> {instruction}\n"

                # Handle bus/subway segments
                bus_data = segment.get("bus")
                if bus_data:
                    buslines = bus_data.get("buslines", [])
                    if buslines:
                        for busline in buslines:
                            line_name = busline.get("name", "未知线路")
                            departure_stop = busline.get("departure_stop", {}).get(
                                "name", "未知站"
                            )
                            arrival_stop = busline.get("arrival_stop", {}).get(
                                "name", "未知站"
                            )
                            bus_duration_s = int(busline.get("duration", 0))
                            bus_duration_min = bus_duration_s // 60
                            bus_duration_sec = bus_duration_s % 60

                            output += f" - 乘坐 {line_name}\n"
                            output += f"   从 {departure_stop} 站上车，在 {arrival_stop} 站下车\n"
                            output += f"   乘车时间：约 {bus_duration_min} 分 {bus_duration_sec} 秒\n"

        return output.strip()
    except Exception as e:
        return {"error": f"Route planning failed: {str(e)}"}


@mcp.tool()
def _maps_direction_by_coordinates(
    origin: str, destination: str, city: str, cityd: str
) -> Dict[str, Any]:
    """根据用户起终点经纬度坐标规划综合各类公共（火车、公交、地铁）交通方式的通勤方案，并且返回通勤方案的数据，跨城场景下必须传起点城市与终点城市

    Args:
        origin (str): 起点经纬度坐标，格式为"经度,纬度" (例如："116.434307,39.90909")
        destination (str): 终点经纬度坐标，格式为"经度,纬度" (例如："116.434307,39.90909")
        city (str): 起点城市名称
        cityd (str): 终点城市名称

    Returns:
        Dict[str, Any]: 包含距离、时长和详细公共交通信息的路线数据
    """
    try:
        response = requests.get(
            "https://restapi.amap.com/v3/direction/transit/integrated",
            params={
                "key": AMAP_MAPS_API_KEY,
                "origin": origin,
                "destination": destination,
                "city": city,
                "cityd": cityd,
            },
        )
        response.raise_for_status()
        data = response.json()

        if data["status"] != "1":
            return {
                "error": f"Direction Transit Integrated failed: {data.get('info') or data.get('infocode')}"
            }

        transits = []
        if data["route"].get("transits"):
            for transit in data["route"]["transits"]:
                segments = []
                if transit.get("segments"):
                    for segment in transit["segments"]:
                        walking_steps = []
                        walking_data = segment.get("walking", {})
                        if walking_data and walking_data.get("steps"):
                            steps_data = walking_data["steps"]
                            if isinstance(steps_data, list):
                                for step in steps_data:
                                    if isinstance(step, dict):
                                        walking_steps.append(
                                            {
                                                "instruction": step.get("instruction"),
                                                "road": step.get("road"),
                                                "distance": step.get("distance"),
                                                "action": step.get("action"),
                                                "assistant_action": step.get(
                                                    "assistant_action"
                                                ),
                                            }
                                        )

                        buslines = []
                        if segment.get("bus", {}).get("buslines"):
                            for busline in segment["bus"]["buslines"]:
                                via_stops = []
                                via_stops_data = busline.get("via_stops", [])
                                if via_stops_data:
                                    # Handle both list and dict cases for via_stops
                                    if isinstance(via_stops_data, list):
                                        for stop in via_stops_data:
                                            if isinstance(stop, dict):
                                                via_stops.append(
                                                    {"name": stop.get("name")}
                                                )
                                            else:
                                                via_stops.append({"name": str(stop)})
                                    else:
                                        via_stops.append({"name": str(via_stops_data)})

                                # Handle departure_stop and arrival_stop safely
                                departure_stop_data = busline.get("departure_stop", {})
                                arrival_stop_data = busline.get("arrival_stop", {})

                                buslines.append(
                                    {
                                        "name": busline.get("name"),
                                        "departure_stop": {
                                            "name": (
                                                departure_stop_data.get("name")
                                                if isinstance(departure_stop_data, dict)
                                                else str(departure_stop_data)
                                            )
                                        },
                                        "arrival_stop": {
                                            "name": (
                                                arrival_stop_data.get("name")
                                                if isinstance(arrival_stop_data, dict)
                                                else str(arrival_stop_data)
                                            )
                                        },
                                        "distance": busline.get("distance"),
                                        "duration": busline.get("duration"),
                                        "via_stops": via_stops,
                                    }
                                )

                        # Safely handle walking data
                        walking_info = (
                            walking_data if isinstance(walking_data, dict) else {}
                        )

                        # Safely handle entrance and exit data
                        entrance_data = segment.get("entrance", {})
                        exit_data = segment.get("exit", {})
                        railway_data = segment.get("railway", {})

                        segments.append(
                            {
                                "walking": {
                                    "origin": walking_info.get("origin"),
                                    "destination": walking_info.get("destination"),
                                    "distance": walking_info.get("distance"),
                                    "duration": walking_info.get("duration"),
                                    "steps": walking_steps,
                                },
                                "bus": {"buslines": buslines},
                                "entrance": {
                                    "name": (
                                        entrance_data.get("name")
                                        if isinstance(entrance_data, dict)
                                        else str(entrance_data)
                                    )
                                },
                                "exit": {
                                    "name": (
                                        exit_data.get("name")
                                        if isinstance(exit_data, dict)
                                        else str(exit_data)
                                    )
                                },
                                "railway": {
                                    "name": (
                                        railway_data.get("name")
                                        if isinstance(railway_data, dict)
                                        else None
                                    ),
                                    "trip": (
                                        railway_data.get("trip")
                                        if isinstance(railway_data, dict)
                                        else None
                                    ),
                                },
                            }
                        )

                transits.append(
                    {
                        "duration": transit.get("duration"),
                        "walking_distance": transit.get("walking_distance"),
                        "segments": segments,
                    }
                )

        return {
            "route": {
                "origin": data["route"]["origin"],
                "destination": data["route"]["destination"],
                "distance": data["route"].get("distance"),
                "transits": transits,
            }
        }
    except requests.exceptions.RequestException as e:
        return {"error": f"Request failed: {str(e)}"}


@mcp.tool()
def maps_input_prompt(keywords: str) -> str:
    """得到特定输入关键字的提示信息列表

    Args:
        key_words (str): 输入的特定关键词

    Returns:
        str: 返回信息包括提供根据用户输入的关键词查询返回建议列表
    """
    try:
        response = requests.get(
            "https://restapi.amap.com/v3/assistant/inputtips",
            params={
                "key": AMAP_MAPS_API_KEY,
                "keywords": keywords,
            },
        )
        response.raise_for_status()
        data = response.json()
        tips = data.get("tips", [])

        if not tips:
            return "没有找到任何提示信息。"

        output_string = "找到以下地点信息：\n"

        for i, tip in enumerate(tips):
            name = tip.get("name", "未知地点")
            district = tip.get("district", "未知区域")
            address = tip.get("address", "无详细地址")
            address = "无详细地址" if address == [] else address
            location = tip.get("location", "未知坐标")

            output_string += f"---\n"
            output_string += f"地点 {i+1}:\n"
            output_string += f"名称: {name}\n"
            output_string += f"区域: {district}\n"
            output_string += f"地址: {address}\n"
            output_string += f"经纬度: {location}\n"

        return output_string.strip()
    except Exception as e:
        return f"error: encounting errors, {e}"


@mcp.tool()
def maps_distance(origin: str, destination: str, type: str = "0") -> Dict[str, Any]:
    """
    测量两个地点之间的距离。

    该函数调用高德地图API，支持驾车、步行和球面距离测量，并以人类可读的中文格式返回结果。

    Args:
        origins (str): 起点地名。
        destination (str): 终点地名。
        type (str, optional): 距离测量类型。
                              "0": 驾车距离。
                              "1": 步行距离。
                              "3": 球面距离。

    Returns:
        Dict[str, Any]: 一个字典，包含距离、持续时间和成功或错误信息。
                        如果成功，返回格式为：
                        {"result": "从 [起点] 到 [终点] 的距离为 [距离] 公里，预计耗时 [时长] 分钟。"}
                        如果失败，返回格式为：
                        {"error": "错误信息"}
    """
    try:
        origin = maps_get_structured_location(origin)[0]
        time.sleep(0.4)
        destination = maps_get_structured_location(destination)[0]
        time.sleep(0.4)
        origins_coord = maps_get_from_location(origin)[0]
        time.sleep(0.4)
        destination_coord = maps_get_from_location(destination)[0]

        response = requests.get(
            "https://restapi.amap.com/v3/distance",
            params={
                "key": AMAP_MAPS_API_KEY,
                "origins": origins_coord,
                "destination": destination_coord,
                "type": type,
            },
        )
        response.raise_for_status()
        data = response.json()

        if data["status"] != "1":
            error_msg = data.get("info") or data.get("infocode")
            return {"error": f"距离查询失败：{error_msg}"}

        results = data["results"][0]
        distance_meters = int(results.get("distance", 0))
        duration_seconds = int(results.get("duration", 0))

        # 转换为人类可读的格式
        distance_km = distance_meters / 1000
        duration_minutes = duration_seconds // 60
        duration_hours = duration_minutes // 60
        remaining_minutes = duration_minutes % 60

        type_map = {"0": "驾车", "1": "步行", "3": "球面"}

        mode = type_map.get(type, "距离")

        duration_str = ""
        if duration_hours > 0:
            duration_str += f"{duration_hours} 小时"
        if remaining_minutes > 0:
            duration_str += f"{remaining_minutes} 分钟"

        if not duration_str:
            duration_str = "无预计耗时"

        # 根据类型构造不同的返回字符串
        if type in ["0", "1"]:
            result_str = f"从 {origin} 到 {destination} 的{mode}距离约为 {distance_km:.2f} 公里，预计耗时 {duration_str}。"
        else:
            result_str = (
                f"从 {origin} 到 {destination} 的球面距离约为 {distance_km:.2f} 公里。"
            )

        return {"result": result_str}

    except requests.exceptions.RequestException as e:
        return {"error": f"请求失败：{str(e)}"}
    except IndexError:
        return {"error": "无法解析地点信息，请检查输入的地点名称。"}
    except Exception as e:
        return {"error": f"发生未知错误：{str(e)}"}


@mcp.tool()
def maps_poi_search(keywords: str, city: str = "", citylimit: str = "false") -> str:
    """关键词搜索 API 根据用户输入的关键字进行 POI 搜索，并返回相关的信息

    Args:
        keywords (str): 用户输入的关键词
        city (str, optional): 城市名. Defaults to "".
        citylimit (str, optional): Defaults to "false".

    Returns:
        str: 返回根据关键词和城市约束的 POI 搜索结果
    """
    try:
        response = requests.get(
            "https://restapi.amap.com/v3/place/text",
            params={
                "key": AMAP_MAPS_API_KEY,
                "keywords": keywords,
                "city": city,
                "citylimit": citylimit,
            },
        )
        response.raise_for_status()
        data = response.json()

        if not data or data["status"] != "1":
            return {
                "error": f"Text Search failed: {data.get('info') or data.get('infocode')}"
            }

        pois = data.get("pois", [])
        if not pois:
            return "No POI information found."

        output_lines = []

        # Process each POI item in the list
        for i, poi in enumerate(pois):
            # Use a horizontal line to separate each POI for clarity
            if i > 0:
                output_lines.append("-" * 20)

            # Basic POI information
            name = poi.get("name", "N/A")
            poi_type = poi.get("type", "N/A")
            address = poi.get("address", "N/A")
            city = poi.get("cityname", "N/A")
            adname = poi.get("adname", "N/A")

            output_lines.append(f"Name: {name}")
            output_lines.append(f"Type: {poi_type}")
            output_lines.append(f"Address: {address}, {adname}, {city}")

            # Additional details from biz_ext
            biz_ext = poi.get("biz_ext", {})
            if biz_ext:
                rating = biz_ext.get("rating")
                cost = biz_ext.get("cost")

                if rating:
                    output_lines.append(f"Rating: {rating}")
                if cost:
                    output_lines.append(f"Cost: {cost}")

            # Location coordinates
            location = poi.get("location")
            if location:
                output_lines.append(
                    f"Location (Lat, Lon): {location.split(',')[1].strip()}, {location.split(',')[0].strip()}"
                )

            # Telephone numbers
            tel = poi.get("tel")
            if tel:
                output_lines.append(f"Tel: {tel}")

            # Photos
            photos = poi.get("photos", [])
            if photos:
                photo_urls = [p.get("url", "N/A") for p in photos]
                output_lines.append(f"Photos ({len(photos)} available):")
                for url in photo_urls:
                    output_lines.append(f"  - {url}")
        return "\n".join(output_lines)
    except requests.exceptions.RequestException as e:
        return {"error": f"Request failed: {str(e)}"}


@mcp.tool()
def maps_around_search(location: str, radius: str = "1000", keywords: str = "") -> str:
    """周边搜，根据用户传入坐标 location 的地点信息和提示词，搜索出 radius 半径范围的POI

    Args:
        location (str): 用户传入的地点信息，支持模糊搜索，例如 "南京夫子庙" 等。
        radius (str, optional): 以坐标为中心的搜索半径（单位：米）. Defaults to "1000".
        keywords (str, optional): 关键字约束. Defaults to "".

    Returns:
        str: 周边搜的相关信息，包括名称、地址和相关店铺 ID
    """
    try:
        # get structured location
        location = maps_get_structured_location(location)[0]
        time.sleep(0.8)
        location_coordinate = maps_get_from_location(location)
        time.sleep(0.8)
        response = requests.get(
            "https://restapi.amap.com/v3/place/around",
            params={
                "key": AMAP_MAPS_API_KEY,
                "location": location_coordinate,
                "radius": radius,
                "keywords": keywords,
            },
        )
        response.raise_for_status()
        data = response.json()

        if data["status"] != "1":
            return {
                "error": f"Around Search failed: {data.get('info') or data.get('infocode')}"
            }

        pois_list = []
        for poi in data.get("pois", []):
            pois_list.append(
                {
                    "id": poi.get("id"),
                    "name": poi.get("name"),
                    "address": poi.get("address"),
                    "typecode": poi.get("typecode"),
                }
            )
        keywords = keywords if keywords != "" else "无"
        formatted_strings = [
            f"在 {location} 周围 {radius} 米的景点 (Restriction: {keywords})"
        ]
        for poi in pois_list:
            name = poi.get("name", "N/A")
            address = poi.get("address", "N/A")
            poi_id = poi.get("id", "N/A")
            formatted_strings.append(f"名称: {name}\n地址: {address}\nID: {poi_id}\n")

        return "\n".join(formatted_strings)

    except requests.exceptions.RequestException as e:
        return {"error": f"Request failed: {str(e)}"}


if __name__ == "__main__":
    mcp.run()