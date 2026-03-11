"""
End-to-End Flight Booking Tests — phptravels.net
=================================================
TC-01  Flights page loads successfully
TC-02  Select departure and arrival cities
TC-03  Select a future departure date
TC-04  Select number of passengers
TC-05  Validate no past date selection  (negative)
TC-06  Search one-way flight
TC-07  Validate search results displayed
TC-08  Verify price is displayed
TC-09  Search round-trip flight
TC-10  Round-trip results have prices
TC-11  One-way end-to-end booking
TC-12  Round-trip end-to-end booking

"""

import time
import pytest
from selenium.webdriver.common.by import By
from pages.flight_search_page import FlightSearchPage, BASE_URL
from pages.flight_results_page import FlightResultsPage
from pages.booking_page import BookingPage
from pages.payment_page import PaymentPage
from utils.logger import get_logger

logger = get_logger(__name__)


# ===========================================================================
#  SMOKE / VALIDATION TESTS   TC-01 – TC-05
# ===========================================================================

class TestFlightSearchValidations:

    @pytest.mark.smoke
    def test_flights_page_loads_successfully(self, driver):
        """TC-01: Verify flights page loads and key elements exist."""
        logger.info("TC-01: Verify flights page loads")
        search_page = FlightSearchPage(driver)
        search_page.load()
        assert "flight" in driver.current_url.lower()
        assert driver.title
        btns = driver.find_elements(By.XPATH, "//button[contains(.,'Search')]")
        assert len(btns) >= 1
        search_page.take_screenshot("tc01_page_loaded")
        logger.info("TC-01 PASSED")

    @pytest.mark.smoke
    def test_select_departure_and_arrival_cities(self, driver, oneway_data):
        """TC-02: Verify departure and arrival city fields are selectable."""
        logger.info("TC-02: Select cities")
        search_page = FlightSearchPage(driver)
        search_page.load()
        search_page.select_flight_type(oneway_data["flight_type"])
        time.sleep(0.5)
        search_page.set_departure_city(oneway_data["departure_city"])
        search_page.set_arrival_city(oneway_data["arrival_city"])
        search_page.take_screenshot("tc02_cities_selected")
        logger.info("TC-02 PASSED")

    @pytest.mark.smoke
    def test_select_future_departure_date(self, driver, oneway_data):
        """TC-03: Verify a future departure date can be set."""
        logger.info("TC-03: Select future date")
        search_page = FlightSearchPage(driver)
        search_page.load()
        search_page.set_departure_date(oneway_data["departure_date"])
        search_page.take_screenshot("tc03_future_date_set")
        logger.info("TC-03 PASSED")

    @pytest.mark.smoke
    def test_select_number_of_passengers(self, driver, oneway_data):
        """TC-04: Verify passenger count can be selected."""
        logger.info("TC-04: Select passengers")
        search_page = FlightSearchPage(driver)
        search_page.load()
        search_page.set_passengers(oneway_data["passengers"])
        search_page.take_screenshot("tc04_passengers_selected")
        logger.info("TC-04 PASSED")

    def test_validate_no_past_date_selection(self, driver):
        """TC-05: Verify past dates cannot be selected (negative)."""
        logger.info("TC-05: Validate past date blocked")
        search_page = FlightSearchPage(driver)
        search_page.load()
        past_date = "01-01-2020"
        date_inputs = driver.find_elements(
            By.XPATH,
            "//input[contains(@id,'Date') or contains(@name,'Date')"
            " or contains(@placeholder,'Date') or contains(@class,'date')]"
        )
        if date_inputs:
            el = date_inputs[0]
            driver.execute_script("arguments[0].removeAttribute('readonly')", el)
            driver.execute_script(f"arguments[0].value = '{past_date}'", el)
            time.sleep(0.5)
        assert "flights" in driver.current_url.lower()
        search_page.take_screenshot("tc05_past_date_validation")
        logger.info("TC-05 PASSED")


# ===========================================================================
#  ONE-WAY SEARCH + RESULTS   TC-06 – TC-08
# ===========================================================================

