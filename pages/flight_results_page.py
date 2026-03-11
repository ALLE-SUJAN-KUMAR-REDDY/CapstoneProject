import time
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from pages.base_page import BasePage
from utils.logger import get_logger

logger = get_logger(__name__)

_PRICE_XPATH = (
    "//*[contains(text(),'USD')]"
    " | //*[contains(@class,'price')]"
    " | //*[contains(@class,'Price')]"
    " | //*[contains(@class,'fare')]"
)

_NO_RESULTS_XPATH = (
    "//*[contains(text(),'No flights') or contains(text(),'no results') "
    "or contains(text(),'No Results') or contains(text(),'not found')]"
)

_RESULT_CARD_XPATH = (
    "//*[contains(@class,'flight-item')]"
    " | //*[contains(@class,'flight-card')]"
    " | //*[contains(@class,'flight-result')]"
    " | //*[contains(@class,'result-item')]"
    " | //*[contains(@class,'FlightResult')]"
    " | //*[contains(@class,'flightrow')]"
    " | //*[contains(@class,'flight-row')]"
)

_EXCLUDED_HREF_PATTERNS = [
    "/page/", "how-to-book", "affiliate", "about",
    "contact", "blog", "terms", "privacy",
]

def _is_excluded_link(el) -> bool:
    href = (el.get_attribute("href") or "").lower()
    return any(pat in href for pat in _EXCLUDED_HREF_PATTERNS)


