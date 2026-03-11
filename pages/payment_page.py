import time
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait
from pages.base_page import BasePage
from utils.logger import get_logger

logger = get_logger(__name__)


class PaymentPage(BasePage):

    def __init__(self, driver: WebDriver):
        super().__init__(driver)

    # ------------------------------------------------------------------ #
    #  Invoice page — wait
    # ------------------------------------------------------------------ #

    def wait_for_invoice_page(self, timeout: int = 40) -> None:
        logger.info("Waiting for invoice page to load...")
        time.sleep(0.3)
        WebDriverWait(self.driver, timeout).until(
            lambda d: "invoice" in d.current_url.lower()
            or len(d.find_elements(
                By.XPATH,
                "//a[contains(.,'Make Payment')]"
                " | //button[contains(.,'Make Payment')]"
            )) > 0
            or len(d.find_elements(
                By.XPATH,
                "//*[contains(text(),'Invoice ID')"
                " or contains(text(),'Invoice #')]"
            )) > 0
        )
        logger.info(f"Invoice page detected: {self.driver.current_url}")

    # ------------------------------------------------------------------ #
    #  Make Payment
    # ------------------------------------------------------------------ #

    def click_make_payment(self) -> None:
        logger.info("Clicking Make Payment button")
        btns = self.driver.find_elements(
            By.XPATH,
            "//button[contains(.,'Make Payment')]"
            " | //a[contains(.,'Make Payment')]"
        )
        visible = [b for b in btns if b.is_displayed() and b.is_enabled()]
        if visible:
            self.driver.execute_script(
                "arguments[0].scrollIntoView({block:'center'});", visible[0])
            time.sleep(0.1)
            try:
                visible[0].click()
            except Exception:
                self.driver.execute_script("arguments[0].click();", visible[0])
            logger.info(f"Make Payment clicked: '{visible[0].text.strip()[:40]}'")
            return
        self.take_screenshot("DIAG_no_make_payment_btn")
        raise RuntimeError("Make Payment button not found on invoice page")

    # ------------------------------------------------------------------ #
    #  Invoice number
    # ------------------------------------------------------------------ #

    def get_invoice_number(self) -> str:
        try:
            for el in self.driver.find_elements(
                By.XPATH,
                "//*[contains(text(),'#') and "
                "(contains(text(),'Invoice') or contains(text(),'Booking'))]"
            ):
                if "#" in el.text:
                    return el.text.strip()
        except Exception:
            pass
        return "Invoice # not found"

    # ------------------------------------------------------------------ #
    #  Proceed to Payment
    # ------------------------------------------------------------------ #

    def click_proceed_to_payment(self) -> None:
        logger.info("Clicking Proceed to Payment (if present)")
        btns = self.driver.find_elements(
            By.XPATH,
            "//button[contains(.,'Proceed to Payment') or contains(.,'Proceed')]"
            " | //a[contains(.,'Proceed to Payment') or contains(.,'Proceed')]"
        )
        visible = [b for b in btns if b.is_displayed() and b.is_enabled()]
        if not visible:
            logger.info("No Proceed button found — may have auto-redirected")
            return
        self.driver.execute_script(
            "arguments[0].scrollIntoView({block:'center'});", visible[0])
        time.sleep(0.1)
        try:
            visible[0].click()
        except Exception:
            self.driver.execute_script("arguments[0].click();", visible[0])
        logger.info("Proceed to Payment clicked")

    # ------------------------------------------------------------------ #
    #  Stripe — wait
    # ------------------------------------------------------------------ #

    def wait_for_stripe_page(self, timeout: int = 30) -> None:
        logger.info("Waiting for Stripe checkout page...")
        WebDriverWait(self.driver, timeout).until(
            lambda d: "stripe.com" in d.current_url
            or "checkout" in d.current_url.lower()
        )
        time.sleep(1)
        logger.info(f"Stripe page URL: {self.driver.current_url}")

    # ------------------------------------------------------------------ #
    #  Stripe — fill helpers
    # ------------------------------------------------------------------ #

    def _stripe_fill(self, el, value: str) -> None:
        self.driver.execute_script(
            "arguments[0].scrollIntoView({block:'center'});", el)
        time.sleep(0.05)
        try:
            self.driver.execute_script("arguments[0].click();", el)
            time.sleep(0.05)
            el.send_keys(Keys.CONTROL + "a")
            el.send_keys(Keys.DELETE)
            el.send_keys(value)
            time.sleep(0.2)
            actual = el.get_attribute("value") or ""
            if actual:
                logger.info(f"_stripe_fill OK (send_keys): '{actual}'")
                return
        except Exception as e:
            logger.warning(f"_stripe_fill attempt 1 failed: {e}")
        try:
            actions = ActionChains(self.driver)
            actions.move_to_element(el).click(el)
            actions.key_down(Keys.CONTROL).send_keys("a").key_up(Keys.CONTROL)
            actions.send_keys(Keys.DELETE)
            for ch in value:
                actions.send_keys(ch)
            actions.perform()
            time.sleep(0.2)
            logger.info(
                f"_stripe_fill OK (ActionChains):"
                f" '{el.get_attribute('value') or ''}'"
            )
        except Exception as e:
            logger.warning(f"_stripe_fill attempt 2 failed: {e}")

    def _find_stripe_field(self, *xpaths: str):
        for xpath in xpaths:
            try:
                els = [e for e in self.driver.find_elements(By.XPATH, xpath)
                       if e.is_displayed()]
                if els:
                    logger.info(
                        f"Stripe field found:"
                        f" name='{els[0].get_attribute('name') or ''}'"
                        f" placeholder='{els[0].get_attribute('placeholder') or ''}'"
                        f" autocomplete='{els[0].get_attribute('autocomplete') or ''}'"
                    )
                    return els[0]
            except Exception:
                continue
        return None

    # ------------------------------------------------------------------ #
    #  Stripe — fill all card details
    # ------------------------------------------------------------------ #

    def fill_card_details(self, data: dict) -> None:
        logger.info("=== Filling Stripe card details ===")
        time.sleep(1)
        self.take_screenshot("stripe_before_fill")

        all_inputs = self.driver.find_elements(By.XPATH, "//input")
        logger.info(f"Total inputs on Stripe page: {len(all_inputs)}")
        for i, inp in enumerate(all_inputs[:10]):
            logger.info(
                f"  input[{i}]"
                f" name={inp.get_attribute('name') or ''}"
                f" placeholder={inp.get_attribute('placeholder') or ''}"
                f" autocomplete={inp.get_attribute('autocomplete') or ''}"
                f" visible={inp.is_displayed()}"
            )

        card_el = self._find_stripe_field(
            "//input[@name='cardNumber']",
            "//input[@name='number']",
            "//input[contains(@autocomplete,'cc-number')]",
            "//input[contains(@placeholder,'1234')]",
        )
        if card_el:
            self._stripe_fill(card_el, data.get("card_number", ""))
            logger.info(
                f"Card number after fill: '{card_el.get_attribute('value') or ''}'")
        else:
            logger.warning("Card number field not found")
        time.sleep(0.2)

        expiry_el = self._find_stripe_field(
            "//input[@name='cardExpiry']",
            "//input[@name='expiry']",
            "//input[contains(@autocomplete,'cc-exp')]",
            "//input[contains(@placeholder,'MM')]",
        )
        if expiry_el:
            self._stripe_fill(expiry_el, data.get("card_expiry", ""))
            logger.info(
                f"Expiry after fill: '{expiry_el.get_attribute('value') or ''}'")
        else:
            logger.warning("Expiry field not found")
        time.sleep(0.2)

        cvc_el = self._find_stripe_field(
            "//input[@name='cardCvc']",
            "//input[@name='cvc']",
            "//input[contains(@autocomplete,'cc-csc')]",
            "//input[contains(@placeholder,'CVC') or contains(@placeholder,'CVV')]",
        )
        if cvc_el:
            self._stripe_fill(cvc_el, data.get("card_cvv", ""))
            logger.info(
                f"CVC after fill: '{cvc_el.get_attribute('value') or ''}'")
        else:
            logger.warning("CVC field not found")
        time.sleep(0.2)

        name_el = self._find_stripe_field(
            "//input[@name='billingName']",
            "//input[contains(@autocomplete,'cc-name')]",
            "//input[@name='name']",
            "//input[contains(@placeholder,'Full name')"
            " or contains(@placeholder,'Name on card')]",
        )
        if name_el:
            self._stripe_fill(name_el, data.get("card_name", ""))
            logger.info(
                f"Name after fill: '{name_el.get_attribute('value') or ''}'")
        else:
            logger.warning("Cardholder name field not found")
        time.sleep(0.2)

        self.take_screenshot("stripe_after_fill")
        logger.info("Stripe card details fill complete")

    # ------------------------------------------------------------------ #
    #  Stripe — click Pay
    # ------------------------------------------------------------------ #

    def click_pay(self) -> None:
        logger.info("Clicking Pay button on Stripe")
        self.driver.execute_script(
            "window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(0.1)

        btns = self.driver.find_elements(
            By.XPATH,
            "//button[contains(.,'Pay')"
            " and not(contains(.,'PayPal'))"
            " and not(contains(.,'Pay with'))]"
        )
        vis = [b for b in btns if b.is_displayed() and b.is_enabled()]
        if vis:
            logger.info(f"Pay button: '{vis[-1].text.strip()[:40]}'")
            self.driver.execute_script(
                "arguments[0].scrollIntoView({block:'center'});", vis[-1])
            time.sleep(0.1)
            try:
                vis[-1].click()
            except Exception:
                self.driver.execute_script("arguments[0].click();", vis[-1])
            logger.info("Pay button clicked")
            return

        sub_btns = [
            b for b in self.driver.find_elements(
                By.XPATH, "//button[@type='submit']")
            if b.is_displayed() and b.is_enabled()
        ]
        if sub_btns:
            self.driver.execute_script(
                "arguments[0].scrollIntoView({block:'center'});", sub_btns[-1])
            time.sleep(0.1)
            try:
                sub_btns[-1].click()
            except Exception:
                self.driver.execute_script(
                    "arguments[0].click();", sub_btns[-1])
            logger.info("Pay (submit) button clicked")
            return

        self.take_screenshot("DIAG_no_pay_button")
        raise RuntimeError("Pay button not found on Stripe checkout")

    # ------------------------------------------------------------------ #
    #  Payment success — wait + status checks
    # ------------------------------------------------------------------ #

    def wait_for_payment_success(self, timeout: int = 60) -> None:
        logger.info("Waiting for payment success / redirect back to site...")
        try:
            WebDriverWait(self.driver, timeout).until(
                lambda d: "stripe.com" not in d.current_url
                or len(d.find_elements(
                    By.XPATH,
                    "//*[contains(text(),'Payment Successful')"
                    " or contains(text(),'Confirmed')"
                    " or contains(text(),'Thank you')]"
                )) > 0
            )
        except Exception:
            logger.warning("Timeout waiting for post-payment redirect")
        time.sleep(1)
        logger.info(f"Post-payment URL: {self.driver.current_url}")
        self.take_screenshot("post_payment_state")

    def is_payment_successful(self) -> bool:
        try:
            return len(self.driver.find_elements(
                By.XPATH,
                "//*[contains(text(),'Payment Successful')"
                " or contains(text(),'successful')"
                " or contains(text(),'Thank you')]"
            )) > 0
        except Exception:
            return False

    def is_booking_confirmed(self) -> bool:
        try:
            return len(self.driver.find_elements(
                By.XPATH,
                "//*[contains(text(),'Confirmed')]"
            )) > 0
        except Exception:
            return False

    def is_payment_status_paid(self) -> bool:
        try:
            return len(self.driver.find_elements(
                By.XPATH,
                "//*[contains(text(),'Paid')]"
            )) > 0
        except Exception:
            return False

    # ------------------------------------------------------------------ #
    #  Download Invoice
    #
    #  FIX: Use innerText (not textContent) to match visible rendered text.
    #  The sidebar button has an SVG icon whose textContent includes extra
    #  invisible characters — innerText gives only what the user sees.
    # ------------------------------------------------------------------ #

    def click_download_invoice(self) -> None:
        logger.info("Clicking Download Invoice")
        time.sleep(1)

        # Step 1 — scroll the Payments Summary sidebar into view
        try:
            sidebar = self.driver.find_elements(
                By.XPATH,
                "//*[contains(@class,'card') or contains(@class,'sidebar')"
                " or contains(@class,'summary')]"
                "[.//*[contains(text(),'Payments Summary')"
                " or contains(text(),'Payment Summary')]]"
            )
            if sidebar:
                self.driver.execute_script(
                    "arguments[0].scrollIntoView({block:'start'});", sidebar[0])
                time.sleep(0.5)
            else:
                self.driver.execute_script("window.scrollBy(0, 400);")
                time.sleep(0.5)
        except Exception:
            pass

        # Step 2 — XPath strategies using normalize-space
        for xpath in [
            "//a[normalize-space(.)='Download Invoice']",
            "//button[normalize-space(.)='Download Invoice']",
            "//a[contains(normalize-space(.),'Download Invoice')]",
            "//button[contains(normalize-space(.),'Download Invoice')]",
            "//*[contains(@class,'btn') and contains(.,'Download')]",
            "//*[contains(@href,'invoice') or contains(@href,'download')]",
        ]:
            try:
                els = self.driver.find_elements(By.XPATH, xpath)
                for el in els:
                    try:
                        if el.size.get("height", 0) > 0:
                            self.driver.execute_script(
                                "arguments[0].scrollIntoView({block:'center'});",
                                el)
                            time.sleep(0.3)
                            self.driver.execute_script(
                                "arguments[0].click();", el)
                            logger.info(
                                f"Download Invoice clicked:"
                                f" '{el.text.strip()[:60]}'"
                            )
                            time.sleep(1)
                            return
                    except Exception:
                        continue
            except Exception:
                continue

        # Step 3 — JS innerText scan (matches visible rendered text only)
        try:
            el = self.driver.execute_script("""
                var all = document.querySelectorAll('a, button');
                for (var i = 0; i < all.length; i++) {
                    var t = (all[i].innerText || '')
                              .toLowerCase()
                              .replace(/\\s+/g,' ')
                              .trim();
                    if (t === 'download invoice') return all[i];
                }
                for (var j = 0; j < all.length; j++) {
                    var t2 = (all[j].innerText || '')
                               .toLowerCase()
                               .replace(/\\s+/g,' ')
                               .trim();
                    if (t2.indexOf('download') !== -1
                            && t2.indexOf('invoice') !== -1) return all[j];
                }
                return null;
            """)
            if el:
                self.driver.execute_script(
                    "arguments[0].scrollIntoView({block:'center'});", el)
                time.sleep(0.3)
                self.driver.execute_script("arguments[0].click();", el)
                logger.info("Download Invoice clicked via JS innerText scan")
                time.sleep(1)
                return
        except Exception as e:
            logger.warning(f"JS innerText scan failed: {e}")

        # Step 4 — diagnostic dump
        self.take_screenshot("DIAG_download_invoice_not_found")
        logger.warning("=== ALL visible anchors/buttons ===")
        for el in self.driver.find_elements(By.XPATH, "//a | //button"):
            try:
                if el.is_displayed() and el.text.strip():
                    logger.warning(
                        f"  <{el.tag_name}>"
                        f" text='{el.text.strip()[:60]}'"
                        f" href='{el.get_attribute('href') or ''}'"
                        f" class='{el.get_attribute('class') or ''}'"
                    )
            except Exception:
                pass
        logger.warning("Download Invoice not found — continuing test")

    # ------------------------------------------------------------------ #
    #  Back to Homepage
    # ------------------------------------------------------------------ #

    def click_back_to_homepage(self) -> None:
        logger.info("Clicking Back to Homepage")
        time.sleep(0.5)

        # Step 1 — JS innerText scan
        try:
            el = self.driver.execute_script("""
                var all = document.querySelectorAll('a, button');
                for (var i = 0; i < all.length; i++) {
                    var t = (all[i].innerText || '')
                              .toLowerCase()
                              .replace(/\\s+/g,' ')
                              .trim();
                    if (t.indexOf('homepage') !== -1
                            || t.indexOf('back to home') !== -1)
                        return all[i];
                }
                return null;
            """)
            if el:
                self.driver.execute_script(
                    "arguments[0].scrollIntoView({block:'center'});", el)
                time.sleep(0.2)
                self.driver.execute_script("arguments[0].click();", el)
                logger.info("Back to Homepage clicked via JS innerText scan")
                time.sleep(1)
                return
        except Exception as e:
            logger.warning(f"JS homepage scan failed: {e}")

        # Step 2 — XPath fallback
        for xpath in [
            "//a[contains(normalize-space(.),'Back to Homepage')]",
            "//button[contains(normalize-space(.),'Back to Homepage')]",
            "//a[contains(normalize-space(.),'Homepage')]",
            "//a[@href='/' or @href='https://phptravels.net'"
            " or @href='https://phptravels.net/']",
        ]:
            els = [e for e in self.driver.find_elements(By.XPATH, xpath)
                   if e.is_displayed()]
            if els:
                self.driver.execute_script(
                    "arguments[0].scrollIntoView({block:'center'});", els[0])
                time.sleep(0.2)
                self.driver.execute_script("arguments[0].click();", els[0])
                logger.info(
                    f"Back to Homepage clicked: '{els[0].text.strip()[:50]}'")
                time.sleep(1)
                return

        logger.warning("Back to Homepage not found")

    # ------------------------------------------------------------------ #
    #  Transaction ID
    # ------------------------------------------------------------------ #

    def get_transaction_id(self) -> str:
        try:
            for el in self.driver.find_elements(
                By.XPATH,
                "//*[contains(text(),'cs_test')"
                " or contains(text(),'Transaction')]"
            ):
                if el.text.strip():
                    return el.text.strip()
        except Exception:
            pass
        return "Transaction ID not found"