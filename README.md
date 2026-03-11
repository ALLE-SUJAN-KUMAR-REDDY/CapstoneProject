# CapstoneProject2 — Flight Booking E2E Test Automation

## Overview
End-to-end Selenium + Pytest automation for [phptravels.net/flights](https://phptravels.net/flights).  
Covers one-way and round-trip booking flows using **Page Object Model** and **Data-Driven Testing** (Excel).

---

## Project Structure
```
CapstoneProject2/
├── pages/
│   ├── base_page.py            # Common Selenium helpers (waits, clicks, screenshots)
│   ├── flight_search_page.py   # Search form POM
│   ├── flight_results_page.py  # Results listing POM
│   ├── booking_page.py         # Booking/checkout form POM
│   └── payment_page.py         # Invoice + Stripe payment POM
├── tests/
│   ├── conftest.py             # Test-level fixtures (Excel data loaders)
│   └── test_end_to_end_booking.py  # All 12 test cases (single file)
├── utils/
│   ├── logger.py               # Centralized logging (console + file)
│   └── excel_utils.py          # openpyxl reader → list of dicts
├── test_data/
│   └── test_data.xlsx          # OneWayFlight + RoundTripFlight sheets
├── reports/                    # pytest-html reports (auto-generated)
├── screenshots/                # Auto-saved screenshots per step
├── logs/                       # Daily log files
├── conftest.py                 # Root: WebDriver setup/teardown
├── generate_excel.py           # Re-generate test_data.xlsx
├── pytest.ini                  # Pytest configuration
└── requirements.txt            # Python dependencies
```

---

## Setup

```bash
# 1. Clone repo and enter folder
git clone <your-repo-url>
cd CapstoneProject2

# 2. Create virtual environment
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt
```

---

## Running Tests

```bash
# Run all tests
pytest

# Run only smoke tests
pytest -m smoke

# Run only one-way tests
pytest -m oneway

# Run only round-trip tests
pytest -m roundtrip

# Run a specific test case
pytest tests/test_end_to_end_booking.py::TestOneWayEndToEndBooking::test_oneway_end_to_end_booking -v
```

Reports are auto-saved to `reports/report.html`.  
Screenshots are saved to `screenshots/`.  
Logs are saved to `logs/`.

---

## Test Data
Edit `test_data/test_data.xlsx` directly, or run:
```bash
python generate_excel.py
```

### Sheets
| Sheet | Description |
|-------|-------------|
| `OneWayFlight` | One-way search + booking data |
| `RoundTripFlight` | Round-trip search + booking data |

---

## Test Cases
| ID | Class | Description |
|----|-------|-------------|
| TC-01 | Validations | Flights page loads successfully |
| TC-02 | Validations | Select departure & arrival cities |
| TC-03 | Validations | Select future departure date |
| TC-04 | Validations | Select number of passengers |
| TC-05 | Validations | Validate no past date selection |
| TC-06 | OneWay Search | Search one-way flight + results load |
| TC-07 | OneWay Search | Validate search results displayed |
| TC-08 | OneWay Search | Verify price is displayed |
| TC-09 | RoundTrip Search | Search round-trip flight + results load |
| TC-10 | RoundTrip Search | Verify round-trip prices displayed |
| TC-11 | OneWay E2E | Full one-way booking → payment → success |
| TC-12 | RoundTrip E2E | Full round-trip booking → payment → success |

---

## Tech Stack
- **Python 3.11+**
- **Selenium 4** — browser automation
- **Pytest** — test runner
- **pytest-html** — HTML report generation
- **openpyxl** — Excel data-driven testing
- **webdriver-manager** — automatic ChromeDriver management
