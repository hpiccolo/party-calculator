import dash
from dash import Dash, dash_table, dcc, html
from dash.dependencies import Input, Output, State
import pandas as pd

app = Dash(__name__)
dropdown_people = ['sim', 'não']
columns_people = [['Nome', 'input'], ['Comida', 'dropdown', dropdown_people],
                  ['Bebida', 'dropdown', dropdown_people]]
stn_people_begin = ['', 'sim', 'sim']
stn_spent_begin = ['', '', 'Comida', '']
dropdown_spent_names = ['']
dropdown_spent_names_food = ['Comida', 'Bebida']
columns_spent = [['Nome', 'dropdown', dropdown_spent_names], ['Valor', 'input'],
                 ['Comida/Bebida', 'dropdown', dropdown_spent_names_food],
                 ['Descrição', 'input']]
dicttf = {'sim': 1, 'não': 0}


def make_dropdown(values):
    pivot = {'options': [
        {'label': i, 'value': i}
        for i in values
    ]}
    return pivot


def make_list(values, index):
    pivot = []
    for item in values:
        pivot.append(item[index])
    return pivot


def make_table(table_id, columns, stn_begin):
    data_to_table = {}
    for i in range(len(columns)):
        data_to_table[columns[i][0]] = stn_begin[i]
    data_to_table = [data_to_table]
    columns_table = [{"name": i[0], "id": i[0], 'presentation': i[1]} for i in columns]
    dropdown_table = {}
    for item in columns:
        if item[1] == "dropdown":
            dropdown_table[item[0]] = make_dropdown(item[2])
    table_return = dash_table.DataTable(
        id=table_id,
        data=data_to_table,
        columns=columns_table,
        editable=True,
        dropdown=dropdown_table,
        row_deletable=True
    )
    return table_return


app.layout = html.Div([
    html.H1('Calculadora do role', style={
        'textAlign': 'center'}
            ),
    html.Div(
        children=html.Div([
            html.H3('Coloque as pessoas que estão no role'),
        ])
    ),
    make_table('people', columns_people, stn_people_begin),
    html.Div(id='people-table-dropdown-container'),
    html.Div(
        children=html.Div([
            html.H3('Coloque os gastos do role'),
        ])
    ),
    make_table('spent', columns_spent, stn_spent_begin),
    html.Div(id='spent-table-dropdown-container'),
    html.Button('Calcular', id='calculate-button', n_clicks=0),
    html.Br(),
    html.Div(id='output'),
    html.Br(),
    html.Div(id='output2'),
    html.Br(),
    html.Div(id='output3'),
])


