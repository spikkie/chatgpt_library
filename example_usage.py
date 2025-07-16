import asyncio
import datetime

from chatgpt_automation import ask_chatgpt
from config import Settings

settings = Settings()


CHATGPT_PROJECT_URL = settings.get("CHATGPT_PROJECT_URL")
EMAIL = settings.get("EMAIL")
PASSWORD = settings.get("PASSWORD")


async def main():
    url = CHATGPT_PROJECT_URL
    email = EMAIL
    password = PASSWORD
    current_date = datetime.datetime.now(datetime.timezone.utc)

    prompt = f"""
        {current_date}
        Extract the text from the image and output as structured JSON in text, at the end add key-value finished: finished
    """

    file_path = "myfile.jpg"

    result = await ask_chatgpt(
        url, email, password, prompt, file_path=file_path, expect_json=True
    )
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
