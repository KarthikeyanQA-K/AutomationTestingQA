import email
import pytest
import os
from Utilities.Helpers.EmailReader import EmailReader
from Utilities.Helpers.base_helpers import BaseHelper
from datetime import datetime
from playwright.sync_api import sync_playwright, ViewportSize
from Utilities.ReadProperties import ReadConfig
from TestData.users import USERS


# =========================================================
# CLI OPTIONS
# =========================================================
def pytest_addoption(parser):
    parser.addoption("--browser_name", action="store", default="chromium")
    parser.addoption("--region", action="store", default="Test")
    parser.addoption("--headless", action="store_true")
    parser.addoption("--user", action="store", default="User1")


# =========================================================
# PLAYWRIGHT CORE
# =========================================================
@pytest.fixture(scope="session")
def playwright_instance():
    with sync_playwright() as pw:
        yield pw


@pytest.fixture(scope="class")
def browser(playwright_instance, request):
    browser_name = request.config.getoption("--browser_name").lower()
    headless = request.config.getoption("--headless")

    if browser_name == "chromium":
        browser = playwright_instance.chromium.launch(headless=headless)
    elif browser_name == "firefox":
        browser = playwright_instance.firefox.launch(headless=headless)
    elif browser_name == "webkit":
        browser = playwright_instance.webkit.launch(headless=headless)
    else:
        raise ValueError("❌ Invalid browser name")

    yield browser
    browser.close()


# =========================================================
# CLASS-SCOPED LOGIN
# =========================================================
@pytest.fixture(scope="class")
def login(browser, request):
    region = request.config.getoption("--region")

    user_marker = request.node.get_closest_marker("user")
    user = user_marker.args[0] if user_marker else request.config.getoption("--user")
    section = f"{region}_{user}"

    login_url = ReadConfig.getURL(section)
    client_id = ReadConfig.getClientID(section)
    login_id = ReadConfig.getUsername(section)
    password = ReadConfig.getPassword(section)

    context = browser.new_context(
        viewport=ViewportSize(width=1470, height=720)
    )
    page = context.new_page()

    # Centralized timeout handling
    page.set_default_timeout(30000)

    helper = BaseHelper(page)

    print(f"\n➡ [CLASS LOGIN] Launching URL: {login_url} ({section})")

    # ✅ SINGLE SOURCE OF TRUTH FOR LOGIN
    # helper.login_and_verify_dashboard(
    #     login_url=login_url,
    #     client_id=client_id,
    #     login_id=login_id,
    #     password=password,
    #     username=login_id
    # )

    # print("✅ Login successful and dashboard fully loaded")

    # yield page

    # context.close()
    skip_login_marker = request.node.get_closest_marker("skip_login")

    if not skip_login_marker:
        # Perform full login and verify dashboard if no skip_login marker
        helper = BaseHelper(page)
        helper.login_and_verify_dashboard(
            login_url=login_url,
            client_id=client_id,
            login_id=login_id,
            password=password,
            username=login_id
        )
        print("✅ Login successful and dashboard fully loaded")
    else:
        # Only navigate to the login page, without performing any login actions
        page.goto(login_url)
        print("✅ Navigated to login page (Login skipped)")

    yield page  # Provide the page object for the test

    context.close()


# =========================================================
# USER MARKER HANDLING
# =========================================================
def pytest_runtest_setup(item):
    user_marker = item.get_closest_marker("user")
    selected_user = user_marker.args[0] if user_marker else "User1"

    os.environ["TEST_USER"] = selected_user

    try:
        display_name = ReadConfig.getUserName(selected_user)
    except Exception:
        display_name = selected_user

    print(f"\n[pytest] Running test for TEST_USER = {selected_user} ({display_name})")


@pytest.fixture
def current_user(request):
    user_key = getattr(request.node, "user", None)
    if user_key:
        user_name = ReadConfig.getUserName(user_key)
        return {"key": user_key, "name": user_name}
    return None

def pytest_runtest_call(item):
    doc = item.function.__doc__
    if doc:
        print(doc.strip())

# ------------------------------------------
# HTML REPORT + GLOBAL METRICS CONFIGURATION
# ------------------------------------------

