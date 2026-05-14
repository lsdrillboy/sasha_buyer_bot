import os

from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN: str = os.environ["BOT_TOKEN"]
CURATOR_USERNAME: str = os.getenv("CURATOR_USERNAME", "")
ADMIN_ID: int = int(os.getenv("ADMIN_ID", "6179488801"))
