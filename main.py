#!/usr/bin/env python3

import logging
import multiprocessing
import random
import string
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from playwright.sync_api import Browser, Page, sync_playwright

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

DEFAULT_TIMEOUT = 10000
SUBMIT_BUTTON_SELECTOR = "div[role='button'][jsname='M2UYVd']"
QUESTION_CONTAINER_SELECTOR = "div[role='listitem']"
RADIO_GROUP_SELECTOR = "div[role='radiogroup']"
RADIO_OPTION_SELECTOR = "div[role='radio']"
CHECKBOX_SELECTOR = "div[role='checkbox']"
HEADING_SELECTOR = "div[role='heading']"
INPUT_SELECTOR = "input"
OTHER_OPTION_VALUE = "__other_option__"


class FormFiller:
    def __init__(self, form_url: str):
        self.form_url = form_url
        self.playwright = sync_playwright().start()
        self.browser: Browser = self.playwright.chromium.launch(headless=True)
        self.context = self.browser.new_context()
        self.page: Page = self.context.new_page()
        self.page.set_default_timeout(DEFAULT_TIMEOUT)

    def _generate_email(self) -> str:
        domains = ["example.com", "test.com", "sample.net", "demo.org"]
        username = "".join(random.choices(string.ascii_lowercase, k=8))
        return f"{username}@{random.choice(domains)}"

    def _generate_name(self) -> str:
        first_names = [
            "John",
            "Mary",
            "James",
            "Patricia",
            "Michael",
            "Jennifer",
            "William",
            "Linda",
            "David",
            "Elizabeth",
        ]
        last_names = [
            "Smith",
            "Johnson",
            "Williams",
            "Jones",
            "Brown",
            "Davis",
            "Miller",
            "Wilson",
            "Moore",
            "Taylor",
        ]
        return f"{random.choice(first_names)} {random.choice(last_names)}"

    def _generate_text(self) -> str:
        words = [
            "great",
            "excellent",
            "good",
            "best",
            "better",
            "awesome",
            "nice",
            "perfect",
            "wonderful",
            "amazing",
        ]
        return " ".join(random.sample(words, random.randint(3, 6)))

    def _fill_radio_group(self, container):
        radio_group = container.locator(RADIO_GROUP_SELECTOR)
        options = radio_group.locator(RADIO_OPTION_SELECTOR).all()
        if not options:
            return

        filtered_options = [
            opt
            for opt in options
            if opt.get_attribute("data-value") != OTHER_OPTION_VALUE
        ]
        chosen_option = random.choice(filtered_options or options)
        chosen_option.scroll_into_view_if_needed()
        chosen_option.click()

    def _fill_checkbox_group(self, container):
        heading_locator = container.locator(HEADING_SELECTOR)
        question_text = (
            heading_locator.inner_text().lower() if heading_locator.count() > 0 else ""
        )

        selection_limit = None
        if "select top" in question_text:
            try:
                limit_str = question_text.split("select top")[1].strip().split()[0]
                selection_limit = int(limit_str)
            except (ValueError, IndexError, AttributeError):
                logging.warning(
                    f"Could not parse selection limit from: {question_text}"
                )

        checkboxes = container.locator(CHECKBOX_SELECTOR).all()
        if not checkboxes:
            return

        filtered_checkboxes = [
            cb
            for cb in checkboxes
            if cb.get_attribute("data-value") != OTHER_OPTION_VALUE
        ]
        eligible_checkboxes = filtered_checkboxes or checkboxes

        if selection_limit:
            num_to_select = min(selection_limit, len(eligible_checkboxes))
        else:
            num_to_select = random.randint(
                1, min(3, len(eligible_checkboxes))
            )  # Default to selecting 1-3

        selected_checkboxes = random.sample(eligible_checkboxes, num_to_select)
        for checkbox in selected_checkboxes:
            checkbox.scroll_into_view_if_needed()
            checkbox.click()
            time.sleep(0.1)

    def _fill_text_input(self, container):
        input_element = container.locator(INPUT_SELECTOR).first
        if input_element.count() == 0:
            return

        heading_locator = container.locator(HEADING_SELECTOR)
        question_text = (
            heading_locator.inner_text().lower() if heading_locator.count() > 0 else ""
        )

        fill_value = ""
        if "email" in question_text:
            fill_value = self._generate_email()
        elif "name" in question_text:
            fill_value = self._generate_name()
        else:
            fill_value = self._generate_text()

        input_element.fill(fill_value)

    def _process_question_container(self, container):
        if container.locator(RADIO_GROUP_SELECTOR).count() > 0:
            self._fill_radio_group(container)
        elif container.locator(CHECKBOX_SELECTOR).count() > 0:
            self._fill_checkbox_group(container)
        elif container.locator(INPUT_SELECTOR).count() > 0:
            self._fill_text_input(container)
        else:
            logging.warning("Unknown question type in container.")

    def fill_form(self) -> bool:
        try:
            self.page.goto(self.form_url)
            question_containers = self.page.locator(QUESTION_CONTAINER_SELECTOR).all()

            for container in question_containers:
                self._process_question_container(container)
                time.sleep(0.1)

            submit_button = self.page.locator(SUBMIT_BUTTON_SELECTOR)
            if submit_button.count() == 0:
                logging.error("Submit button not found.")
                return False
            submit_button.click()

            self.page.wait_for_url("**/formResponse*")
            logging.info(f"Successfully submitted form: {self.form_url}")
            return True

        except Exception as e:
            logging.error(f"Error filling form {self.form_url}: {e}")
            return False

    def run_submission(self) -> bool:
        success = self.fill_form()
        self.cleanup()
        return success

    def cleanup(self):
        try:
            if self.context:
                self.context.close()
            if self.browser:
                self.browser.close()
            if self.playwright:
                self.playwright.stop()
        except Exception as e:
            logging.error(f"Error during cleanup: {e}")


