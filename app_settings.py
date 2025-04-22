import logging

AI_MODEL_NAME = 'qwen2-0.5b-instruct'

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
LOGGER = logging.getLogger(__name__)