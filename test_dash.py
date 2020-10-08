import dash
import time
import dash_html_components as html
from dash.testing.application_runners import import_app


def test_001_unemployed_officer(dash_duo):
    app = import_app("app")
    dash_duo.start_server(app)
    # close out of modal disclaimer
    dash_duo.multiple_click("#disclaimer_btn", 1)
    dash_duo.multiple_click("#close", 1)
    time.sleep(0.5)
    inputbox = dash_duo.find_element("#officer_input")
    dash_duo.find_element("#data_html")
    inputbox.send_keys("Feaman, Adam\n")
    dash_duo.multiple_click("#submit", 1)
    dash_duo.wait_for_contains_text("#officer_name", "Feaman")
    dash_duo.wait_for_contains_text(
        "#officer-info", "No longer employed with the SLMPD"
    )


def test_002_employed_officer(dash_duo):
    app = import_app("app")
    dash_duo.start_server(app)
    # close out of modal disclaimer
    dash_duo.multiple_click("#disclaimer_btn", 1)
    dash_duo.multiple_click("#close", 1)
    time.sleep(0.5)
    inputbox = dash_duo.find_element("#officer_input")
    dash_duo.find_element("#data_html")
    inputbox.send_keys("Taylor, Heather\n")
    dash_duo.multiple_click("#submit", 1)
    dash_duo.wait_for_contains_text("#officer_name", "Taylor")
    dash_duo.wait_for_contains_text("#officer-info", "DSN:")
