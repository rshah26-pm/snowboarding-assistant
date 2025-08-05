import json
import os

PROMPT_JSON_PATH = os.path.join(os.path.dirname(__file__), "prompts.json")

def load_prompts():
    with open(PROMPT_JSON_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

PROMPTS = load_prompts()

def get_prompt(prompt_type, version="v1"):
    prompt_versions = PROMPTS.get(prompt_type, {})
    if version in prompt_versions:
        return prompt_versions[version]["prompt"]
    elif "v1" in prompt_versions:
        return prompt_versions["v1"]["prompt"]
    else:
        raise ValueError(f"No prompt found for type '{prompt_type}' and version '{version}'")

def get_prompt_description(prompt_type, version="v1"):
    prompt_versions = PROMPTS.get(prompt_type, {})
    if version in prompt_versions:
        return prompt_versions[version]["description"]
    elif "v1" in prompt_versions:
        return prompt_versions["v1"]["description"]
    else:
        return ""

def list_prompt_types():
    return list(PROMPTS.keys())

def list_versions(prompt_type):
    return list(PROMPTS.get(prompt_type, {}).keys())