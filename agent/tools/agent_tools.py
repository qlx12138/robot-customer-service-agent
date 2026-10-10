"""扫地机器人智能客服可调用的业务工具。

位置和天气来自公开实时接口；用户与设备使用记录来自项目本地数据集。
所有对外工具均返回 JSON 字符串，便于模型稳定解析，也便于日志审计。
"""

from __future__ import annotations

import csv
import json
import re
from contextvars import ContextVar
from datetime import datetime
from functools import lru_cache
from ipaddress import ip_address
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

from langchain_core.tools import tool

from rag.rag_service import RagSummarizeService
from utils.config_handler import agent_conf
from utils.logger_handler import logger
from utils.path_tool import get_abs_path


HTTP_TIMEOUT_SECONDS = 8
USER_AGENT = "robot-customer-service-agent/1.0"
MONTH_PATTERN = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")

WEATHER_CODES = {
    0: "晴",
    1: "大部晴朗",
    2: "多云",
    3: "阴",
    45: "雾",
    48: "雾凇",
    51: "小毛毛雨",
    53: "中等毛毛雨",
    55: "强毛毛雨",
    61: "小雨",
    63: "中雨",
    65: "大雨",
    71: "小雪",
    73: "中雪",
    75: "大雪",
    80: "小阵雨",
    81: "中等阵雨",
    82: "强阵雨",
    95: "雷暴",
    96: "雷暴伴小冰雹",
    99: "雷暴伴大冰雹",
}

_request_client_ip: ContextVar[str | None] = ContextVar("request_client_ip", default=None)


class ToolDataError(RuntimeError):
    """外部服务或本地业务数据不可用。"""


def _json(data: dict[str, Any]) -> str:
    return json.dumps(data, ensure_ascii=False, separators=(",", ":"))


