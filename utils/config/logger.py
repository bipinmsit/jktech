import logging
import sys

# from dotenv import load_dotenv

# # Load environment variables for local development
# if os.getenv("ENVIRONMENT") is None:
#     load_dotenv()

# Get logger
logger = logging.getLogger()
# Create formatter
formatter = logging.Formatter(fmt="%(asctime)s - %(levelname)s - %(message)s")
# Create handlers
stream_handler = logging.StreamHandler(sys.stdout)
# file_handler = logging.FileHandler('app.log')
# Set formatters
stream_handler.setFormatter(formatter)
# file_handler.setFormatter(formatter)
# Add handlers to the logger
logger.addHandler(stream_handler)
# logger.addHandler(file_handler)
# Set log level

# log_level = os.getenv("LOG_LEVEL").upper()
# numeric_level = getattr(logging,log_level)
# logger.setLevel(numeric_level)
