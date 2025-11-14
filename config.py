"""
Configuration file for AI Agent
Contains all settings, prompts, and constants
"""

from pathlib import Path

# ============= LLM Configuration =============
LLM_MODEL = "claude-3-5-sonnet-20241022"
LLM_MAX_TOKENS = 8000
LLM_TEMPERATURE = 0.7

# ============= Directory Configuration =============
OUTPUT_DIR = Path("./outputs")
LOG_DIR = Path("./logs")
TASKS_FILE = OUTPUT_DIR / "tasks.json"
HISTORY_FILE = OUTPUT_DIR / "chat_history.json"

# Create directories if they don't exist
OUTPUT_DIR.mkdir(exist_ok=True)
LOG_DIR.mkdir(exist_ok=True)

# ============= Streamlit UI Configuration =============
PAGE_LAYOUT = "wide"
INITIAL_SIDEBAR_STATE = "expanded"

# ============= System Prompts =============
SYSTEM_PROMPTS = {
    "research": """You are an expert AI research assistant with deep knowledge across all domains.
Your role is to provide comprehensive, well-researched answers with accurate information.

Key responsibilities:
- Provide detailed, factual responses
- Use structured formatting with headers and bullet points
- Cite sources when possible
- Acknowledge limitations in knowledge
- Ask clarifying questions when needed""",

    "analysis": """You are an expert data analyst and critical thinker.
Analyze information thoroughly and provide insights.

Focus on:
- Identifying patterns and trends
- Providing evidence-based conclusions
- Highlighting key findings
- Offering actionable recommendations""",

    "writing": """You are an expert writer and editor.
Help create clear, engaging, and well-structured content.

Expertise in:
- Essay and article writing
- Technical documentation
- Creative writing
- Content editing and improvement"""
}

# ============= Query Keywords =============
QUERY_KEYWORDS = {
    "research": ["research", "find", "search", "look up", "information about"],
    "analysis": ["analyze", "examine", "evaluate", "assess", "review"],
    "writing": ["write", "create", "draft", "compose", "generate"],
    "coding": ["code", "program", "script", "function", "implement"],
    "explain": ["explain", "describe", "tell me about", "what is", "how does"]
}

# ============= API Configuration =============
# API keys are loaded from .env file
ANTHROPIC_API_KEY_NAME = "ANTHROPIC_API_KEY"

# ============= Chat Configuration =============
MAX_CONVERSATION_HISTORY = 50  # Maximum number of messages to keep in memory
CONTEXT_WINDOW_SIZE = 10  # Number of previous messages to include in context

# ============= Output Configuration =============
SAVE_OUTPUTS = True
AUTO_SAVE_CHAT = True
EXPORT_FORMAT = "markdown"  # Options: markdown, json, txt

# ============= Feature Flags =============
ENABLE_WEB_SEARCH = True
ENABLE_FILE_UPLOAD = True
ENABLE_KNOWLEDGE_BASE = True
ENABLE_TASK_MANAGEMENT = True