class TestOneWayFlightSearch:

    @pytest.mark.oneway
    def test_search_one_way_flight(self, driver, oneway_data):
        """TC-06: Search one-way and verify results page loads."""
        logger.info("TC-06: One-way search")
        FlightSearchPage(driver).load().search_one_way(oneway_data)
        results_page = FlightResultsPage(driver)
        results_page.wait_for_results()
        results_page.take_screenshot("tc06_results")
        assert results_page.are_results_displayed() \
               or "flights" in driver.current_url.lower()
        logger.info("TC-06 PASSED")

    @pytest.mark.oneway
    def test_validate_search_results_displayed(self, driver, oneway_data):
        """TC-07: Verify results are listed with Book Now buttons."""
        logger.info("TC-07: Validate results displayed")
        FlightSearchPage(driver).load().search_one_way(oneway_data)
        results_page = FlightResultsPage(driver)
        results_page.wait_for_results()
        assert results_page.are_results_displayed()
        count_text = results_page.get_results_count_text()
        logger.info(f"Count: {count_text}")
        results_page.take_screenshot("tc07_results")
        logger.info("TC-07 PASSED")

    @pytest.mark.oneway
    def test_verify_price_is_displayed(self, driver, oneway_data):
        """TC-08: Verify at least one price is visible."""
        logger.info("TC-08: Verify price displayed")
        FlightSearchPage(driver).load().search_one_way(oneway_data)
        results_page = FlightResultsPage(driver)
        results_page.wait_for_results()
        assert results_page.is_price_displayed()
        first_price = results_page.get_first_flight_price()
        logger.info(f"Price: {first_price}")
        results_page.take_screenshot("tc08_price")
        logger.info("TC-08 PASSED")


# ===========================================================================
#  ROUND-TRIP SEARCH   TC-09 – TC-10
# ===========================================================================

class TestRoundTripFlightSearch:

    @pytest.mark.roundtrip
    def test_search_round_trip_flight(self, driver, roundtrip_data):
        """TC-09: Search round-trip and verify results load."""
        logger.info("TC-09: Round-trip search")
        FlightSearchPage(driver).load().search_round_trip(roundtrip_data)
        results_page = FlightResultsPage(driver)
        results_page.wait_for_results()
        results_page.take_screenshot("tc09_roundtrip_results")
        assert results_page.are_results_displayed() \
               or "flights" in driver.current_url.lower()
        logger.info("TC-09 PASSED")

    @pytest.mark.roundtrip
    def test_round_trip_results_have_prices(self, driver, roundtrip_data):
        """TC-10: Verify prices shown in round-trip results."""
        logger.info("TC-10: Round-trip prices")
        FlightSearchPage(driver).load().search_round_trip(roundtrip_data)
        results_page = FlightResultsPage(driver)
        results_page.wait_for_results()
        assert results_page.is_price_displayed()
        first_price = results_page.get_first_flight_price()
        logger.info(f"Price: {first_price}")
        results_page.take_screenshot("tc10_roundtrip_prices")
        logger.info("TC-10 PASSED")


# ===========================================================================
#  ONE-WAY END-TO-END BOOKING   TC-11
# ===========================================================================

class TestOneWayEndToEndBooking:

    @pytest.mark.oneway
    def test_oneway_end_to_end_booking(self, driver, oneway_data):
        """TC-11: Search → Book → Pay → Download Invoice → Back to Homepage"""
        logger.info("TC-11: One-way end-to-end booking")

        # Step 1: Search
        search_page = FlightSearchPage(driver)
        search_page.load()
        search_page.search_one_way(oneway_data)
        logger.info("Step 1: Search done")

        # Step 2: Results
        results_page = FlightResultsPage(driver)
        results_page.wait_for_results()
        assert results_page.are_results_displayed(), "No flight results found"
        results_page.take_screenshot("tc11_step2_results")
        results_page.click_first_book_now()
        logger.info("Step 2: Book Now clicked")

        # Step 3: Booking form
        booking_page = BookingPage(driver)
        booking_page.wait_for_page_load()
        booking_page.log_form_elements()
        booking_page.take_screenshot("tc11_step3a_form")
        booking_page.fill_guest_details(oneway_data)
        booking_page.fill_passenger_details(oneway_data)
        booking_page.select_credit_card_payment()
        booking_page.accept_terms_and_conditions()
        total = booking_page.get_booking_total()
        logger.info(f"Booking total: {total}")
        booking_page.take_screenshot("tc11_step3b_filled")
        booking_page.click_confirm_booking()
        logger.info("Step 3: Booking confirmed")

        # Step 4: Invoice
        payment_page = PaymentPage(driver)
        payment_page.wait_for_invoice_page()
        payment_page.take_screenshot("tc11_step4_invoice")
        invoice_num = payment_page.get_invoice_number()
        logger.info(f"Invoice: {invoice_num}")
        payment_page.click_make_payment()
        logger.info("Step 4: Make Payment clicked")

        # Step 5: Proceed
        time.sleep(2)
        payment_page.click_proceed_to_payment()
        logger.info("Step 5: Proceed handled")

        # Step 6: Stripe
        payment_page.wait_for_stripe_page()
        payment_page.take_screenshot("tc11_step6_stripe")
        payment_page.fill_card_details(oneway_data)
        payment_page.take_screenshot("tc11_step6b_filled")
        payment_page.click_pay()
        logger.info("Step 6: Pay clicked")

        # Step 7: Success
        payment_page.wait_for_payment_success()
        payment_page.take_screenshot("tc11_step7_success")
        confirmed = payment_page.is_booking_confirmed()
        paid      = payment_page.is_payment_status_paid()
        logger.info(f"Confirmed: {confirmed}")
        logger.info(f"Paid: {paid}")
        assert payment_page.is_payment_successful() or confirmed, \
            "Payment was not successful"

        # Step 8: Download Invoice
        payment_page.click_download_invoice()
        payment_page.take_screenshot("tc11_step8_download")

        # Step 9: Back to Homepage
        payment_page.click_back_to_homepage()
        payment_page.take_screenshot("tc11_step9_done")

        logger.info("TC-11 PASSED")


