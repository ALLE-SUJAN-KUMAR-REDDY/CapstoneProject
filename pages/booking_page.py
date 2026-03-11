import time
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from pages.base_page import BasePage
from utils.logger import get_logger

logger = get_logger(__name__)


class BookingPage(BasePage):

    def __init__(self, driver: WebDriver):
        super().__init__(driver)

    # ------------------------------------------------------------------ #
    #  Page load
    # ------------------------------------------------------------------ #

    def wait_for_page_load(self) -> None:
        logger.info("Waiting for booking page to load...")
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        WebDriverWait(self.driver, 20).until(
            EC.presence_of_element_located((By.TAG_NAME, "form"))
        )
        time.sleep(1)
        logger.info(f"Booking page URL: {self.driver.current_url}")
        logger.info(f"Booking page title: {self.driver.title}")
        inputs = self.driver.find_elements(By.XPATH, "//input | //select")
        if inputs:
            logger.info("Booking form inputs detected")
        logger.info(f"Total form elements: {len(inputs)}")
        for el in inputs:
            logger.info(
                f"  {el.tag_name} type={el.get_attribute('type') or 'select-one'}"
                f" name={el.get_attribute('name') or ''}"
                f" id={el.get_attribute('id') or ''}"
                f" placeholder={el.get_attribute('placeholder') or ''}"
                f" visible={el.is_displayed()}"
            )

    def log_form_elements(self) -> None:
        all_els = self.driver.find_elements(By.XPATH, "//input | //select")
        logger.info(f"Total form elements: {len(all_els)}")
        for el in all_els:
            logger.info(
                f"  {el.tag_name} type={el.get_attribute('type') or 'select-one'}"
                f" name={el.get_attribute('name') or ''}"
                f" id={el.get_attribute('id') or ''}"
                f" placeholder={el.get_attribute('placeholder') or ''}"
                f" visible={el.is_displayed()}"
            )
        self.take_screenshot("booking_form_elements")

    # ------------------------------------------------------------------ #
    #  Low-level helpers
    # ------------------------------------------------------------------ #

    def _fill_input(self, el, value: str) -> None:
        self.driver.execute_script(
            "arguments[0].scrollIntoView({block:'center'});", el)
        time.sleep(0.1)
        try:
            el.clear()
            el.send_keys(value)
            actual = el.get_attribute("value") or ""
            if actual:
                logger.info(f"Filled input: '{actual}'")
                return
        except Exception:
            pass
        try:
            self.driver.execute_script("arguments[0].value = '';", el)
            ActionChains(self.driver).move_to_element(el).click(el)\
                .send_keys(value).perform()
            logger.info(f"Filled input via ActionChains: '{value}'")
        except Exception as e:
            logger.warning(f"_fill_input failed: {e}")

    def _select_by_text(self, sel_el, text: str) -> bool:
        sel  = Select(sel_el)
        opts = [o.text.strip() for o in sel.options]
        if text in opts:
            sel.select_by_visible_text(text)
            logger.info(f"Selected (exact): '{text}'")
            return True
        for opt in opts:
            if text.lower() in opt.lower():
                sel.select_by_visible_text(opt)
                logger.info(f"Selected (partial): '{opt}'")
                return True
        logger.warning(f"Option '{text}' not found in {opts[:6]}")
        return False

    # ------------------------------------------------------------------ #
    #  Guest Booking
    # ------------------------------------------------------------------ #

    def _select_guest_radio(self) -> None:
        logger.info("Selecting Guest Booking option")
        self.take_screenshot("booking_guest_before_fill")
        radios = self.driver.find_elements(By.XPATH, "//input[@type='radio']")
        for r in radios:
            if r.get_attribute("id") == "booking_guest":
                if not r.is_selected():
                    self.driver.execute_script("arguments[0].click();", r)
                logger.info("Guest radio selected")
                return
        if radios and not radios[0].is_selected():
            self.driver.execute_script("arguments[0].click();", radios[0])

    def _fill_title(self, title: str) -> None:
        logger.info(f"Filling title: {title}")
        for sel_el in self.driver.find_elements(By.TAG_NAME, "select"):
            opts = [o.text.strip() for o in Select(sel_el).options]
            if any(t in opts for t in ["Mr", "Mrs", "Ms", "Miss", "Dr"]):
                if self._select_by_text(sel_el, title):
                    logger.info(f"Title set to: {title}")
                    return

    def _fill_text_input_by_placeholder(self, placeholder: str,
                                         value: str) -> bool:
        for el in self.driver.find_elements(
            By.XPATH, f"//input[@placeholder='{placeholder}']"
        ):
            if el.is_displayed():
                self._fill_input(el, value)
                return True
        return False

    def _fill_first_name(self, name: str) -> None:
        logger.info(f"Filling first name: {name}")
        if self._fill_text_input_by_placeholder("Enter First Name", name):
            return
        for el in self.driver.find_elements(By.XPATH, "//input[@type='text']"):
            if el.is_displayed():
                ph = (el.get_attribute("placeholder") or "").lower()
                nm = (el.get_attribute("name") or "").lower()
                if "first" in ph or "first" in nm:
                    self._fill_input(el, name)
                    return
        for el in self.driver.find_elements(By.XPATH, "//input[@type='text']"):
            if el.is_displayed():
                self._fill_input(el, name)
                return

    def _fill_last_name(self, name: str) -> None:
        logger.info(f"Filling last name: {name}")
        if self._fill_text_input_by_placeholder("Enter Last Name", name):
            return
        for el in self.driver.find_elements(By.XPATH, "//input[@type='text']"):
            if el.is_displayed():
                ph = (el.get_attribute("placeholder") or "").lower()
                nm = (el.get_attribute("name") or "").lower()
                if "last" in ph or "last" in nm:
                    self._fill_input(el, name)
                    return
        inputs = [e for e in self.driver.find_elements(
            By.XPATH, "//input[@type='text']") if e.is_displayed()]
        if len(inputs) >= 2:
            self._fill_input(inputs[1], name)

    def _fill_email(self, email: str) -> None:
        logger.info(f"Filling email: {email}")
        for el in self.driver.find_elements(
            By.XPATH,
            "//input[@type='email' or @placeholder='Enter Email']"
        ):
            if el.is_displayed():
                self._fill_input(el, email)
                return

    def _fill_country_code(self, code_str: str) -> None:
        logger.info(f"Filling country code: '{code_str}'")
        all_selects = self.driver.find_elements(By.TAG_NAME, "select")
        logger.info(f"Total <select> elements on page: {len(all_selects)}")
        parts  = code_str.split()
        prefix = parts[0] if parts else ""
        dial   = parts[1] if len(parts) > 1 else ""

        for sel_el in all_selects:
            sel  = Select(sel_el)
            opts = [o.text.strip() for o in sel.options]
            if len(opts) < 50:
                continue
            dial_opts = [o for o in opts if "+" in o]
            if len(dial_opts) < 50:
                continue
            logger.info(
                f"Country-code select found: {len(opts)} options,"
                f" current='{Select(sel_el).first_selected_option.text.strip()}'"
            )
            for opt in opts:
                if opt == code_str:
                    sel.select_by_visible_text(opt)
                    logger.info(f"Country code selected: '{opt}'")
                    return
            for opt in opts:
                if opt.startswith(prefix + " "):
                    sel.select_by_visible_text(opt)
                    logger.info(f"Country code selected: '{opt}'")
                    return
            for opt in opts:
                if dial and dial in opt:
                    sel.select_by_visible_text(opt)
                    logger.info(f"Country code selected: '{opt}'")
                    return

    def _fill_phone(self, phone: str) -> None:
        logger.info(f"Filling phone: {phone}")
        for el in self.driver.find_elements(
            By.XPATH,
            "//input[@type='tel' or @placeholder='Enter Phone Number']"
        ):
            if el.is_displayed():
                self._fill_input(el, phone)
                return

    # ------------------------------------------------------------------ #
    #  Passenger details
    # ------------------------------------------------------------------ #

    def _fill_nationality(self, nationality: str) -> None:
        logger.info(f"Filling nationality: {nationality}")
        for sel_el in self.driver.find_elements(By.TAG_NAME, "select"):
            opts = [o.text.strip() for o in Select(sel_el).options]
            if any("India" in o or "United" in o or "Pakistan" in o
                   for o in opts):
                if self._select_by_text(sel_el, nationality):
                    return

    def fill_dob(self, day: str, month: str, year: str) -> None:
        logger.info(f"Filling DOB: day='{day}' month='{month}' year='{year}'")
        day_num = day.lstrip("0") or day
        if " " in month:
            month_num  = month.split()[0].lstrip("0") or month.split()[0]
            month_name = month.split()[1] if len(month.split()) > 1 else month
        else:
            month_num  = month
            month_name = month
        logger.info(
            f"DOB normalised: day='{day_num}' month_num='{month_num}'"
            f" month_name='{month_name}' year='{year}'"
        )

        day_sel = month_sel = year_sel = None
        for sel_el in self.driver.find_elements(By.TAG_NAME, "select"):
            opts     = [o.text.strip() for o in Select(sel_el).options]
            num_opts = [o for o in opts if o.isdigit()]
            if len(num_opts) >= 28 and all(
                int(o) <= 31 for o in num_opts if o.isdigit()
            ):
                day_sel = sel_el
            elif len(opts) == 13 and any(
                any(m in o for m in ["Jan","Feb","Mar","Apr","May","Jun",
                                     "Jul","Aug","Sep","Oct","Nov","Dec"])
                for o in opts
            ):
                month_sel = sel_el
            elif len(opts) > 50 and any(
                o.isdigit() and 1900 < int(o) < 2100
                for o in opts if o.isdigit()
            ):
                year_sel = sel_el

        day_ok = month_ok = year_ok = False
        if day_sel:
            opts = [o.text.strip() for o in Select(day_sel).options]
            for opt in opts:
                if day.lstrip("0") in opt or day in opt:
                    Select(day_sel).select_by_visible_text(opt)
                    logger.info(f"DOB day selected: '{opt}'")
                    day_ok = True
                    break

        if month_sel:
            opts = [o.text.strip() for o in Select(month_sel).options]
            for opt in opts:
                if month_name.lower() in opt.lower() or month_num in opt.split()[0]:
                    Select(month_sel).select_by_visible_text(opt)
                    logger.info(f"DOB month selected: '{opt}'")
                    month_ok = True
                    break

        if year_sel:
            opts = [o.text.strip() for o in Select(year_sel).options]
            for opt in opts:
                if year in opt:
                    Select(year_sel).select_by_visible_text(opt)
                    logger.info(f"DOB year selected: '{opt}'")
                    year_ok = True
                    break

        logger.info(
            f"DOB fill result: day={day_ok} month={month_ok} year={year_ok}"
        )

    def _fill_passport(self, passport: str) -> None:
        logger.info(f"Filling passport: '{passport}'")
        self.driver.execute_script("window.scrollBy(0, 600);")
        time.sleep(0.3)

        target = None
        for label in self.driver.find_elements(By.TAG_NAME, "label"):
            lt = label.text.strip().lower()
            if "passport" in lt or "id" in lt:
                logger.info("Passport found via label XPath")
                try:
                    nxt = label.find_element(
                        By.XPATH, "following::input[@type='text'][1]")
                    target = nxt
                    break
                except Exception:
                    pass

        if not target:
            els = self.driver.find_elements(
                By.XPATH, "//input[@placeholder='6 - 15 Numbers']")
            if els:
                target = els[0]

        if not target:
            inputs = [
                e for e in self.driver.find_elements(
                    By.XPATH, "//input[@type='text']")
                if e.is_displayed()
            ]
            if inputs:
                target = inputs[-1]

        if not target:
            logger.warning("Passport field not found")
            return

        logger.info(
            f"Passport target: placeholder='{target.get_attribute('placeholder')}'"
            f" name='{target.get_attribute('name') or ''}'"
        )

        for attempt in range(1, 4):
            try:
                self.driver.execute_script(
                    "arguments[0].scrollIntoView({block:'center'});", target)
                time.sleep(0.2)
                actions = ActionChains(self.driver)
                actions.move_to_element(target).click(target)
                actions.key_down(Keys.CONTROL).send_keys("a").key_up(Keys.CONTROL)
                actions.send_keys(Keys.DELETE)
                actions.send_keys(passport)
                actions.perform()
                time.sleep(0.3)
                actual = target.get_attribute("value") or ""
                logger.info(f"Passport after ActionChains attempt {attempt}: '{actual}'")
                if actual == passport:
                    logger.info(f"Passport confirmed on attempt {attempt}")
                    return
            except Exception as e:
                logger.warning(f"Passport attempt {attempt} failed: {e}")
                time.sleep(0.5)

        try:
            self.driver.execute_script("""
                var nativeInputValueSetter =
                    Object.getOwnPropertyDescriptor(
                        window.HTMLInputElement.prototype, 'value').set;
                nativeInputValueSetter.call(arguments[0], arguments[1]);
                arguments[0].dispatchEvent(new Event('input', {bubbles:true}));
                arguments[0].dispatchEvent(new Event('change', {bubbles:true}));
            """, target, passport)
            time.sleep(0.3)
            actual = target.get_attribute("value") or ""
            logger.info(f"Passport via JS setter: '{actual}'")
        except Exception as e:
            logger.warning(f"Passport JS fallback failed: {e}")

    # ------------------------------------------------------------------ #
    #  Public composite methods
    # ------------------------------------------------------------------ #

    def fill_guest_details(self, data: dict) -> None:
        logger.info("=== Filling guest details ===")
        self._select_guest_radio()
        self._fill_title(data.get("title", "Mr"))
        self._fill_first_name(data.get("first_name", ""))
        self._fill_last_name(data.get("last_name", ""))
        self._fill_email(data.get("email", ""))
        self._fill_country_code(data.get("country_code", "IN +91"))
        self._fill_phone(data.get("phone", ""))
        self.take_screenshot("booking_guest_after_fill")
        logger.info("Guest details filled")

    def fill_passenger_details(self, data: dict) -> None:
        logger.info("=== Filling passenger details ===")
        self.take_screenshot("booking_passenger_before_fill")
        self._fill_nationality(data.get("nationality", "India"))
        self.fill_dob(
            data.get("dob_day", ""),
            data.get("dob_month", ""),
            data.get("dob_year", "")
        )
        self._fill_passport(data.get("passport_number", ""))
        self.take_screenshot("booking_passenger_after_fill")
        logger.info("Passenger details filled")

    # ------------------------------------------------------------------ #
    #  Payment / Confirm
    # ------------------------------------------------------------------ #

    def select_credit_card_payment(self) -> None:
        logger.info("Selecting Credit Card payment method")
        for label in self.driver.find_elements(By.TAG_NAME, "label"):
            if "credit" in label.text.lower():
                self.driver.execute_script(
                    "arguments[0].scrollIntoView({block:'center'});", label)
                time.sleep(0.1)
                try:
                    label.click()
                except Exception:
                    self.driver.execute_script("arguments[0].click();", label)
                logger.info(f"Clicked credit label directly: '{label.text.strip()}'")
                return

        for radio in self.driver.find_elements(
            By.XPATH, "//input[@type='radio']"
        ):
            try:
                parent_text = radio.find_element(By.XPATH, "..").text.lower()
            except Exception:
                parent_text = ""
            if "credit" in parent_text or "stripe" in parent_text:
                if not radio.is_selected():
                    self.driver.execute_script("arguments[0].click();", radio)
                logger.info("Credit card radio selected")
                return

    def accept_terms_and_conditions(self) -> None:
        logger.info("Accepting Terms & Conditions")
        for cb in self.driver.find_elements(
            By.XPATH, "//input[@type='checkbox']"
        ):
            self.driver.execute_script(
                "arguments[0].scrollIntoView({block:'center'});", cb)
            time.sleep(0.1)
            try:
                if not cb.is_selected():
                    cb.click()
                logger.info("Checkbox checked")
            except Exception:
                self.driver.execute_script("arguments[0].click();", cb)
                logger.info("Checkbox checked via JS")

    def get_booking_total(self) -> str:
        try:
            for el in self.driver.find_elements(
                By.XPATH, "//*[contains(text(),'USD')]"
            ):
                t = el.text.strip()
                if t and len(t) > 4:
                    return t
        except Exception:
            pass
        return "Total not found"

    def click_confirm_booking(self) -> None:
        logger.info("Clicking Confirm Booking button")
        for xpath in [
            "//button[contains(.,'Confirm Booking')]",
            "//button[contains(.,'Confirm')]",
            "//button[@type='submit']",
        ]:
            btns = self.driver.find_elements(By.XPATH, xpath)
            vis  = [b for b in btns if b.is_displayed() and b.is_enabled()]
            if vis:
                target = vis[-1]
                logger.info(
                    f"Confirm button: tag={target.tag_name}"
                    f" text='{target.text.strip()[:40]}'"
                )
                self.driver.execute_script(
                    "arguments[0].scrollIntoView({block:'center'});", target)
                time.sleep(0.3)
                try:
                    target.click()
                except Exception:
                    self.driver.execute_script("arguments[0].click();", target)
                logger.info("Confirm Booking clicked")
                return
        raise RuntimeError("Confirm Booking button not found")