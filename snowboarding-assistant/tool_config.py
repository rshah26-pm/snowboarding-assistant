import os
import json

TOOL_DESCRIPTIONS_JSON_PATH = os.path.join(os.path.dirname(__file__), "tool_descriptions.json")

# Tool description versions for A/B testing
TOOL_DESCRIPTION_VERSIONS = {
    "web_search": "v1",
    "resort_distance_calculator": "v1"
}

def get_tool_version(tool_name):
    """Get the current version for a specific tool."""
    return TOOL_DESCRIPTION_VERSIONS.get(tool_name, "v1")

def load_tool_descriptions():
    """Load tool descriptions from JSON file."""
    with open(TOOL_DESCRIPTIONS_JSON_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

TOOL_DESCRIPTIONS = load_tool_descriptions()

def get_tool_description(tool_name, version="v1"):
    """Get tool description for a specific tool and version."""
    tool_versions = TOOL_DESCRIPTIONS.get(tool_name, {})
    if version in tool_versions:
        return tool_versions[version]["description"]
    elif "v1" in tool_versions:
        return tool_versions["v1"]["description"]
    else:
        raise ValueError(f"No description found for tool '{tool_name}' and version '{version}'")