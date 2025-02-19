#!/usr/bin/env python3

import logging
import multiprocessing
import random
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
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
                    filtered_options = [
                        option
                        for option in options
                        if option.get_attribute("data-value") != "__other_option__"
                    ]
                    chosen_option = (
                        random.choice(filtered_options)
                        if filtered_options
                        else random.choice(options)
                    )
                    chosen_option.scroll_into_view_if_needed()
                    chosen_option.click()
                    time.sleep(0.1)

            submit_button = self.page.locator("div[role='button'][jsname='M2UYVd']")
            submit_button.click()

            self.page.wait_for_url("**/formResponse*")
            return True

        except Exception as e:
            logging.error(f"Error filling form: {str(e)}")
            return False

    def run(self):
        """Run a single form submission."""
        success = self.fill_form()
        if success:
            self.successful_submissions += 1
        else:
            self.failed_submissions += 1
        self.cleanup()
        return success

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


def submission_worker(form_url: str) -> bool:
    """Worker function for handling a single form submission in a separate thread."""
    try:
        form_filler = FormFiller(form_url, submission_count=1)
        return form_filler.run()
    except Exception as e:
        logging.error(f"Worker thread error: {str(e)}")
        return False


def run_threaded_submissions(
    form_url: str, submission_count: int, max_workers: int = None
):
    """Run form submissions using multiple threads."""
    successful_submissions = 0
    failed_submissions = 0
    start_time = time.time()

    # Use CPU count for optimal number of workers
    cpu_count = multiprocessing.cpu_count()
    usable_cpu_count = max(cpu_count // 2, 1)  # Use only half of the available cores
    if max_workers is None:
        max_workers = min(usable_cpu_count, submission_count)

    logging.info(
        f"Starting {submission_count} threaded submissions with {max_workers} workers "
        f"(System has {cpu_count} CPU cores)"
    )

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks and store futures
        futures = [
            executor.submit(submission_worker, form_url)
            for _ in range(submission_count)
        ]

        # Process completed futures as they finish
        for i, future in enumerate(as_completed(futures), 1):
            try:
                if future.result():
                    successful_submissions += 1
                else:
                    failed_submissions += 1

                # Log progress every 5 submissions
                if i % 5 == 0:
                    current_rate = i / (time.time() - start_time)
                    logging.info(
                        f"Completed {i}/{submission_count} submissions. "
                        f"Current rate: {current_rate:.2f}/sec"
                    )

            except Exception as e:
                failed_submissions += 1
                logging.error(f"Future error: {str(e)}")

    # Log final summary
    duration = time.time() - start_time
    logging.info(
        f"""
Thread pool submission completed:
- Total submissions attempted: {submission_count}
- Successful submissions: {successful_submissions}
- Failed submissions: {failed_submissions}
- Time taken: {duration:.2f} seconds
- Average rate: {successful_submissions / duration:.2f} submissions/second
"""
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
        run_threaded_submissions(
            form_url, submission_count
        )  # max_workers will be auto-calculated
    except KeyboardInterrupt:
        logging.info("Operation interrupted by user")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Fatal error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