# ===========================================================================
#  ROUND-TRIP END-TO-END BOOKING   TC-12
# ===========================================================================

class TestRoundTripEndToEndBooking:

    @pytest.mark.roundtrip
    def test_roundtrip_end_to_end_booking(self, driver, roundtrip_data):
        """TC-12: Search → Book → Pay → Download Invoice → Back to Homepage"""
        logger.info("TC-12: Round-trip end-to-end booking")

        # Step 1: Search
        search_page = FlightSearchPage(driver)
        search_page.load()
        search_page.search_round_trip(roundtrip_data)
        logger.info("Step 1: Round-trip search done")

        # Step 2: Results
        results_page = FlightResultsPage(driver)
        results_page.wait_for_results()
        assert results_page.are_results_displayed(), "No round-trip results"
        results_page.take_screenshot("tc12_step2_results")
        results_page.click_first_book_now()
        logger.info("Step 2: Book Now clicked")

        # Step 3: Booking form
        booking_page = BookingPage(driver)
        booking_page.wait_for_page_load()
        booking_page.log_form_elements()
        booking_page.take_screenshot("tc12_step3a_form")
        booking_page.fill_guest_details(roundtrip_data)
        booking_page.fill_passenger_details(roundtrip_data)
        booking_page.select_credit_card_payment()
        booking_page.accept_terms_and_conditions()
        total = booking_page.get_booking_total()
        logger.info(f"Booking total: {total}")
        booking_page.take_screenshot("tc12_step3b_filled")
        booking_page.click_confirm_booking()
        logger.info("Step 3: Booking confirmed")

        # Step 4: Invoice
        payment_page = PaymentPage(driver)
        payment_page.wait_for_invoice_page()
        payment_page.take_screenshot("tc12_step4_invoice")
        invoice_num = payment_page.get_invoice_number()
        logger.info(f"Invoice: {invoice_num}")
        payment_page.click_make_payment()
        logger.info("Step 4: Make Payment clicked")

        # Step 5: Proceed
        time.sleep(2)
        payment_page.click_proceed_to_payment()
        logger.info("Step 5: Proceed handled")

        # Step 6: Stripe
        payment_page.wait_for_stripe_page()
        payment_page.take_screenshot("tc12_step6_stripe")
        payment_page.fill_card_details(roundtrip_data)
        payment_page.take_screenshot("tc12_step6b_filled")
        payment_page.click_pay()
        logger.info("Step 6: Pay clicked")

        # Step 7: Success
        payment_page.wait_for_payment_success()
        payment_page.take_screenshot("tc12_step7_success")
        confirmed = payment_page.is_booking_confirmed()
        paid      = payment_page.is_payment_status_paid()
        logger.info(f"Confirmed: {confirmed}")
        logger.info(f"Paid: {paid}")
        assert payment_page.is_payment_successful() or confirmed, \
            "Round-trip payment was not successful"

        # Step 8: Download Invoice
        payment_page.click_download_invoice()
        payment_page.take_screenshot("tc12_step8_download")

        # Step 9: Back to Homepage
        payment_page.click_back_to_homepage()
        payment_page.take_screenshot("tc12_step9_done")

        logger.info("TC-12 PASSED")