def _request_json(url: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    if params:
        url = f"{url}?{urlencode(params)}"
    request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    try:
        with urlopen(request, timeout=HTTP_TIMEOUT_SECONDS) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
        logger.warning("外部接口请求失败: %s (%s)", url, exc)
        raise ToolDataError("外部数据服务暂时不可用，请稍后重试") from exc
    if not isinstance(payload, dict):
        raise ToolDataError("外部数据服务返回了无法识别的格式")
    return payload


def set_request_client_ip(raw_ip: str | None) -> None:
    """保存当前请求的客户端 IP，供无显式参数的定位工具使用。"""
    if not raw_ip:
        _request_client_ip.set(None)
        return
    candidate = raw_ip.split(",", 1)[0].strip()
    try:
        parsed = ip_address(candidate)
    except ValueError:
        logger.warning("忽略无效客户端 IP: %r", candidate)
        _request_client_ip.set(None)
        return
    _request_client_ip.set(str(parsed) if parsed.is_global else None)


@lru_cache(maxsize=1)
def _get_rag_service() -> RagSummarizeService:
    return RagSummarizeService()


def _load_usage_records() -> dict[str, dict[str, dict[str, str]]]:
    data_path = get_abs_path(agent_conf["external_data_path"])
    records: dict[str, dict[str, dict[str, str]]] = {}
    try:
        with open(data_path, "r", encoding="utf-8-sig", newline="") as stream:
            reader = csv.DictReader(stream)
            required = {"用户ID", "特征", "清洁效率", "耗材", "对比", "时间"}
            if not reader.fieldnames or not required.issubset(reader.fieldnames):
                raise ToolDataError(f"使用记录字段不完整，缺少: {sorted(required - set(reader.fieldnames or []))}")
            for row in reader:
                user_id = (row.get("用户ID") or "").strip()
                month = (row.get("时间") or "").strip()
                if not user_id or not MONTH_PATTERN.fullmatch(month):
                    logger.warning("跳过无效使用记录: user_id=%r month=%r", user_id, month)
                    continue
                records.setdefault(user_id, {})[month] = {
                    "用户特征": (row.get("特征") or "").strip(),
                    "清洁效率": (row.get("清洁效率") or "").strip(),
                    "耗材状态": (row.get("耗材") or "").strip(),
                    "同类对比": (row.get("对比") or "").strip(),
                }
    except OSError as exc:
        raise ToolDataError(f"无法读取使用记录文件: {data_path}") from exc
    return records


@tool(description="从扫地机器人知识库检索故障排查、维护保养、选购和使用建议")
def search_product_knowledge(query: str) -> str:
    query = query.strip()
    if len(query) < 2:
        raise ValueError("检索问题至少需要 2 个字符")
    return _get_rag_service().rag_summarize(query)


@tool(description="优先根据客户端公网 IP 获取近似城市和经纬度；无客户端 IP 时使用服务出口 IP，并明确标注来源")
def get_user_location() -> str:
    client_ip = _request_client_ip.get()
    payload = _request_json(f"https://ipwho.is/{client_ip}" if client_ip else "https://ipwho.is/")
    if payload.get("success") is False:
        raise ToolDataError(payload.get("message") or "IP 定位失败")
    city = payload.get("city")
    latitude = payload.get("latitude")
    longitude = payload.get("longitude")
    if not city or latitude is None or longitude is None:
        raise ToolDataError("IP 定位结果缺少城市或经纬度")
    return _json(
        {
            "city": city,
            "region": payload.get("region"),
            "country": payload.get("country"),
            "latitude": latitude,
            "longitude": longitude,
            "timezone": (payload.get("timezone") or {}).get("id"),
            "source": "ipwho.is",
            "ip_scope": "forwarded_client_ip" if client_ip else "service_egress_ip",
            "accuracy_note": "IP 定位仅到城市级，可能受代理或运营商出口影响",
        }
    )


@tool(description="通过 Open-Meteo 获取指定城市的真实实时天气，包括温度、湿度、降水和风速")
def get_weather(city: str) -> str:
    city = city.strip()
    if not city:
        raise ValueError("城市名称不能为空")
    geocoding = _request_json(
        "https://geocoding-api.open-meteo.com/v1/search",
        {"name": city, "count": 1, "language": "zh", "format": "json"},
    )
    results = geocoding.get("results") or []
    if not results:
        raise ToolDataError(f"未找到城市: {city}")
    place = results[0]
    weather = _request_json(
        "https://api.open-meteo.com/v1/forecast",
        {
            "latitude": place["latitude"],
            "longitude": place["longitude"],
            "current": "temperature_2m,relative_humidity_2m,precipitation,weather_code,wind_speed_10m",
            "timezone": "auto",
        },
    )
    current = weather.get("current") or {}
    code = current.get("weather_code")
    if not current or current.get("temperature_2m") is None:
        raise ToolDataError("天气接口未返回有效的实时数据")
    return _json(
        {
            "city": place.get("name", city),
            "admin1": place.get("admin1"),
            "country": place.get("country"),
            "observed_at": current.get("time"),
            "weather": WEATHER_CODES.get(code, f"天气代码 {code}"),
            "temperature_c": current.get("temperature_2m"),
            "relative_humidity_percent": current.get("relative_humidity_2m"),
            "precipitation_mm": current.get("precipitation"),
            "wind_speed_kmh": current.get("wind_speed_10m"),
            "source": "Open-Meteo",
        }
    )


@tool(description="返回 Asia/Shanghai 时区的真实当前月份，格式为 YYYY-MM")
def get_current_month() -> str:
    return datetime.now(ZoneInfo("Asia/Shanghai")).strftime("%Y-%m")


@tool(description="校验用户提供的用户 ID 是否存在于本地设备使用记录中，不推测或随机生成身份")
def validate_user_id(user_id: str) -> str:
    user_id = user_id.strip()
    if not user_id:
        raise ValueError("用户 ID 不能为空")
    records = _load_usage_records()
    if user_id not in records:
        return _json({"valid": False, "user_id": user_id, "message": "未找到该用户的设备使用记录"})
    return _json({"valid": True, "user_id": user_id, "available_months": sorted(records[user_id])})


@tool(description="查询指定用户可生成设备使用报告的月份列表")
def list_available_report_months(user_id: str) -> str:
    user_id = user_id.strip()
    months = sorted(_load_usage_records().get(user_id, {}))
    return _json({"user_id": user_id, "available_months": months, "count": len(months)})


@tool(description="查询指定用户在指定月份的真实本地设备使用记录，用于生成月度报告")
def get_device_usage_record(user_id: str, month: str) -> str:
    user_id = user_id.strip()
    month = month.strip()
    if not MONTH_PATTERN.fullmatch(month):
        raise ValueError("月份格式必须为 YYYY-MM")
    record = _load_usage_records().get(user_id, {}).get(month)
    if not record:
        logger.warning("未检索到用户 %s 在 %s 的使用记录", user_id, month)
        return _json({"found": False, "user_id": user_id, "month": month, "message": "未找到对应月份的使用记录"})
    return _json({"found": True, "user_id": user_id, "month": month, "record": record, "source": "local_csv"})


@tool(description="标记当前任务为设备月度报告生成场景，触发中间件切换报告提示词")
def start_report_generation() -> str:
    return _json({"report_context": True, "message": "已进入设备月度报告生成流程"})
