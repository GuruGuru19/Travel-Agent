import os
import sys
from collections import defaultdict
from datetime import datetime
from typing import TypedDict

from dotenv import load_dotenv

from langchain.chat_models import init_chat_model
from langchain_core.tools import tool

from langgraph.prebuilt import ToolNode
from langgraph.graph import StateGraph, START, END

import requests

load_dotenv()

DEBUG = '-d' in sys.argv

WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
CHAT_MODEL = os.getenv("CHAT_MODEL")

system_prompt = f"""Today is {datetime.today().strftime("%A, %B %d, %Y")}.
You are George, a helpful, friendly, and efficient travel agent. Your goal is to assist users with 
travel-related queries, including weather forecasts, travel tips, destinations, and planning.

Use tools when needed, and respond clearly and concisely. Avoid unnecessary explanations. Prefer bullet points for 
lists. If unsure or lacking information, say so briefly and suggest alternatives.

Never suggest help if you are missing the tools to do so. If you're not sure ask the user to clarify data.

To suggest what to pack, first determine the weather, then consider local customs, and finally list essential items.

Stay professional, polite, and proactive.
"""


class ChatState(TypedDict):
    messages: list


# tools
@tool
def get_weather_current(city_name: str) -> str:
    """returns the current weather and temperature for a given city name"""

    if DEBUG:
        print(f"!!! Getting weather for {city_name} with get_weather() tool")

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
    if DEBUG:
        print(f"!!! Getting weather forecast for {city_name} with get_weather_forecast() tool")
    base_url = "https://api.openweathermap.org/data/2.5/forecast"
    params = {
        "q": city_name,
        "appid": WEATHER_API_KEY,
        "units": "metric"
    }

    response = requests.get(base_url, params=params)
    data = response.json()

    if response.status_code != 200 or "list" not in data:
        return f"Error: Could not get weather for '{city_name}'. Possible reasons: invalid city name or network issue."

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


tool_list = [get_weather_forecast, get_weather_current]

agent_llm = init_chat_model(CHAT_MODEL, model_provider="ollama")
agent_llm = agent_llm.bind_tools(tool_list)


def interpreter_node(state):
    """use the LLM to generate the next step. it could be a tool all or just a 'final answer' response"""
    response = agent_llm.invoke(state['messages'])
    return {'messages': state['messages'] + [response]}


def router_node(state):
    last_message = state['messages'][-1]
    return 'tools' if getattr(last_message, 'tool_calls', None) else 'end'


tool_node = ToolNode(tool_list)


def tools_node(state):
    result = tool_node.invoke(state)

    return {
        'messages': state['messages'] + result['messages']
    }


builder = StateGraph(ChatState)
builder.add_node('interpreter', interpreter_node)
builder.add_node('tools', tools_node)

builder.add_edge(START, 'interpreter')
builder.add_edge('tools', 'interpreter')
builder.add_conditional_edges('interpreter', router_node, {'tools': 'tools', 'end': END})

graph = builder.compile()


def separate_thoughts(msg: str) -> tuple[str, str]:
    """Separates <think> content from the rest of the message.
    Returns tuple of (thought_content, main_message)"""
    think_start = msg.find("<think>")
    think_end = msg.find("</think>")

    if think_start == -1 or think_end == -1:
        return "", msg.strip()  # No thoughts found

    thought_content = msg[think_start + 7:think_end].strip()
    main_message = (msg[:think_start] + msg[think_end + 8:]).strip()

    return thought_content, main_message


if __name__ == '__main__':
    state = {'messages': [{'role': 'system', 'content': system_prompt}]}

    print('Type an instruction or "/q".\n')

    while True:
        user_message = input('> ')

        if user_message.lower() == '/q':
            break

        state['messages'].append({'role': 'user', 'content': user_message})

        state = graph.invoke(state)

        # Get the last message (AI response)
        last_thoughts, last_message = separate_thoughts(state['messages'][-1].content)

        if DEBUG:
            print(f"AI thoughts:\n{last_thoughts}\nFinal Answer:")

        print(last_message, '\n')
