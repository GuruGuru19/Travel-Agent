
## Setup
### First - setup Ollama
1. download and install ollama: https://ollama.com/.
2. open your terminal and pull an LLM.
> example:
> ```
> ollama pull qwen3:4b
> ```
you can read and pick an LLM from this list: https://ollama.com/search.


### Second - setup `.env` file
1. make a new file in the project directory named `.env`.
2. insert `CHAT_MODEL=model_name` use the model name that you picked in the ollama setup.
3. insert `WEATHER_API_KEY="your_api_key"` get a free API key from https://openweathermap.org/api.

> example:
> ```text
> CHAT_MODEL="qwen3:4b"
> WEATHER_API_KEY="a1b2c3d4e5f6g7h8"
> ```