# chatgpt_automation/automation.py

import json
import os
import shutil
import tempfile
from typing import Any, Optional

from logger import logger
from patchright.async_api import async_playwright
from playwright.async_api import Browser, Page


class ChatGPTAutomation:
    def __init__(
        self,
        project_url: str,
        email: str,
        password: str,
        profile_dir: str = "/app/profile",
    ):
        self.project_url = project_url
        self.email = email
        self.password = password
        self.profile_dir = profile_dir

    async def _do_login_if_needed(self, page: Page, browser: Browser) -> bool:
        logger.info("Checking if login is needed for project_url=%s", self.project_url)
        try:
            # Try to find the login button
            await page.wait_for_selector(
                'button[data-testid="login-button"]', timeout=5000
            )
        except Exception as e:
            if type(e).__name__ == "TimeoutError":
                logger.debug("Already logged in (Timeout waiting for login button)")
                return True
            logger.exception("Error waiting for login button")
            return False

        try:
            await page.click('button[data-testid="login-button"]')
            # await page.wait_for_load_state("networkidle")
            await page.wait_for_load_state("domcontentloaded")
            await page.wait_for_timeout(1000)
        except Exception:
            logger.exception("Failed to click login button or load page")
            return False

        try:
            await page.click('button[value="google"]')
            await page.wait_for_timeout(3000)
        except Exception:
            logger.exception("Failed to click Google login button")
            return False

        google_page = page
        if len(browser.pages) > 1:
            google_page = browser.pages[-1]

        try:
            await google_page.wait_for_load_state("domcontentloaded", timeout=10000)
        except Exception:
            logger.warning("Google login page did not load DOMContentLoaded in time")

        try:
            await google_page.click(f'text="{self.email}"', timeout=3000)
        except Exception:
            try:
                await google_page.fill('input[type="email"]', self.email)
                await google_page.click('button:has-text("Next")')
                await google_page.wait_for_timeout(2000)
            except Exception:
                logger.exception("Failed to enter Google email and press Next")
                return False

        try:
            await google_page.fill('input[type="password"]', self.password)
            await google_page.click('button:has-text("Next")')
            await google_page.wait_for_timeout(5000)
        except Exception:
            logger.exception("Failed to enter Google password and press Next")
            return False

        try:
            await page.goto(self.project_url)
        except Exception:
            logger.exception("Failed to navigate back to project URL after login")
            return False

        logger.info("Login successful")
        return True

    async def ask_question(
        self,
        prompt: str,
        file_path: Optional[str] = None,
        expect_json: bool = False,
    ) -> Any:
        logger.info("ask_question called (expect_json=%s)", expect_json)
        temp_dir = tempfile.mkdtemp()
        try:
            logger.debug("Copying profile directory to temporary dir: %s", temp_dir)
            shutil.copytree(
                self.profile_dir, f"{temp_dir}/profile_copy", dirs_exist_ok=True
            )
            async with async_playwright() as p:
                logger.debug("DISPLAY = %s", os.getenv("DISPLAY"))
                browser = await p.chromium.launch_persistent_context(
                    user_data_dir=f"{temp_dir}/profile_copy",
                    # user_data_dir=self.profile_dir,
                    headless=False,
                    # args=[
                    #     "--no-sandbox",
                    #     "--disable-gpu",
                    #     "--disable-dev-shm-usage",
                    #     "--disable-setuid-sandbox",
                    #     "--disable-features=VizDisplayCompositor",
                    # ],
                )
                page = await browser.new_page()
                logger.debug("Navigate to project URL: %s", self.project_url)
                await page.goto(self.project_url)
                logger.debug("Navigated to project URL: %s", self.project_url)
                logged_in = await self._do_login_if_needed(page, browser)
                if not logged_in:
                    logger.error("Login failed for project_url=%s", self.project_url)
                    await browser.close()
                    raise RuntimeError("Login failed")

                if expect_json:
                    # extend the prompt with end of json data, so this marker can be used to wait for
                    json_prompt_default_rules = """
                    JSON GENERATION STRICT RULES:

                        Your goal is to generate one things:

                         You will generate ONE JSON and ONLY ONE valid JSON object.

                        JSON must be strictly valid (Python json.loads() must parse it without error).

                        No explanation, no comments, no extra text — just the JSON block.

                        At the end add the key-value:   "finished": "finished""

                        Wrap the JSON inside a single ```json code block.

                        Once JSON is generated: STOP. No repetition. No extra output.

                    JSON GENERATION ADDITIONAL RULES:

                        All keys must use double quotes.

                        No trailing commas.

                        YOU MUST After generating the JSON: STOP IMMEDIATELY. Do not produce any additional JSON, examples, or text.

                    """

                    json_prompt_end_statement = """

                        --- END OF INSTRUCTION ---
                    """

                    prompt += json_prompt_default_rules + json_prompt_end_statement

                # await page.wait_for_selector("#prompt-textarea", timeout=15000)
                # logger.debug("Prompt textarea available, filling prompt")
                # await page.fill("#prompt-textarea", prompt)
                # if file_path:
                #     logger.info("Uploading file: %s", file_path)
                #     await page.set_input_files('input[type="file"]', file_path)
                # submit_button = page.locator("#composer-submit-button")
                # await submit_button.wait_for(state="visible")
                # logger.debug("Submitting prompt")
                # await submit_button.click()
                # await page.wait_for_timeout(2000)

                await page.wait_for_selector("#prompt-textarea", timeout=15000)
                logger.debug("Prompt textarea available, filling prompt")
                await page.fill("#prompt-textarea", prompt)

                if file_path:
                    logger.info("Uploading file: %s", file_path)
                    await page.set_input_files('input[type="file"]', file_path)

                submit_button = page.locator("#composer-submit-button")

                # Wait up to 30 seconds until the button is both visible and enabled
                logger.debug("Waiting for submit button to be visible and enabled")
                await submit_button.wait_for(state="visible", timeout=30000)

                # Retry loop to ensure button is enabled
                for attempt in range(30):
                    is_enabled = await submit_button.is_enabled()
                    if is_enabled:
                        logger.debug(
                            f"Submit button is enabled (attempt {attempt + 1})"
                        )
                        break
                    logger.debug(
                        f"Submit button still disabled (attempt {attempt + 1}), retrying..."
                    )
                    await page.wait_for_timeout(
                        1000
                    )  # Wait 1 second before next attempt
                else:
                    logger.error(
                        "Submit button did not become enabled after 30 seconds"
                    )
                    raise RuntimeError("Submit button was not enabled in time")

                logger.debug("Submitting prompt now")
                await submit_button.click()

                # Optional: allow UI to update
                await page.wait_for_timeout(2000)

                if expect_json:
                    json_text = await self._wait_and_get_json(page)
                    logger.debug("Received JSON text: %s", json_text)
                    await browser.close()
                    return json.loads(json_text)
                else:
                    response = await self._wait_and_get_response(page)
                    await browser.close()
                    logger.debug("Received text response")
                    return response

        except Exception as e:
            logger.exception("Exception during ask_question %s", e)
            raise

        finally:
            try:
                self._save_profile(temp_dir)
                logger.debug("Profile saved from temp dir: %s", temp_dir)
                logger.debug("run finally")
            except Exception:
                logger.exception("Failed to save profile after question")
            shutil.rmtree(temp_dir, ignore_errors=True)
            logger.debug("Temporary directory cleaned up: %s", temp_dir)

    async def _wait_and_get_json(self, page: Page) -> str:
        logger.info("Waiting for JSON code block to appear in page")
        await page.wait_for_selector("code.language-json", timeout=1200000)
        await page.wait_for_selector(
            'span.hljs-attr:text("finished"), strong[data-start][data-end]:text("finished")'
        )
        logger.debug("JSON code block detected, extracting content")
        return await page.locator(
            "div.contain-inline-size code.language-json"
        ).text_content()

    async def _wait_and_get_response(self, page: Page) -> str:
        logger.info("Waiting for markdown response in page")
        await page.wait_for_selector("div.markdown", timeout=1200000)
        logger.debug("Markdown response detected, extracting content")
        return await page.locator("div.markdown").text_content()

    def _save_profile(self, temp_dir: str):
        app_profile = self.profile_dir
        src_profile = os.path.join(temp_dir, "profile_copy")
        logger.debug("Saving profile from %s to %s", src_profile, app_profile)
        if self._is_dir_empty(app_profile):
            if os.path.isdir(src_profile):
                shutil.rmtree(app_profile, ignore_errors=True)
                shutil.copytree(src_profile, app_profile, dirs_exist_ok=True)
                logger.info("Profile saved to %s", app_profile)
            else:
                logger.warning("Source profile directory missing: %s", src_profile)

    @staticmethod
    def _is_dir_empty(path: str) -> bool:
        empty = not os.path.exists(path) or len(os.listdir(path)) == 0
        logger.debug("Checked if dir is empty: %s -> %s", path, empty)
        return empty


# Quick one-shot helper


async def ask_chatgpt(
    project_url, email, password, prompt, file_path=None, expect_json=False
):
    try:
        logger.info(
            "Starting ask_chatgpt: prompt=%s, file_path=%s, expect_json=%s",
            prompt[:60] + "..." if len(prompt) > 60 else prompt,
            file_path,
            expect_json,
        )
        bot = ChatGPTAutomation(project_url, email, password)
        logger.debug("ChatGPTAutomation instance created: %r", bot)
        resp = await bot.ask_question(
            prompt, file_path=file_path, expect_json=expect_json
        )
    except Exception:
        logger.exception("Exception in ask_chatgpt")
        raise
    return resp
