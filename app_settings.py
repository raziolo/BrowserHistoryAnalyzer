import logging
from pathlib import Path

AI_MODELS = [
    {'name': 'qwen2-0.5b-instruct', 'thinking': False},
    {'name': 'phi-3.1-mini-128k-instruct@q8_0', 'thinking': False},
    {'name': 'granite-3.1-8b-instruct', 'thinking': False},
    {'name': 'deepseek-r1-distill-qwen-32b', 'thinking': True},
    {'name': 'agentica-org_deepscaler-1.5b-preview', 'thinking': True},
    {'name': 'mistral-7b-instruct-v0.3', 'thinking': False}, # 5
    {'name': 'gemma-3-4b-it', 'thinking': False}, # 6

]
AI_MODEL_N = 6
AI_MODEL_NAME = AI_MODELS[AI_MODEL_N]['name']  # Default model
AI_MODEL_THINKING = AI_MODELS[AI_MODEL_N]['thinking']  # Default thinking mode

# AI_MODEL_NAME = 'gemma-3-4b-it'  # Override directly if needed


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
LOGGER = logging.getLogger(__name__)

# Shared Configuration
BACKUP_DIR = Path(__file__).parent / "backupManager" / "history_backups"


# CLASSIFIER CONFIGURATION

DAYS_TO_ANALYZE = 31  # Analyze history from last N days

# Configure classification parameters
CLASSIFICATION_PARAMETERS = {
    "categories": [
        # Core verticals
        "Social Media",
        "News",
        "Media",
        "E‑commerce",
        "Shopping",
        "Education",
        "Learning",
        "Video",
        "Streaming",
        "Music",
        "Audio",
        "Technology",
        "Gadgets",
        "Finance",
        "Banking",
        "Health",
        "Fitness",
        "Travel",
        "Transportation",
        "Sports",
        "Government",
        "Politics",
        "Jobs",
        "Career",
        "Lifestyle",
        "Hobbies",
        "Food",
        "Cooking",
        "Real Estate",
        "Science",
        "Research",
        "Art",
        "Culture",
        "Forums",
        "Q&A",
        "Blogs",
        "Personal",
        "Adult",
        "Utilities",
        "Productivity",
        "Search"
        # Fallback
        "Other"
    ],
    "temperature": 0.1, # Lower temperature for more deterministic results, higher for more creative ones
    "max_tokens": 1000  # allow a bit more room for multi‑word labels
}