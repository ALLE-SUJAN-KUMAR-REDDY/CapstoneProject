import time
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from pages.base_page import BasePage
from utils.logger import get_logger

logger = get_logger(__name__)

BASE_URL = "https://phptravels.net/flights"

_DATE_INPUT_XPATH = (
    "//input[contains(@id,'Date') or contains(@name,'Date') "
    "or contains(@placeholder,'Date') or contains(@class,'date') "
    "or contains(@id,'date') or contains(@name,'date') "
    "or @type='date' or contains(@class,'datepicker')]"
)

# Matches any visible autocomplete suggestion item (ng-select, role=option, li in dropdown)
_SUGGESTION_XPATH = (
    "//*[contains(@class,'ng-option')]"
    " | //*[@role='option']"
    " | //ng-dropdown-panel//span[contains(@class,'ng-option-label')]"
    " | //ul[contains(@class,'dropdown') or contains(@class,'suggestions')]//li"
)


class FlightSearchPage(BasePage):
    """Page Object for the flight search page."""

    DEPARTURE_FIELD      = (By.XPATH, "//input[contains(@placeholder,'From') or contains(@id,'Origin') or contains(@class,'origin')]")
    ARRIVAL_FIELD        = (By.XPATH, "//input[contains(@placeholder,'To') or contains(@id,'Destination') or contains(@class,'destination')]")
    DEPARTURE_DATE_FIELD = (By.XPATH, "//input[contains(@id,'DepartDate') or contains(@name,'DepartDate') or @placeholder='Departure Date']")
    RETURN_DATE_FIELD    = (By.XPATH, "//input[contains(@id,'ReturnDate') or contains(@name,'ReturnDate') or @placeholder='Return Date']")
    SEARCH_BUTTON        = (By.XPATH, "//button[contains(text(),'Search') or contains(@class,'search')]")
    ALL_SELECTS          = (By.TAG_NAME, "select")

    def __init__(self, driver: WebDriver):
        super().__init__(driver)

    def load(self) -> "FlightSearchPage":
        self.open(BASE_URL)
        self.wait_for_page_load()
        logger.info("Flight search page loaded")
        return self

    def wait_for_page_load(self) -> None:
        WebDriverWait(self.driver, 30).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        time.sleep(0.1)
        logger.info(f"Page title: {self.driver.title}")
        logger.info(f"Page URL:   {self.driver.current_url}")
        buttons = self.driver.find_elements(By.TAG_NAME, "button")
        logger.info(f"Buttons on page: {[b.text.strip() for b in buttons if b.text.strip()]}")
        selects = self.driver.find_elements(By.TAG_NAME, "select")
        logger.info(f"Native selects found: {len(selects)}")
        try:
            WebDriverWait(self.driver, 10).until(
                lambda d: len(d.find_elements(
                    By.XPATH,
                    "//button[contains(.,'Search') or contains(@class,'search')]"
                    " | //input[@type='submit']"
                )) > 0
            )
            logger.info("Search button confirmed present")
        except Exception:
            logger.warning("Search button not detected during page load — proceeding anyway")

    def is_page_loaded(self) -> bool:
        try:
            return self.driver.execute_script("return document.readyState") == "complete"
        except Exception:
            return False

    def _select_option_in_element(self, select_el, text: str) -> None:
        from selenium.webdriver.support.ui import Select
        sel = Select(select_el)
        options_text = [o.text.strip() for o in sel.options]
        for opt in options_text:
            if text.lower() in opt.lower():
                sel.select_by_visible_text(opt)
                return
        sel.select_by_visible_text(text)

    # ------------------------------------------------------------------ #
    #  Autocomplete — FAST: wait for dropdown, click matching item immediately
    # ------------------------------------------------------------------ #

    def _fill_autocomplete(self, field_xpath: str, value: str) -> None:
        """
        Fast autocomplete fill:
        1. Click field, clear, type first 3 chars
        2. Wait (up to 4s) for ng-option/role=option items to appear
        3. Click the item whose text contains the airport code
        4. Fall back to first visible item, then Enter
        """
        field = self.find_clickable(By.XPATH, field_xpath)
        self.driver.execute_script(
            "arguments[0].scrollIntoView({block:'center'});", field)
        field.click()
        field.clear()
        field.send_keys(value[:3])

        code = value[:3].upper()
        clicked = False

        # Wait for dropdown items to appear (max 4s)
        try:
            WebDriverWait(self.driver, 4).until(
                lambda d: len([
                    e for e in d.find_elements(By.XPATH, _SUGGESTION_XPATH)
                    if e.is_displayed()
                ]) > 0
            )
        except Exception:
            logger.warning(f"Dropdown did not appear for '{value}' within 4s")

        # Collect all visible suggestion items
        items = self.driver.find_elements(By.XPATH, _SUGGESTION_XPATH)
        visible = [i for i in items if i.is_displayed()]
        logger.info(f"Dropdown items visible for '{value}': {len(visible)}")

        # Priority: click item whose text contains the 3-letter airport code
        for item in visible:
            if code in item.text.upper():
                self.driver.execute_script("arguments[0].click();", item)
                logger.info(
                    f"Clicked matching suggestion '{code}': "
                    f"'{item.text.strip()[:60]}'")
                clicked = True
                break

        # Fallback: click first visible item
        if not clicked and visible:
            self.driver.execute_script("arguments[0].click();", visible[0])
            logger.info(
                f"Clicked first suggestion for '{value}': "
                f"'{visible[0].text.strip()[:60]}'")
            clicked = True

        # Last resort: press Enter
        if not clicked:
            field.send_keys(Keys.RETURN)
            logger.warning(f"No dropdown items found for '{value}' — sent Enter")

    # ------------------------------------------------------------------ #
    #  Date helpers — 3-strategy robust date setting
    # ------------------------------------------------------------------ #

    def _get_date_inputs(self) -> list:
        inputs = self.driver.find_elements(By.XPATH, _DATE_INPUT_XPATH)
        return [i for i in inputs if i.is_displayed()]

    def _set_date_field(self, el, date_str: str) -> None:
        self.driver.execute_script(
            "arguments[0].removeAttribute('readonly');"
            "arguments[0].removeAttribute('disabled');", el
        )
        # Strategy 1: send_keys
        try:
            el.clear()
            el.send_keys(date_str)
            time.sleep(0.1)
            if el.get_attribute("value"):
                logger.info(f"Date set via send_keys: '{date_str}'")
                self._dismiss_datepicker()
                return
        except Exception as e:
            logger.debug(f"send_keys failed: {e}")

        # Strategy 2: JS value + events
        try:
            self.driver.execute_script(
                "arguments[0].value = arguments[1];"
                "arguments[0].dispatchEvent(new Event('input',{bubbles:true}));"
                "arguments[0].dispatchEvent(new Event('change',{bubbles:true}));",
                el, date_str
            )
            time.sleep(0.1)
            logger.info(f"Date set via JS: '{date_str}'")
            self._dismiss_datepicker()
            return
        except Exception as e:
            logger.debug(f"JS date strategy failed: {e}")

        # Strategy 3: ActionChains triple-click
        try:
            ActionChains(self.driver).triple_click(el).send_keys(date_str).perform()
            time.sleep(0.1)
            logger.info(f"Date set via ActionChains: '{date_str}'")
            self._dismiss_datepicker()
        except Exception as e:
            logger.warning(f"All date strategies failed for '{date_str}': {e}")

    def _dismiss_datepicker(self) -> None:
        try:
            self.driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
        except Exception:
            pass
        try:
            self.driver.find_element(By.TAG_NAME, "body").click()
        except Exception:
            pass
        time.sleep(0.05)

    # ------------------------------------------------------------------ #
    #  Actions
    # ------------------------------------------------------------------ #

    def select_flight_type(self, flight_type: str) -> None:
        logger.info(f"Selecting flight type: {flight_type}")
        selects = self.driver.find_elements(By.TAG_NAME, "select")
        for sel_el in selects:
            try:
                from selenium.webdriver.support.ui import Select
                sel = Select(sel_el)
                options = [o.text.strip().lower() for o in sel.options]
                if any("way" in o or "trip" in o or "round" in o or "one" in o
                       for o in options):
                    self._select_option_in_element(sel_el, flight_type)
                    logger.info(f"Flight type set: {flight_type} (native select)")
                    time.sleep(0.1)
                    return
            except Exception:
                continue

        for xpath in [
            "//div[contains(@class,'flight-type') or contains(@class,'tripType')]",
            "//div[contains(text(),'One Way') or contains(text(),'Round Trip')]",
            "//span[contains(text(),'One Way') or contains(text(),'Round Trip')]",
        ]:
            els = self.driver.find_elements(By.XPATH, xpath)
            if els and els[0].is_displayed():
                els[0].click()
                time.sleep(0.1)
                for opt_xpath in [
                    f"//*[contains(text(),'{flight_type}') and "
                    f"(contains(@class,'option') or contains(@class,'item') "
                    f"or ancestor::ul)]",
                    f"//*[contains(text(),'{flight_type}')]",
                ]:
                    opts = self.driver.find_elements(By.XPATH, opt_xpath)
                    for opt in opts:
                        if opt.is_displayed() and \
                                flight_type.lower() in opt.text.strip().lower():
                            opt.click()
                            logger.info(
                                f"Flight type set: {flight_type} (custom dropdown)")
                            time.sleep(0.1)
                            return
        logger.warning(f"Could not set flight type: {flight_type}")

    def set_departure_city(self, city_code: str) -> None:
        logger.info(f"Setting departure city: {city_code}")
        for xpath in [
            "(//input[@type='text'])[1]",
            "//input[contains(@placeholder,'From') or contains(@id,'origin') "
            "or contains(@name,'origin')]",
            "//input[contains(@class,'origin')]",
        ]:
            els = self.driver.find_elements(By.XPATH, xpath)
            if els and els[0].is_displayed():
                self._fill_autocomplete(xpath, city_code)
                return

    def set_arrival_city(self, city_code: str) -> None:
        logger.info(f"Setting arrival city: {city_code}")
        for xpath in [
            "(//input[@type='text'])[2]",
            "//input[contains(@placeholder,'To') or contains(@id,'destination') "
            "or contains(@name,'destination')]",
            "//input[contains(@class,'destination')]",
        ]:
            els = self.driver.find_elements(By.XPATH, xpath)
            if els and els[0].is_displayed():
                self._fill_autocomplete(xpath, city_code)
                return

    def set_departure_date(self, date_str: str) -> None:
        logger.info(f"Setting departure date: {date_str}")
        date_inputs = self._get_date_inputs()
        if date_inputs:
            self._set_date_field(date_inputs[0], date_str)
        else:
            logger.warning("Departure date field not found")

    def set_return_date(self, date_str: str) -> None:
        logger.info(f"Setting return date: {date_str}")
        time.sleep(0.1)
        date_inputs = self._get_date_inputs()
        if len(date_inputs) >= 2:
            self._set_date_field(date_inputs[1], date_str)
        elif len(date_inputs) == 1:
            logger.warning("Only one date field — setting return on same field")
            self._set_date_field(date_inputs[0], date_str)
        else:
            logger.warning("Return date field not found")

    def set_passengers(self, count: str) -> None:
        logger.info(f"Setting passenger count: {count}")
        selects = self.driver.find_elements(By.TAG_NAME, "select")
        for sel_el in selects:
            try:
                from selenium.webdriver.support.ui import Select
                sel = Select(sel_el)
                options_text = [o.text.strip() for o in sel.options]
                if any(any(c.isdigit() for c in o) for o in options_text):
                    for opt in options_text:
                        if count in opt:
                            sel.select_by_visible_text(opt)
                            logger.info(f"Passenger set: {opt}")
                            return
            except Exception:
                continue

        for xpath in [
            "//div[contains(@class,'passenger') or contains(@class,'Passenger')]",
            "//div[contains(text(),'Passenger') or contains(text(),'passenger')]",
        ]:
            els = self.driver.find_elements(By.XPATH, xpath)
            if els and els[0].is_displayed():
                els[0].click()
                time.sleep(0.1)
                opts = self.driver.find_elements(
                    By.XPATH,
                    f"//*[contains(text(),'{count}') and "
                    f"(contains(@class,'option') or contains(@class,'item') "
                    f"or ancestor::ul)]"
                )
                for opt in opts:
                    if opt.is_displayed():
                        opt.click()
                        logger.info(f"Passenger set: {count} (custom dropdown)")
                        return
        logger.warning(f"Could not set passenger count: {count}")

    def _ensure_on_flights_page(self) -> None:
        current = self.driver.current_url
        if "flights" not in current.lower():
            logger.warning(f"Drifted to {current} — navigating back")
            self.driver.get(BASE_URL)
            self.wait_for_page_load()

    def click_search(self) -> None:
        logger.info("Clicking Search Flights button")
        try:
            self.driver.execute_script("document.activeElement.blur();")
        except Exception:
            pass
        try:
            self.driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
        except Exception:
            pass
        time.sleep(0.1)

        self._ensure_on_flights_page()

        search_xpaths = [
            "//button[normalize-space(.)='Search Flights']",
            "//button[normalize-space(.)='Search']",
            "//button[contains(translate(.,'abcdefghijklmnopqrstuvwxyz',"
            "'ABCDEFGHIJKLMNOPQRSTUVWXYZ'),'SEARCH')]",
            "//button[contains(@class,'search') and not(ancestor::nav)]",
            "//form//button[@type='submit']",
            "//button[@type='submit']",
        ]

        original_url = self.driver.current_url
        clicked = False
        for xpath in search_xpaths:
            btns = self.driver.find_elements(By.XPATH, xpath)
            visible = [b for b in btns if b.is_displayed() and b.is_enabled()]
            if visible:
                btn = visible[0]
                self.driver.execute_script(
                    "arguments[0].scrollIntoView({block:'center'});", btn)
                time.sleep(0.1)
                self.driver.execute_script("arguments[0].click();", btn)
                logger.info(f"Search clicked via: {xpath}")
                clicked = True
                break

        if not clicked:
            logger.error("Search button not found")
            self.take_screenshot("DIAG_search_button_not_found")
            return

        try:
            WebDriverWait(self.driver, 15).until(
                lambda d: d.current_url != original_url)
            logger.info(f"Navigated to: {self.driver.current_url}")
        except Exception:
            logger.warning("URL did not change after Search click")
            self.take_screenshot("DIAG_url_no_change_after_search")

    def search_one_way(self, data: dict) -> None:
        logger.info("Starting one-way flight search")
        self.select_flight_type(data["flight_type"])
        time.sleep(0.1)
        self.set_departure_city(data["departure_city"])
        self.set_arrival_city(data["arrival_city"])
        self.set_departure_date(data["departure_date"])
        self.set_passengers(data["passengers"])
        self.take_screenshot("search_oneway_filled")
        self.click_search()

    def search_round_trip(self, data: dict) -> None:
        logger.info("Starting round-trip flight search")
        self.select_flight_type(data["flight_type"])
        time.sleep(0.1)
        self.set_departure_city(data["departure_city"])
        self.set_arrival_city(data["arrival_city"])
        self.set_departure_date(data["departure_date"])
        self.set_return_date(data["return_date"])
        self.set_passengers(data["passengers"])
        self.take_screenshot("search_roundtrip_filled")
        self.click_search()