class FlightResultsPage(BasePage):

    def __init__(self, driver: WebDriver):
        super().__init__(driver)

    def wait_for_results(self, timeout: int = 60) -> None:
        logger.info("Waiting for flight results to load...")
        try:
            WebDriverWait(self.driver, 15).until(
                EC.invisibility_of_element_located(
                    (By.XPATH, "//*[contains(@class,'loading') or contains(@class,'spinner') or contains(@class,'preloader')]")
                )
            )
        except Exception:
            pass
        time.sleep(3)
        try:
            WebDriverWait(self.driver, timeout).until(
                lambda d: (
                    len(d.find_elements(By.XPATH, _PRICE_XPATH)) > 0
                    or len(d.find_elements(By.XPATH, _NO_RESULTS_XPATH)) > 0
                    or len(d.find_elements(By.XPATH, "//*[contains(text(),'Flights') and contains(text(),'Supplier')]")) > 0
                    or len(d.find_elements(By.XPATH, "//*[contains(text(),'Flights') and contains(text(),'Found')]")) > 0
                )
            )
            logger.info("Flight results detected")
        except Exception:
            logger.warning("Timed out waiting for results")
            self.take_screenshot("DIAG_results_timeout")

    def are_results_displayed(self) -> bool:
        """Check if flight results are visible. Retries on stale element."""
        for _attempt in range(3):
            try:
                book_btns = [
                    el for el in self.driver.find_elements(
                        By.XPATH,
                        "//button[contains(translate(.,'abcdefghijklmnopqrstuvwxyz','ABCDEFGHIJKLMNOPQRSTUVWXYZ'),'BOOK NOW')]"
                    )
                    if el.is_displayed()
                ]
                if book_btns:
                    logger.info(f"are_results_displayed: {len(book_btns)} book button(s) found")
                    return True
                prices = [
                    p for p in self.driver.find_elements(By.XPATH, "//*[contains(text(),'USD')]")
                    if p.is_displayed() and p.text.strip() and p.text.strip() != "USD"
                ]
                if prices:
                    logger.info(f"are_results_displayed: {len(prices)} USD price(s) found")
                    return True
                found_text = self.driver.find_elements(
                    By.XPATH,
                    "//*[contains(text(),'Flights') and (contains(text(),'Found') or contains(text(),'Supplier'))]"
                )
                if any(f.is_displayed() for f in found_text):
                    return True
                break  # No stale error, genuinely no results
            except Exception as e:
                logger.warning(f"are_results_displayed attempt {_attempt+1} stale/error: {e}")
                time.sleep(1)
        self.take_screenshot("DIAG_are_results_false")
        return False

    def get_results_count_text(self) -> str:
        for _attempt in range(3):
            try:
                for el in self.driver.find_elements(
                    By.XPATH,
                    "//*[contains(text(),'Flights') or contains(text(),'flights') or contains(text(),'Results')]"
                ):
                    text = el.text.strip()
                    if text and any(ch.isdigit() for ch in text):
                        return text
                return "Results count not found"
            except Exception:
                time.sleep(1)
        return "Results count not found"

    def is_price_displayed(self) -> bool:
        for _attempt in range(3):
            try:
                return any(p.is_displayed() and p.text.strip()
                           for p in self.driver.find_elements(By.XPATH, _PRICE_XPATH))
            except Exception:
                time.sleep(1)
        return False

    def get_first_flight_price(self) -> str:
        for p in self.driver.find_elements(By.XPATH, _PRICE_XPATH):
            if p.text.strip():
                return p.text.strip()
        return "Price not found"

    def get_all_prices(self) -> list:
        return [p.text.strip() for p in self.driver.find_elements(
            By.XPATH, _PRICE_XPATH) if p.text.strip()]

    def click_first_book_now(self) -> None:
        logger.info("Clicking Book Now on first available flight")
        time.sleep(1)

        strat1 = [
            el for el in self.driver.find_elements(
                By.XPATH,
                "//button[contains(translate(.,'abcdefghijklmnopqrstuvwxyz','ABCDEFGHIJKLMNOPQRSTUVWXYZ'),'BOOK NOW')]"
            )
            if el.is_displayed()
            and el.is_enabled()
            and not (el.get_attribute("href") or "").strip()
            and "btn" in (el.get_attribute("class") or "")
        ]
        logger.info(f"Strategy 1 (button 'Book Now' with btn class, no href): {len(strat1)} found")

        if strat1:
            target = strat1[0]
            logger.info(f"Clicked Book Now: tag={target.tag_name}, text='{target.text.strip()[:50]}'")
            self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", target)
            time.sleep(0.3)
            try:
                target.click()
            except Exception:
                self.driver.execute_script("arguments[0].click();", target)
            time.sleep(2)
            current = self.driver.current_url
            if any(pat in current for pat in _EXCLUDED_HREF_PATTERNS):
                logger.error(f"Strategy 1 landed on wrong page: {current}")
                self.driver.back()
                time.sleep(2)
                raise RuntimeError(f"Book Now went to wrong page: {current}")
            logger.info(f"Book Now clicked OK, URL: {current}")
            return

        strat2 = [
            el for el in self.driver.find_elements(
                By.XPATH,
                "//button[contains(translate(.,'abcdefghijklmnopqrstuvwxyz','ABCDEFGHIJKLMNOPQRSTUVWXYZ'),'BOOK')]"
            )
            if el.is_displayed()
            and el.is_enabled()
            and "how to book" not in el.text.lower()
            and not _is_excluded_link(el)
        ]
        logger.info(f"Strategy 2 (button with 'Book', not nav): {len(strat2)} found")

        if strat2:
            target = strat2[0]
            logger.info(f"Clicked Book Now (strat2): tag={target.tag_name}, text='{target.text.strip()[:50]}'")
            self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", target)
            time.sleep(0.3)
            try:
                target.click()
            except Exception:
                self.driver.execute_script("arguments[0].click();", target)
            time.sleep(2)
            current = self.driver.current_url
            if any(pat in current for pat in _EXCLUDED_HREF_PATTERNS):
                logger.error(f"Strategy 2 landed on wrong page: {current}")
                self.driver.back()
                time.sleep(2)
                raise RuntimeError(f"Book Now went to wrong page: {current}")
            logger.info(f"Book Now clicked OK, URL: {current}")
            return

        self.take_screenshot("DIAG_no_book_button")
        all_els = self.driver.find_elements(By.XPATH, "//a | //button")
        logger.warning("All visible links/buttons on page:")
        for el in all_els:
            if el.is_displayed():
                logger.warning(
                    f"  {el.tag_name} | text='{el.text.strip()[:50]}' "
                    f"| href='{el.get_attribute('href') or ''}' "
                    f"| class='{el.get_attribute('class') or ''}'"
                )
        raise RuntimeError("No valid 'Book Now' button found in flight results")