def submission_worker(form_url: str) -> bool:
    form_filler = None
    try:
        form_filler = FormFiller(form_url)
        return form_filler.run_submission()
    except Exception as e:
        logging.error(f"Worker thread error for {form_url}: {e}")
        return False
    finally:
        if form_filler:
            form_filler.cleanup()


def run_threaded_submissions(
    form_url: str, submission_count: int, max_workers: int = None
):
    successful_submissions = 0
    failed_submissions = 0
    start_time = time.time()

    cpu_count = multiprocessing.cpu_count()
    default_workers = max(cpu_count // 2, 1)
    workers = min(max_workers or default_workers, submission_count)

    logging.info(
        f"Starting {submission_count} submissions for {form_url} with {workers} workers "
        f"(System CPUs: {cpu_count})"
    )

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [
            executor.submit(submission_worker, form_url)
            for _ in range(submission_count)
        ]

        for i, future in enumerate(as_completed(futures), 1):
            try:
                if future.result():
                    successful_submissions += 1
                else:
                    failed_submissions += 1
            except Exception as e:
                failed_submissions += 1
                logging.error(f"Future result error: {e}")

            if i % 10 == 0 or i == submission_count:
                elapsed = time.time() - start_time
                rate = i / elapsed if elapsed > 0 else 0
                logging.info(
                    f"Progress: {i}/{submission_count} ({successful_submissions} success, {failed_submissions} fail). "
                    f"Rate: {rate:.2f}/sec"
                )

    duration = time.time() - start_time
    final_rate = successful_submissions / duration if duration > 0 else 0
    logging.info(
        f"""
    ----------------------------------------
    Submission Summary for: {form_url}
    ----------------------------------------
    Total Attempted:  {submission_count}
    Successful:       {successful_submissions}
    Failed:           {failed_submissions}
    Total Time:       {duration:.2f} seconds
    Average Rate:     {final_rate:.2f} submissions/second
    ----------------------------------------
    """
    )
    return successful_submissions, failed_submissions


def get_user_input():
    form_url = input("Enter the Google Form URL: ").strip()
    while not form_url:
        print("Form URL cannot be empty.")
        form_url = input("Enter the Google Form URL: ").strip()

    submission_count = 0
    while submission_count <= 0:
        try:
            count_str = input("Enter the number of submissions to make: ").strip()
            submission_count = int(count_str)
            if submission_count <= 0:
                print("Please enter a positive number for submissions.")
        except ValueError:
            print("Invalid number entered. Please enter an integer.")

    return form_url, submission_count


def main():
    form_url, submission_count = get_user_input()

    try:
        run_threaded_submissions(form_url, submission_count)
    except KeyboardInterrupt:
        logging.info("Operation interrupted by user.")
        sys.exit(1)
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
