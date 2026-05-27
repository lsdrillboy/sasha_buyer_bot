import os

from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN: str = os.environ["BOT_TOKEN"]
CURATOR_USERNAME: str = os.getenv("CURATOR_USERNAME", "")
ADMIN_ID: int = int(os.getenv("ADMIN_ID", "6179488801"))

# Платёжные реквизиты
PAYMENT_CARD: str = os.getenv("PAYMENT_CARD", "0000 0000 0000 0000")
PAYMENT_BANK: str = os.getenv("PAYMENT_BANK", "Сбербанк")
PAYMENT_RECIPIENT: str = os.getenv("PAYMENT_RECIPIENT", "Иванов Иван Иванович")
PAYMENT_AMOUNT: str = os.getenv("PAYMENT_AMOUNT", "5 000 ₽")
