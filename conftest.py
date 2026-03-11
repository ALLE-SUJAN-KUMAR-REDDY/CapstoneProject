import os
import glob
import pytest
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from utils.logger import get_logger

logger = get_logger("conftest")

# Resolve ChromeDriver path once at module load — avoids re-downloading on every test
# and prevents ChunkedEncodingError from repeated download attempts
os.environ["WDM_ARCH"] = "64"
_driver_path = None

def _get_driver_path() -> str:
    global _driver_path
    if _driver_path and os.path.isfile(_driver_path):
        return _driver_path

    raw = ChromeDriverManager().install()

    # webdriver-manager sometimes returns THIRD_PARTY_NOTICES instead of the exe
    if not raw.endswith(".exe"):
        base = os.path.dirname(raw)
        exes = glob.glob(os.path.join(base, "**", "chromedriver.exe"), recursive=True)
        if exes:
            raw = exes[0]
        else:
            raise RuntimeError(f"chromedriver.exe not found near: {raw}")

    logger.info(f"ChromeDriver resolved: {raw}")
    _driver_path = raw
    return _driver_path


def pytest_configure(config):
    """Ensure output directories exist before any test runs."""
    for folder in ["reports", "screenshots", "logs"]:
        os.makedirs(folder, exist_ok=True)


def pytest_html_report_title(report):
    report.title = "Flight Booking E2E Test Report"


@pytest.fixture(scope="function")
def driver(request):
    """
    Pytest fixture: creates a Chrome WebDriver instance per test function.
    Takes a screenshot on failure, then quits the browser.
    """
    logger.info(f"Setting up Chrome WebDriver for: {request.node.name}")

    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--disable-infobars")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    service = Service(_get_driver_path())
    chrome_driver = webdriver.Chrome(service=service, options=options)
    chrome_driver.implicitly_wait(5)
    chrome_driver.set_page_load_timeout(60)

    yield chrome_driver

    # --- Teardown ---
    if request.node.rep_call.failed if hasattr(request.node, "rep_call") else False:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = request.node.name.replace("/", "_").replace(":", "_")
        screenshot_path = os.path.join("screenshots", f"FAIL_{safe_name}_{timestamp}.png")
        try:
            chrome_driver.save_screenshot(screenshot_path)
            logger.error(f"Test FAILED — screenshot saved: {screenshot_path}")
        except Exception as e:
            logger.warning(f"Could not save failure screenshot: {e}")

    logger.info(f"Tearing down WebDriver for: {request.node.name}")
    chrome_driver.quit()


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Make test outcome available inside fixtures for screenshot-on-fail."""
    outcome = yield
    rep = outcome.get_result()
    setattr(item, f"rep_{rep.when}", rep)
