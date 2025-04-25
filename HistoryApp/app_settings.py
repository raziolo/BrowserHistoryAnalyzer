import logging
from pathlib import Path


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

DAYS_TO_ANALYZE = 1 # Fallback  # Analyze history from last N days
