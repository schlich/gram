import dash
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
import dash_table
import pandas as pd
import pygsheets as pyg
import plotly.graph_objs as go
from dotenv import load_dotenv
from flask_talisman import Talisman
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate


external_stylesheets = [dbc.themes.JOURNAL]
load_dotenv()

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
server = app.server

# csp = {
#     'default-src': '\'self\'',
#     'script-src': '\'self\'',
#     'style-src': '\'self\''
#     }
# Talisman(server, content_security_policy=csp)

client = pyg.authorize(service_account_env_var="GOOGLE_SHEETS_CREDS_JSON")


def fetch_data(table_name):
    table = client.open("EMR Database").worksheet("title", table_name).get_all_values()
    headers = table.pop(0)
    data = pd.DataFrame(table, columns=headers)
    return data


officers = fetch_data("officers")
officers["Officer Name"] = officers["Last Name"] + ", " + officers["First Name"]
# officers['DSN'] = officers['DSN'].astype('int64')
# print(officers.index.dtype, officers['DSN'])
complaints = fetch_data("complaints")
officers_complaints = fetch_data("officers_complaints")
data = officers_complaints.merge(officers, on="DSN", how="outer").merge(
    complaints, on="File #", how="outer", suffixes=["_2020", ""]
)

race_counts = complaints["Race of Complainant"].value_counts()
race_counts = race_counts.drop("")
bosnians = race_counts.loc["Bosnian"]
asians = race_counts.loc["Asian"]
hispanics = race_counts.loc["Hispanic"]
race_counts["Other"] += bosnians + asians + hispanics
race_counts.drop(["Bosnian", "Asian", "Hispanic"], inplace=True)
display_data = data[
    [
        "Officer Name",
        "DSN",
        "Rank_2020",
        "2020 Assignment",
        "Date of Incident",
        "Location of Incident",
        "Nature of Complaint",
        "Redacted Complainant's Statement",
        "Age",
        "Race of Complainant",
        "Complainant Gender",
        "FY 2021 Salary",
        "Rank",
        "Assignment",
        "District",
        "On-Duty",
        "District",
        "City",
    ]
]
column_names = [
    "Date of Incident",
    "Nature of Complaint",
    "Age",
    "Race of Complainant",
    "Complainant Gender",
]

