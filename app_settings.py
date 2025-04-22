import logging
from pathlib import Path

# AI_MODEL_NAME = 'qwen2-0.5b-instruct'
# AI_MODEL_NAME = 'phi-3.1-mini-128k-instruct@q8_0'
# AI_MODEL_NAME = 'granite-3.1-8b-instruct'
AI_MODEL_NAME = 'mistral-7b-instruct-v0.3'
'''
AI_MODEL_NAME = 'mistral-7b-instruct-v0.3' 
Runs very good on mid-range GPUs (4060), the output quality is the best of the models tested. 
'''

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
LOGGER = logging.getLogger(__name__)

# Shared Configuration
BACKUP_DIR = Path(__file__).parent / "backupManager" / "history_backups"


# CLASSIFIER CONFIGURATION

DAYS_TO_ANALYZE = 1  # Analyze history from last N days

# Configure classification parameters
CLASSIFICATION_PARAMETERS = {
    "categories": [
        # Core verticals
        "Social Media",
        "News & Media",
        "E‑commerce & Shopping",
        "Education & Learning",
        "Video & Streaming",
        "Music & Audio",
        "Technology & Gadgets",
        "Finance & Banking",
        "Health & Fitness",
        "Travel & Transportation",
        "Sports",
        "Government & Politics",
        "Jobs & Career",
        "Lifestyle & Hobbies",
        "Food & Cooking",
        "Real Estate",
        "Science & Research",
        "Art & Culture",
        "Forums & Q&A",
        "Blogs & Personal",
        "Adult",
        "Utilities & Productivity",
        # Fallback
        "Other"
    ],
    "temperature": 0.1, # Lower temperature for more deterministic results, higher for more creative ones
    "max_tokens": 8  # allow a bit more room for multi‑word labels
}