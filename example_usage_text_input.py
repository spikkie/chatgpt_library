import asyncio
import datetime

from chatgpt_automation import ask_chatgpt
from config import Settings
from logger import logger

settings = Settings()

CHATGPT_PROJECT_URL = settings.get("CHATGPT_PROJECT_URL")
EMAIL = settings.get("EMAIL")
PASSWORD = settings.get("PASSWORD")

PROMPT_FILE = "prompt_template.txt"


def load_prompt(current_date: datetime.datetime) -> str:
    with open(PROMPT_FILE, "r", encoding="utf-8") as f:
        template = f.read()
    return template.format(current_date=current_date)


async def main():
    url = CHATGPT_PROJECT_URL
    email = EMAIL
    password = PASSWORD
    current_date = datetime.datetime.now(datetime.timezone.utc)

    prompt = load_prompt(current_date)
    logger.debug(prompt)

    # file_path = "myfile.jpg"

    result = await ask_chatgpt(
        # url, email, password, prompt, file_path=file_path, expect_json=True
        url,
        email,
        password,
        prompt,
        expect_json=True,
    )
    logger.info(prompt)


if __name__ == "__main__":
    asyncio.run(main())
