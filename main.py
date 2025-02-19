#!/usr/bin/env python3

import logging
import random
import sys
import time
from playwright.sync_api import sync_playwright, Page, Browser


class FormFiller:
    def __init__(self, form_url: str, submission_count: int):
        self.form_url = form_url
        self.submission_count = submission_count
        self.successful_submissions = 0
        self.failed_submissions = 0
        self.setup_browser()

    def setup_browser(self):
        """Initialize Playwright browser with appropriate options."""
        self.playwright = sync_playwright().start()
        self.browser: Browser = self.playwright.chromium.launch(headless=False)
        self.context = self.browser.new_context()
        self.page: Page = self.context.new_page()
        self.page.set_default_timeout(10000)

    def fill_form(self) -> bool:
        """Fill a single form with random choices."""
        try:
            self.page.goto(self.form_url)

            questions = self.page.locator("div[role='radiogroup']").all()

            for question in questions:
                options = question.locator("div[role='radio']").all()
                if options:
                    random_option = random.choice(options)
                    random_option.scroll_into_view_if_needed()
                    random_option.click()
                    time.sleep(0.1)

            submit_button = self.page.locator("div[role='button'][jsname='M2UYVd']")
            submit_button.click()

            self.page.wait_for_function(
                "() => /\\/formResponse($|\\?)/.test(window.location.href)",
                timeout=8000,
            )
            return True

        except Exception as e:
            logging.error(f"Error filling form: {str(e)}")
            return False

    def run(self):
        """Run the form filling process for the specified number of times."""
        logging.info(
            f"Starting form submission for {self.submission_count} submissions"
        )
        start_time = time.time()

        for i in range(self.submission_count):
            try:
                if self.fill_form():
                    self.successful_submissions += 1
                    if self.successful_submissions % 5 == 0:
                        current_rate = self.successful_submissions / (
                            time.time() - start_time
                        )
                        logging.info(
                            f"Completed {self.successful_submissions}/{self.submission_count} "
                            f"submissions. Rate: {current_rate:.2f}/sec"
                        )
                else:
                    self.failed_submissions += 1

            except Exception as e:
                self.failed_submissions += 1
                logging.error(f"Submission {i+1} failed: {str(e)}")

        duration = time.time() - start_time
        self.log_summary(duration)
        self.cleanup()

    def log_summary(self, duration: float):
        """Log the summary of the form filling process."""
        logging.info(
            f"""
Form submission completed:
- Total submissions attempted: {self.submission_count}
- Successful submissions: {self.successful_submissions}
- Failed submissions: {self.failed_submissions}
- Time taken: {duration:.2f} seconds
- Average rate: {self.successful_submissions / duration:.2f} submissions/second
"""
        )

    def cleanup(self):
        """Clean up resources."""
        try:
            self.context.close()
            self.browser.close()
            self.playwright.stop()
        except Exception as e:
            logging.error(f"Error during cleanup: {str(e)}")


def setup_logging():
    """Set up logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def main():
    """Main entry point of the script."""
    setup_logging()

    form_url = input("Enter the Google Form URL: ")
    while True:
        try:
            submission_count = int(input("Enter the number of submissions to make: "))
            if submission_count > 0:
                break
            print("Please enter a positive number.")
        except ValueError:
            print("Please enter a valid number.")

    try:
        form_filler = FormFiller(form_url, submission_count)
        form_filler.run()
    except KeyboardInterrupt:
        logging.info("Operation interrupted by user")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Fatal error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
