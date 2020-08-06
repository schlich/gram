from django.shortcuts import render
import os
import dash
import json
import dash_core_components as dcc
import dash_html_components as html
import dash_table
import pandas as pd
import pygsheets as pyg
import plotly.graph_objs as go
from dash.exceptions import PreventUpdate
from dash.dependencies import Input, Output, State


external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash('PoliceData', external_stylesheets=external_stylesheets)


client = pyg.authorize(service_account_env_var = 'GOOGLE_SHEETS_CREDS_JSON')

officers = client.open("cleaned_police_data").worksheet('title','officers')
complaints = client.open("cleaned_police_data").worksheet('title','complaints')
rawdata = complaints.get_all_values()
headers = rawdata.pop(0)
data = pd.DataFrame(rawdata, columns=headers)

race_counts = data['Race of Complainant'].value_counts()
officers = data['Officer Name'].unique()
display_data = data[['Officer Name', 'DSN #', 'Rank','Assignment','Date of Incident','Location of Incident', 'Nature of Complaint',"Complainant's Statement",'Age',"Race of Complainant","Complainant Gender"]]
column_names = ['Date of Incident','Nature of Complaint','Age','Race of Complainant','Complainant Gender']

app.layout = html.Div([
    html.H2('St Louis Police Complaints'),
	html.H5('Search for/select an officer'),
	html.Datalist(id='officers', children = [html.Option(value=i) for i in officers]),
	dcc.Input(id='officer_input', list='officers'),
	html.Button('Search',id='submit'),
	html.Div([
		html.Div([
			html.H3('Officer Name', id='officer_name'),
			html.H5('DSN: ', id='dsn'),
			html.P('Rank: ', id='rank'),
			html.P('Assignment: ', id='assignment'),
		]),
		html.Div([
			dash_table.DataTable(
				id='complaints',
				columns=[{"name": i, "id": i, 'selectable': True} for i in column_names],
				data=pd.DataFrame().to_dict('records'),
				# hidden_columns=['Officer Name'],
				row_selectable='single',
				style_data={
					'whiteSpace': 'normal',
					'height': 'auto'
				},
			),
			html.H3("Complainant's Statement:"),
			html.P("Search for an officer and select a row to view the complainant's statement",id='statement')
		])
	], id='data_html', style= {'display': 'none'}),
	# html.H3('Citizen Complaint Summary Statistics-'),
	# dcc.Graph(
	# 	figure=go.Figure(
	# 		data=go.Pie(
	# 			labels=race_counts.index.tolist(),
	# 			values=race_counts.values.tolist(),
	# 			textinfo='label+value'
	# 		)
	# 	)
	# )

])

@app.callback(
	[Output('complaints', 'data'),
	Output('data_html','style'),
	Output('officer_name','children'),
	Output('dsn','children'),
	Output('rank','children'),
	Output('assignment','children')],
	[Input('submit', 'n_clicks')],
    [State('officer_input', 'value')]
)
def update_data(n_clicks,officer):
	if n_clicks:
		complaints = display_data[display_data['Officer Name']==officer].to_dict('records')
		firstrow = complaints[0]
		dsn = 'DSN: ' + firstrow['DSN #']
		rank = 'Rank: ' + firstrow['Rank']
		assignment = 'Assignment: ' + firstrow['Assignment']
		return complaints, {'display':'block'}, officer, dsn, rank, assignment
	else:
		raise PreventUpdate

@app.callback(
	dash.dependencies.Output('statement','children'),
     [dash.dependencies.Input('complaints', "derived_virtual_data"),
	 dash.dependencies.Input('complaints', "derived_virtual_selected_rows")],
)
def get_statement(rows, derived_virtual_selected_rows):
	if not derived_virtual_selected_rows:
		statement = "Select a row to view the complainant's statement"
	else:
		data =  pd.DataFrame(rows)
		statement = data.loc[derived_virtual_selected_rows[0],"Complainant's Statement"]

	return statement

if __name__ == '__main__':
    app.run_server(debug=True)