@app.callback(
    Output('output', component_property='children'),
    Input('calculate-button', 'n_clicks'),
    Input('people', 'data'),
    Input('spent', 'data')
)
def calculate(n_clicks, people, spent):
    output = ""
    if n_clicks > 0:
        peopledf = pd.DataFrame(people)
        if peopledf.at[len(peopledf) - 1, columns_spent[0][0]] == stn_people_begin[0]:
            peopledf = peopledf.drop(len(peopledf) - 1)
        spentdf = pd.DataFrame(spent)
        spentdf[columns_spent[1][0]] = spentdf[columns_spent[1][0]].apply(lambda x: int(x) if x.isdigit() else 0)
        people_pay_food = sum(peopledf[columns_people[1][0]] == dropdown_people[0])
        people_pay_drink = sum(peopledf[columns_people[2][0]] == dropdown_people[0])
        food_df = spentdf[spentdf[columns_spent[2][0]] == dropdown_spent_names_food[0]]
        drink_df = spentdf[spentdf[columns_spent[2][0]] == dropdown_spent_names_food[1]]
        total_amount_food = food_df[columns_spent[1][0]].sum()
        total_amount_drink = drink_df[columns_spent[1][0]].sum()
        per_people_food = total_amount_food / people_pay_food
        per_people_drink = total_amount_drink / people_pay_drink
        peopledf = peopledf.set_index(columns_people[0][0])
        dicttf = {'sim': 1, 'não': 0}
        peopledf[columns_people[1][0]] = peopledf[columns_people[1][0]].map(dicttf)
        peopledf[columns_people[2][0]] = peopledf[columns_people[2][0]].map(dicttf)
        peopledf['Paid'] = spentdf.groupby(columns_spent[0][0]).sum()
        peopledf['Pay'] = peopledf[columns_people[1][0]] * per_people_food + peopledf[
            columns_people[2][0]] * per_people_drink
        peopledf = peopledf.fillna(0)
        peopledf['Balance'] = peopledf['Paid'] - peopledf['Pay']
        peopledf['Final Balance'] = peopledf['Balance']
        peopledf['Resume'] = peopledf.index
        in_debit = peopledf[peopledf['Balance'] < 0].reset_index()
        in_credit = peopledf[peopledf['Balance'] > 0].reset_index()
        resume_mensage = " paga {value:.2f} para {creditor:}"
        creditor = 0
        debitor = 0
        while creditor < len(in_credit):
            if in_debit.at[debitor, 'Final Balance'] + in_credit.at[creditor, 'Final Balance'] > 0.01:
                if in_debit.at[debitor, 'Balance'] != in_debit.at[debitor, 'Final Balance']:
                    in_debit.at[debitor, 'Resume'] += " e "
                to_pay = -in_debit.at[debitor, 'Final Balance']
                in_debit.at[debitor, 'Final Balance'] += to_pay
                in_credit.at[creditor, 'Final Balance'] += -to_pay
                in_debit.at[debitor, 'Resume'] += resume_mensage.format(value=to_pay,
                                                                        creditor=in_credit.at[
                                                                            creditor, columns_spent[0][0]])
                debitor += 1
                if in_credit.loc[creditor, 'Final Balance'] == 0:
                    creditor += 1
            else:
                to_pay = in_credit.at[creditor, 'Final Balance']
                in_debit.at[debitor, 'Final Balance'] += to_pay
                in_credit.at[creditor, 'Final Balance'] += -to_pay
                in_debit.at[debitor, 'Resume'] += resume_mensage.format(value=to_pay,
                                                                        creditor=in_credit.at[
                                                                            creditor, columns_spent[0][0]])
                if creditor + 1 < len(in_credit) and in_debit.at[
                    debitor, 'Final Balance'] - in_credit.at[creditor, 'Final Balance'] > 0.01:
                    in_debit.at[debitor, 'Resume'] += ", "
                creditor += 1
        output = str(in_debit["Resume"].values)
    return output


@app.callback(
    Output('people', 'data'),
    # Output('output2', component_property='children'),
    Input('people', 'active_cell'),
    Input('people', 'data'),
    State('people', 'data'),
    State('people', 'columns')
)
def update_people_rows(active_cell, data, rows, columns):
    if type(active_cell) == dict:
        if data[-1][columns_people[0][0]] != stn_people_begin[0]:
            rows.append({columns[c]['id']: stn_people_begin[c] for c in range(len(columns))})
    return rows  # , f'Output: {data}'


@app.callback(
    Output('spent', 'data'),
    # Output('output3', component_property='children'),
    Input('spent', 'active_cell'),
    Input('spent', 'data'),
    State('spent', 'data'),
    State('spent', 'columns')
)
def update_spent_rows(active_cell, data, rows, columns):
    if type(active_cell) == dict:
        if data[-1][columns_spent[1][0]] != stn_spent_begin[1]:
            stn_spent_begin[0] = data[-1][columns_spent[0][0]]
            rows.append({columns[c]['id']: stn_spent_begin[c] for c in range(len(columns))})
    return rows  # , f'Output: {data}'


@app.callback(
    Output('spent', 'dropdown'),
    State('spent', 'dropdown'),
    Input('people', 'data'),
)
def spent_dropdown_update(dropdown, data):
    names = []
    for item in data:
        if item[columns_spent[0][0]] is not None:
            names.append(item[columns_spent[0][0]])
            dropdown[columns_spent[0][0]] = make_dropdown(names)
    return dropdown


if __name__ == '__main__':
    app.run_server(debug=True)
