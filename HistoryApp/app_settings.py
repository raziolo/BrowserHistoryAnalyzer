import logging
from pathlib import Path

AI_MODELS = [
    {'name': 'qwen2-0.5b-instruct', 'thinking': False}, #0
    {'name': 'phi-3.1-mini-128k-instruct@q8_0', 'thinking': False}, #1
    {'name': 'phi-3.1-mini-128k-instruct@iq3_m', 'thinking': False}, #2
    {'name': 'granite-3.1-8b-instruct', 'thinking': False}, #3
    {'name': 'deepseek-r1-distill-qwen-32b', 'thinking': True}, #4
    {'name': 'agentica-org_deepscaler-1.5b-preview', 'thinking': True}, #5
    {'name': 'mistral-7b-instruct-v0.3', 'thinking': False}, # 6
    {'name': 'gemma-3-4b-it', 'thinking': False}, # 7

]
AI_MODEL_N = 7
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
BACKUP_DIR = Path(__file__).parent.parent / "backupManager" / "history_backups"

# CLASSIFIER CONFIGURATION
import django
django.setup()
from frontend.models import App_Settings

DAYS_TO_ANALYZE = App_Settings.objects.get(name='days_to_analyze').value  # Analyze history from last N days

# Configure classification parameters
CATEGORIES = App_Settings.objects.get(name='categories').value


MAX_TOKENS = App_Settings.objects.get(name='max_tokens').value  # Max tokens for LLM
TEMPERATURE = App_Settings.objects.get(name='temperature').value  # Temperature for LLM