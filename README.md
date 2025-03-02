# Snowboarding assistant: Let AI plan your trips to the mountains :mountain: :snowboarder:

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Overview
So you're all about the adventure, but not about the planning? Snowboarding assistant is an AI agent that helps you plan your season and trips so you make the most of the snow! Find the best resorts for your skill level and interests, get live weather forecasts for destinations, find beginner-friendly slopes and trails, get recommendations for gear and equipment, and more. Built by a snowboarder for snowboarders, using a snowboarder-friendly AI agent! Have fun and stay warm!

Example of how you can super-charge your snowboarding journey with this assistant :rocket:

![Example chat screenshot](assets/example-4-mini.png)

## Quick Start
We currently only support running the assistant locally on MacOS (Sonoma). Inference only on Groq since snowboarders love blazing fast responses (i.e., inference) :wink:
#### Step 1
First, you can set your Groq API key in the environment variables:
```
export GROQ_API_KEY=<your-groq-api-key>
export TAVILY_API_KEY=<your-tavily-api-key>
```

#### Step 2
Set up a virtual environment and install the dependencies.
```
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### Step 3
Run the streamlit app.
```
python3 -m streamlit run streamlit_app.py
```

#### Step 4
Start planning your season with the assistant on your browser - have fun and stay warm!

## Features
- **AI agent framework**: The assistant is built using Langchain, an AI agent framework with tool use:
    - **Web search**: The assistant can search the web for real-time information like weather, snow conditions, and resort information.
    - **Location-based recommendations**: The assistant can use your location to recommend resorts near you.
- **Natural Language Input**: Describe what you want to do in plain English (or other supported languages).
- **Snowboarder-friendly responses and assistance**: The assistant is designed to be helpful and friendly to snowboarders.
- **Browser-based simple user interface**: Zero-friction to get going.

## Technologies Used
- Llama (open-source large language model)
- Groq (super-fast inference platform)
- Streamlit (Web user interface)
- Tavily (web search)
- Geopy (location services)
- Langchain (AI agent framework)

## Configuration
Snowboarding assistant can be configured through environment variables. Support for config file coming soon.

## License
MIT License. See [LICENSE](LICENSE) for details.

## Requirements
- Python 3.9+
- Groq API key (sign up at https://console.groq.com)
- Tavily API key (sign up at https://tavily.com)

## Dependencies
- streamlit
- groq
- langchain
- geopy
- python-dotenv
- tavily-python

## Troubleshooting
- **API Key Issues**: Ensure your API keys are correctly set in the .env file or as environment variables
- **Location Access**: If location features aren't working, check that you've allowed location access in your browser
- **Rate Limiting**: The application limits requests to 20 per minute to prevent API overuse

## Contributing
See [CONTRIBUTING.md](CONTRIBUTING.md) for information on how to contribute to this project.