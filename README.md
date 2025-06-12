
## Setup
### First - setup Ollama
1. Download and install ollama: https://ollama.com/.
2. Open your terminal and pull an LLM.
> Example:
> ```shell
> ollama pull qwen3:4b
> ```
You can read and pick an LLM from this list: https://ollama.com/search.


### Second - setup `.env` file
1. Make a new file in the project directory named `.env`.
2. Insert `CHAT_MODEL=model_name` use the model name that you picked in the ollama setup.
3. Insert `WEATHER_API_KEY="your_api_key"` get a free API key from https://openweathermap.org/api.

> example:
> ```text
> CHAT_MODEL="qwen3:4b"
> WEATHER_API_KEY="a1b2c3d4e5f6g7h8"
> ```


## Running the code
1. Open your terminal and move to the project directory. 
2. Run:
```shell
    uv run main.py
```
> You can run the script with the `-d` flag to enter 'debug mode' and see the agent's thoughts.
> 
> If you don't have `uv` you can install it using:
> ```shell
> pip install uv
> ```
