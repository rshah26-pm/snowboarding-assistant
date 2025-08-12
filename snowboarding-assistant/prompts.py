import os

PROMPTS_DIR = os.path.join(os.path.dirname(__file__), "prompts")

def get_prompt(prompt_type):
    """Get prompt content from text file"""
    file_path = os.path.join(PROMPTS_DIR, f"{prompt_type}.txt")
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read().strip()
    except FileNotFoundError:
        raise ValueError(f"Prompt file not found: {file_path}")

def list_prompt_types():
    """List all available prompt types based on available text files"""
    if not os.path.exists(PROMPTS_DIR):
        return []
    
    prompt_files = [f for f in os.listdir(PROMPTS_DIR) if f.endswith('.txt')]
    return [f[:-4] for f in prompt_files]  # Remove .txt extension