# Project Name

Snowboard assistant helps you plan your season and trips so you make the most of the snow.

## Quick Start
We currently only support running the assistant locally on MacOS (Sonoma) with Groq for inference.
#### Step 1
First, you can set your Groq API key in the environment variables:
```
export GROQ_API_KEY=<your-groq-api-key>
```

#### Step 2
Set up a virtual environment and install the dependencies.
```
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### Step 3
Run the assistant
```
python3 main.py
```

## Usage
Open your terminal and run the main.py file. Follow the prompts to start planning your season!

## Features
- **Natural Language Input**: Describe what you want to do in plain English (or other supported languages).
- **Snowboarder-friendly responses and assistance**: The assistant is designed to be helpful and friendly to snowboarders.

## Technologies Used
- Llama (super-open large language model)
- Groq (super-fast inference platform)

## Configuration
Snowboarding assistant can be configured through environment variables. Support for config file coming soon.

## License
MIT License. See [LICENSE](LICENSE) for details.