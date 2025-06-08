import os
import json
from collections import defaultdict
from datetime import datetime
from typing import TypedDict

from dotenv import load_dotenv

from langchain.chat_models import init_chat_model
from langchain_core.tools import tool

from langgraph.prebuilt import ToolNode
from langgraph.graph import StateGraph, START, END

load_dotenv()

WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
CHAT_MODEL = "qwen3:4b"


class ChatState(TypedDict):
    messages: list


# tools
import requests


@tool
def get_weather_current(city_name: str) -> str:
    """returns the current weather and temperature for a given city name"""

    print(f"Getting weather for {city_name} with get_weather() tool")

    base_url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": city_name,
        "appid": WEATHER_API_KEY,
        "units": "metric"
    }

    response = requests.get(base_url, params=params)
    if response.status_code != 200:
        return f"Error: Unable to fetch weather data for '{city_name}'. error: {response.text}"

    data = response.json()
    temp = data['main']['temp']
    description = data['weather'][0]['description']
    city = data['name']
    country = data['sys']['country']

    return f"The weather in {city}, {country} is {description} with a temperature of {temp}°C."


@tool
def get_weather_forecast(city_name: str) -> str:
    """Returns the weather and temperature forecast for the next 5 days with a given city name."""
    base_url = "https://api.openweathermap.org/data/2.5/forecast"
    params = {
        "q": city_name,
        "appid": WEATHER_API_KEY,
        "units": "metric"
    }

    response = requests.get(base_url, params=params)
    data = response.json()

    if response.status_code != 200 or "list" not in data:
        return f"Error: Could not get weather for '{city_name}'. Please check the city name or try again later."

    # Get current weather from first forecast entry
    first = data['list'][0]
    current_weather = first['weather'][0]['description'].capitalize()
    current_temp = first['main']['temp']
    current_summary = f"Current weather in {city_name}: {current_weather}, {current_temp:.1f}°C."

    # Group forecasts by date with weather descriptions
    daily_data = defaultdict(list)
    for item in data['list']:
        date = item['dt_txt'].split()[0]
        temp_min = item['main']['temp_min']
        temp_max = item['main']['temp_max']
        weather_desc = item['weather'][0]['description']
        daily_data[date].append((temp_min, temp_max, weather_desc))

    # Format daily forecasts (skip today if partial)
    forecast_lines = []
    today = datetime.now().strftime('%Y-%m-%d')
    for date, entries in sorted(daily_data.items()):
        if date == today:
            continue  # skip partial data for today
        min_temp = min(e[0] for e in entries)
        max_temp = max(e[1] for e in entries)

        # Collect most frequent weather description
        descriptions = [e[2] for e in entries]
        most_common_desc = max(set(descriptions), key=descriptions.count).capitalize()

        date_label = datetime.strptime(date, '%Y-%m-%d').strftime('%A')
        forecast_lines.append(f"{date_label}: {most_common_desc}, {min_temp:.1f}°C – {max_temp:.1f}°C")

    forecast_summary = "\n".join(forecast_lines)
    return f"{current_summary}\nTemperature & weather forecast:\n{forecast_summary}"


print(get_weather_forecast("New York"))
