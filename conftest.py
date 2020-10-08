from selenium.webdriver import FirefoxOptions


def pytest_setup_options():
    options = FirefoxOptions()
    options.add_argument("--headless")
    return options
