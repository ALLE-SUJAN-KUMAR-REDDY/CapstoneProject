import os
import time
from datetime import datetime
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from utils.logger import get_logger

logger = get_logger(__name__)

DEFAULT_TIMEOUT = 20
POLL_FREQUENCY = 0.5


class BasePage:
    """
    Base class for all Page Objects.
    Provides common Selenium helper methods with explicit waits and logging.
    """

    def __init__(self, driver: WebDriver):
        self.driver = driver
        self.wait = WebDriverWait(driver, DEFAULT_TIMEOUT, poll_frequency=POLL_FREQUENCY)

    # ------------------------------------------------------------------ #
    #  Navigation
    # ------------------------------------------------------------------ #

    def open(self, url: str) -> None:
        logger.info(f"Opening URL: {url}")
        self.driver.get(url)

    def get_title(self) -> str:
        return self.driver.title

    def get_current_url(self) -> str:
        return self.driver.current_url

    # ------------------------------------------------------------------ #
    #  Element finders with explicit waits
    # ------------------------------------------------------------------ #

    def find_element(self, by: str, value: str, timeout: int = DEFAULT_TIMEOUT) -> WebElement:
        logger.debug(f"Waiting for element: ({by}, '{value}')")
        return WebDriverWait(self.driver, timeout).until(
            EC.presence_of_element_located((by, value))
        )

    def find_clickable(self, by: str, value: str, timeout: int = DEFAULT_TIMEOUT) -> WebElement:
        logger.debug(f"Waiting for clickable: ({by}, '{value}')")
        return WebDriverWait(self.driver, timeout).until(
            EC.element_to_be_clickable((by, value))
        )

    def find_visible(self, by: str, value: str, timeout: int = DEFAULT_TIMEOUT) -> WebElement:
        logger.debug(f"Waiting for visible: ({by}, '{value}')")
        return WebDriverWait(self.driver, timeout).until(
            EC.visibility_of_element_located((by, value))
        )

    def find_elements(self, by: str, value: str, timeout: int = DEFAULT_TIMEOUT) -> list:
        WebDriverWait(self.driver, timeout).until(
            EC.presence_of_element_located((by, value))
        )
        return self.driver.find_elements(by, value)

    # ------------------------------------------------------------------ #
    #  Interactions
    # ------------------------------------------------------------------ #

    def click(self, by: str, value: str, timeout: int = DEFAULT_TIMEOUT) -> None:
        element = self.find_clickable(by, value, timeout)
        logger.info(f"Clicking element: ({by}, '{value}')")
        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", element)
        time.sleep(0.3)
        element.click()

    def js_click(self, by: str, value: str, timeout: int = DEFAULT_TIMEOUT) -> None:
        element = self.find_element(by, value, timeout)
        logger.info(f"JS clicking element: ({by}, '{value}')")
        self.driver.execute_script("arguments[0].click();", element)

    def type_text(self, by: str, value: str, text: str, clear: bool = True, timeout: int = DEFAULT_TIMEOUT) -> None:
        element = self.find_visible(by, value, timeout)
        logger.info(f"Typing '{text}' into ({by}, '{value}')")
        if clear:
            element.clear()
        element.send_keys(text)

    def get_text(self, by: str, value: str, timeout: int = DEFAULT_TIMEOUT) -> str:
        element = self.find_visible(by, value, timeout)
        return element.text.strip()

    def is_element_present(self, by: str, value: str, timeout: int = 5) -> bool:
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
            return True
        except TimeoutException:
            return False

    def is_element_visible(self, by: str, value: str, timeout: int = 5) -> bool:
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located((by, value))
            )
            return True
        except TimeoutException:
            return False

    def wait_for_url_contains(self, fragment: str, timeout: int = DEFAULT_TIMEOUT) -> None:
        logger.debug(f"Waiting for URL to contain: '{fragment}'")
        WebDriverWait(self.driver, timeout).until(EC.url_contains(fragment))

    def scroll_to_element(self, by: str, value: str) -> None:
        element = self.find_element(by, value)
        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", element)
        time.sleep(0.3)

    def select_dropdown_by_visible_text(self, by: str, value: str, text: str) -> None:
        from selenium.webdriver.support.ui import Select
        element = self.find_element(by, value)
        Select(element).select_by_visible_text(text)

    # ------------------------------------------------------------------ #
    #  Screenshots
    # ------------------------------------------------------------------ #

    def take_screenshot(self, name: str = "screenshot") -> str:
        os.makedirs("screenshots", exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = os.path.join("screenshots", f"{name}_{timestamp}.png")
        self.driver.save_screenshot(filepath)
        logger.info(f"Screenshot saved: {filepath}")
        return filepath

    # ------------------------------------------------------------------ #
    #  Waits
    # ------------------------------------------------------------------ #

    def sleep(self, seconds: float) -> None:
        time.sleep(seconds)