def pytest_configure(config):
    # -------------------------
    # GLOBAL RESULTS (MASTER)
    # -------------------------
    if not hasattr(config, "workerinput"):
        config._global_results = {
            "passed": 0,
            "failed": 0,
            "skipped": 0,
        }
        config.start_time = datetime.now()

    # -------------------------
    # HTML REPORT PATH
    # -------------------------
    if hasattr(config.option, "htmlpath") and not config.option.htmlpath:
        reports_dir = os.path.join(os.getcwd(), "Reports")
        os.makedirs(reports_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        config.option.htmlpath = os.path.join(
            reports_dir,
            f"Cflow-Automation-Report-CI-CD--{timestamp}.html"
        )


# ------------------------------------------
# PYTEST-HTML METADATA (single source)
# ------------------------------------------

def pytest_metadata(metadata):
    metadata.clear()
    metadata.update({
        "Region": "Test",
        "User": "User1-Dinesh Aravinth",
        "Base URL": "https://testapp.cflowapps.com",
        "Execution Time": datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
    })



# =========================================================
# GLOBAL TEST METRICS (XDIST SAFE)
# =========================================================

@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()

    if report.when != "call":
        return

    config = item.config

    if hasattr(config, "workeroutput"):
        if report.passed:
            config.workeroutput["passed"] = config.workeroutput.get("passed", 0) + 1
        elif report.failed:
            config.workeroutput["failed"] = config.workeroutput.get("failed", 0) + 1
        elif report.skipped:
            config.workeroutput["skipped"] = config.workeroutput.get("skipped", 0) + 1



def pytest_testnodedown(node, error):
    results = node.config._global_results
    worker = node.workeroutput or {}

    results["passed"] += worker.get("passed", 0)
    results["failed"] += worker.get("failed", 0)
    results["skipped"] += worker.get("skipped", 0)



def pytest_sessionfinish(session, exitstatus):
    if hasattr(session.config, "workerinput"):
        return

    end_time = datetime.now()
    start_time = session.config.start_time
    duration = end_time - start_time

    results = session.config._global_results
    total = results["passed"] + results["failed"] + results["skipped"]

    with open("test_env.properties", "w", encoding="utf-8") as properties_file:
        properties_file.write(f"TOTAL_TESTS={total}\n")
        properties_file.write(f"PASSED={results['passed']}\n")
        properties_file.write(f"FAILED={results['failed']}\n")
        properties_file.write(f"SKIPPED={results['skipped']}\n")
        properties_file.write(f"START_TIME={start_time}\n")
        properties_file.write(f"END_TIME={end_time}\n")
        properties_file.write(f"DURATION={duration}\n")

    print("✅ test_env.properties generated successfully (MASTER node)")

LOGIN_URL = "https://testapp.cflowapps.com/login"
CLIENT_ID = "cflowautomation.com"

@pytest.fixture
def login_as(browser):
    """
    Login factory: login_as("A1"), login_as("A2"), etc.
    Returns: page, context, browser
    """

    def _login(user_key: str):
        context = browser.new_context()
        page = context.new_page()

        helper = BaseHelper(page)
        user = USERS[user_key]

        helper.login_and_verify_dashboard(
            login_url=LOGIN_URL,
            client_id=CLIENT_ID,
            login_id=user["username"],
            password=user["password"],
            username=user["display"]
        )

        # ✅ RETURN 3 VALUES (matches test expectations)
        return page, context, browser

    yield _login

# it will get the email and check the dta
@pytest.fixture
def get_reset_link(request):
    marker = request.node.get_closest_marker("user")
    if not marker or not marker.args:
        pytest.fail("❌ @pytest.mark.user('<username>') marker is missing")

    user = marker.args[0]
    section = f"Test_{user}"

    email = ReadConfig.config.get(section, "email")
    email_password = ReadConfig.config.get(section, "email_password")
    imap_server = ReadConfig.config.get(section, "imap_server", fallback="imap.gmail.com")
    sender = ReadConfig.config.get(section, "sender", fallback=None)

    def fetch_reset_link():
        print(f"📧 Fetching reset email for user: {user}")

        result = EmailReader.wait_for_reset_email(
            email=email, 
            email_password=email_password,
            imap_server=imap_server,
            sender=sender,
            subject_keyword="Reset",
            timeout=180,
        )

        if not result or "link" not in result:
            pytest.fail("❌ Reset email not found or link missing")
        return {
            "link": result["link"],
            "timestamp": result.get("timestamp")
        }

    return fetch_reset_link