app.layout = html.Div(
    [
        dbc.Modal(
            [
                dbc.ModalHeader("Welcome!"),
                dbc.ModalBody(
                    children="The GRAM Policing project is a tool to help hold police accountable to the public they serve.\nThis database is part of an ongoing and evolving grassroots project to make records of police interactions available and useful to the public.\n",
                    id="disclaimer_txt",
                ),
                dbc.ModalFooter(
                    [
                        dbc.Button(
                            "View Data Disclaimer",
                            id="disclaimer_btn",
                            className="ml-auto",
                        ),
                        html.Div(
                            dbc.Button("Close", id="close", className="ml-auto"),
                            id="close-div",
                            style={"display": "none"},
                        ),
                    ]
                ),
            ],
            id="modal",
            is_open=True,
        ),
        html.Br(),
        html.A(
            html.Img(
                src="https://jointhegram.org/wp-content/uploads/2018/02/cropped-GRAM_1c_web_long_tag.jpg",
                height=90,
                style={
                    "display": "block",
                    "margin-left": "auto",
                    "margin-right": "auto",
                },
            ),
            href="https://jointhegram.org",
        ),
        html.Br(),
        html.H2("Saint Louis Metropolitan Police Department (SLMPD)"),
        html.H3("Employee Misconduct Report (EMR) - Allegations"),
        html.P("EMRs obtained via Missouri Open Records Requests from 2010-2019"),
        html.H5("Select an officer to see misconduct reports:"),
        html.Datalist(
            id="officers",
            children=[html.Option(value=i) for i in officers["Officer Name"].to_list()],
        ),
        dcc.Input(id="officer_input", list="officers"),
        dbc.Button("Search", id="submit"),
        html.Div(
            [
                html.Br(),
                html.Br(),
                html.H3("Officer Name", id="officer_name"),
                html.Div(
                    id="officer-info",
                ),
                html.Div(
                    [
                        html.Br(),
                        html.H4("EMR Complaint Summary"),
                        html.P(
                            "Select incident date for more information on the allegation:"
                        ),
                        dash_table.DataTable(
                            id="complaints",
                            columns=[
                                {"name": i, "id": i, "selectable": True}
                                for i in column_names
                            ],
                            data=pd.DataFrame().to_dict("records"),
                            # hidden_columns=['Officer Name'],
                            row_selectable="single",
                            style_data={"whiteSpace": "normal", "height": "auto"},
                        ),
                        html.Div(
                            id="incident-info",
                        ),
                    ]
                ),
                html.Br(),
                html.Br(),
                # dbc.Button("Back to Home", id="back-button"),
            ],
            id="data_html",
            style={"display": "none"},
        ),
        html.Br(),
        html.Br(),
        html.Hr(),
        html.Div(
            [
                html.H3("Summary Statistics from EMRs: 2010-2019"),
                # html.P('Tip: Click on a legend entry to add/remove groups'),
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                html.H4("Race of Complainant"),
                                dcc.Graph(
                                    figure=go.Figure(
                                        data=go.Pie(
                                            labels=race_counts.index.tolist(),
                                            values=race_counts.values.tolist(),
                                            textinfo="label+value",
                                        ),
                                        layout_margin_t=10,
                                        layout_showlegend=False,
                                    )
                                ),
                            ],
                        ),
                        dbc.Col(
                            [
                                html.H4("Gender of Complainant"),
                                dcc.Graph(
                                    figure=go.Figure(
                                        data=go.Pie(
                                            labels=complaints["Complainant Gender"]
                                            .value_counts()
                                            .index.tolist(),
                                            values=complaints["Complainant Gender"]
                                            .value_counts()
                                            .values.tolist(),
                                            textinfo="label+value",
                                        ),
                                        layout_margin_t=10,
                                        layout_showlegend=False,
                                    )
                                ),
                            ],
                        ),
                        dbc.Col(
                            [
                                html.H4("Police District of Incident Location"),
                                html.P("(See map below)"),
                                dcc.Graph(
                                    figure=go.Figure(
                                        data=go.Pie(
                                            labels=complaints["District"]
                                            .value_counts()
                                            .index.tolist(),
                                            values=complaints["District"]
                                            .value_counts()
                                            .values.tolist(),
                                            textinfo="label+value",
                                            textposition="inside",
                                        ),
                                        layout_margin_t=10,
                                        layout_showlegend=False,
                                    )
                                ),
                            ]
                        ),
                    ]
                ),
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                html.H4("Nature of Complaint"),
                                dcc.Graph(
                                    figure=go.Figure(
                                        data=go.Pie(
                                            labels=complaints["Nature of Complaint"]
                                            .value_counts()
                                            .index.tolist(),
                                            values=complaints["Nature of Complaint"]
                                            .value_counts()
                                            .values.tolist(),
                                            textinfo="label+value",
                                            textposition="inside",
                                        ),
                                        layout_margin_t=10,
                                        layout_showlegend=False,
                                    )
                                ),
                            ],
                        ),
                        dbc.Col(
                            [
                                html.H4(
                                    "Click on the image below to view our interactive map of SLMPD and misconduct data:"
                                ),
                                html.A(
                                    html.Img(
                                        src="assets/stl_police_districts_map.PNG",
                                        width="80%",
                                    ),
                                    href="https://public.tableau.com/profile/andrew.arkills#!/vizhome/PoliceDistrictMapping/Dashboard1",
                                ),
                            ]
                        ),
                    ]
                ),
            ],
            id="charts",
        ),
        # dbc.Container(
        #     [
        #         # html.Iframe(
        #         # 	src='https://public.tableau.com/views/PoliceDistrictMapping/Dashboard1?:showVizHome=no&:embed=true',
        #         # 	height="800",
        #         # 	width="100%",
        #         # ),
        #         html.H4(
        #             "Click on the image below to view our interactive map of SLMPD data and misconduct data:"
        #         ),
        #         html.A(
        #             html.Img(src="assets/stl_police_districts_map.PNG"),
        #             href="https://public.tableau.com/profile/andrew.arkills#!/vizhome/PoliceDistrictMapping/Dashboard1",
        #         ),
        #     ],
        #     style={"width": "50%"},
        # ),
    ],
    className="container",
)


@app.callback(
    [
        Output("complaints", "data"),
        Output("data_html", "style"),
        Output("officer_name", "children"),
        Output("charts", "style"),
        Output("officer-info", "children"),
    ],
    [Input("submit", "n_clicks")],
    [State("officer_input", "value")],
)
def update_data(n_clicks, officer):
    if n_clicks:
        complaints = (
            display_data[display_data["Officer Name"] == officer]
            .sort_values("Date of Incident")
            .to_dict("records")
        )
        firstrow = complaints[0]
        dsn = firstrow["DSN"]
        rank = firstrow["Rank_2020"]
        assignment = firstrow["2020 Assignment"]
        salary = firstrow["FY 2021 Salary"]
        if not rank:
            officer_info = "No longer employed with the SLMPD"
        else:
            officer_info = [
                html.H5([html.B("DSN: "), str(dsn)]),
                html.P([html.B("Rank: "), str(rank)]),
                html.P([html.B("Assignment: "), str(assignment)]),
                html.P([html.B("2021 Salary: "), str(salary)]),
            ]
        return (
            complaints,
            {"display": "block"},
            officer,
            {"display": "none"},
            officer_info,
        )
    else:
        raise PreventUpdate


