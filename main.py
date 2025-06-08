import os
import json
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


def get_weather(city_name: str) -> str:
    """returns the current weather and temperature for a given city name"""

    print(f"Getting weather for {city_name} with get_weather() tool")

    base_url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": city_name,
        "appid": WEATHER_API_KEY,
        "units": "metric"  # Use "imperial" for Fahrenheit
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


print(get_weather("Tel Aviv"))