@app.callback(
    Output("incident-info", "children"),
    [
        Input("complaints", "derived_virtual_data"),
        Input("complaints", "derived_virtual_selected_rows"),
    ],
)
def get_statement(rows, derived_virtual_selected_rows):
    if not derived_virtual_selected_rows:
        incident_info = "Select a row to view the complainant's statement and more info about the incident"
    else:
        data = pd.DataFrame(rows)
        statement = data.loc[
            derived_virtual_selected_rows[0], "Redacted Complainant's Statement"
        ]
        incident_info = [
            # html.P(
            #     html.B("Nature of Complaint: "),
            #     data.loc[derived_virtual_selected_rows[0], "Nature of Complaint"],
            # ),
            html.H5("Complainant's Statement:"),
            html.P(statement),
            html.P(statement),
            html.H5("Officer information at time of incident:"),
            html.P(
                [html.B("Rank: "), data.loc[derived_virtual_selected_rows[0], "Rank"]]
            ),
            html.P(
                [
                    html.B("Assignment: "),
                    data.loc[derived_virtual_selected_rows[0], "Assignment"],
                ]
            ),
            html.P(
                [
                    html.B("On-Duty: "),
                    data.loc[derived_virtual_selected_rows[0], "On-Duty"],
                ]
            ),
            html.H5("Location of Incident"),
            html.P(
                [
                    html.B("District: "),
                    data.loc[derived_virtual_selected_rows[0], "District"],
                ]
            ),
            html.P(
                [html.B("City: "), data.loc[derived_virtual_selected_rows[0], "City"]]
            ),
        ]
    return incident_info


@app.callback(
    [
        Output("disclaimer_txt", "children"),
        Output("close-div", "style"),
        Output("disclaimer_btn", "style"),
    ],
    [Input("disclaimer_btn", "n_clicks")],
)
def show_disclaimer(n_clicks):
    if n_clicks and n_clicks > 0:
        text = (
            "The information provided on the GRAM Accountability Project "
            + "with respect to Police Data comes primarily from the Saint Louis Metropolitan "
            + "Police Department in response to Sunshine requests.  \n\nAt this time, the search "
            + "engine allows the user to search all available Employee Misconduct Reports (EMRs) "
            + "from 2010 to 2019. The records published have been deemed to be open to the public "
            + "by the SLMPD and Sunshine Law.  The SLMPD is not required by the Missouri Sunshine "
            + "Law to disclose all EMR Allegations.  That means that only a small fraction of the "
            + "complaints filed as EMRs are open and obtainable by the Sunshine Law. \n\n"
            + "The SLMPD does not provide the Internal Affairs or COB rulings on individual "
            + "complaints; thus the public is left only with the allegations of misconduct.  \n\n"
            + "GRAM cannot guarantee the accuracy of the data provided. However, the data "
            + "was faithfully copied from open record reports obtained directly from the SLMPD.  "
            + "We are committed to transparency in the publication of the data and welcome critiques. \n\n"
            + "*Identifying information of civilian complainants has been removed from the search "
            + "engine database."
        )

        return text, {"display": "block"}, {"display": "none"}
    return (
        "The GRAM Policing project is a tool to help hold police accountable to the public they serve.\nThis database is part of an ongoing and evolving grassroots project to make records of police interactions available and useful to the public.\n",
        {"display": "none"},
        {"display": "block"},
    )


@app.callback(
    Output("modal", "is_open"),
    [Input("close", "n_clicks")],
)
def close_disclaimer(n_clicks):
    return False if n_clicks and n_clicks > 0 else True


if __name__ == "__main__":
    Talisman(
        app.server,
        content_security_policy=None,
        # {
        #     "default-src": ["'self'", "google.com"],
        #     "script-src": ["'self'", "'unsafe-eval'"] + app.csp_hashes(),
        #     "style-src": [
        #         "'self'",
        #         "bootstrapcdn.com",
        #         "unsafe-inline",
        #     ],  # ["'self'", "'unsafe-inline'"],
        #     "img-src": ["'self'", "jointhegram.org"],
        # },
    )
    app.run_server()
