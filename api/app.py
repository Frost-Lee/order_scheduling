import flask
import json
import numpy as np
import pandas as pd
import time

from scheduler.order_scheduler import OrderScheduler

app = flask.Flask(__name__)

@app.route('/batchfulfillmentplan', methods=['GET', 'POST'])
def get_batch_fulfillment_plan():
    time.sleep(1)
    files = flask.request.files
    if 'orders' not in files or 'sourcing_rules' not in files or 'supply_plans' not in files:
        flask.abort(400, 'Unexpected file attachments.')
    try:
        response = _prepare_batch_fulfillment_plan_response(
            order_df=pd.read_csv(files['orders']),
            sourcing_rule_df=pd.read_csv(files['sourcing_rules']),
            supply_plan_df=pd.read_csv(files['supply_plans'])
        )
        return response
    except AssertionError:
        flask.abort(400, 'Unexpected file format')

def _prepare_batch_fulfillment_plan_response(order_df, sourcing_rule_df, supply_plan_df):
    df_legal = lambda df, titles: set([*df.columns]) == set(titles)  and len(np.where(pd.isnull(df))[0]) == 0
    assert df_legal(order_df, ['customer', 'product', 'date', 'quantity']) and df_legal(sourcing_rule_df, ['site', 'product', 'customer']) and df_legal(supply_plan_df, ['site', 'product', 'date', 'quantity'])
    order_df['date'], supply_plan_df['date'] = pd.to_datetime(order_df['date']), pd.to_datetime(supply_plan_df['date'])
    order_df, supply_plan_df = order_df.sort_values(by=['date']), supply_plan_df.sort_values(by=['date'])
    order_scheduler = OrderScheduler()
    for _, row in sourcing_rule_df.iterrows():
        order_scheduler.add_sourcing_rule(row['customer'], row['site'], row['product'])
    fulfillment_plans = []
    for date in sorted(set(order_df['date']).union(set(supply_plan_df['date']))):
        order_daily_df, supply_daily_df = order_df[order_df['date'] == date] , supply_plan_df[supply_plan_df['date'] == date]
        for _, row in order_daily_df.iterrows():
            order_scheduler.claim_order(row['customer'], row['product'], row['quantity'], row['date'])
        for _, row in supply_daily_df.iterrows():
            order_scheduler.claim_supply_plan(row['site'], row['product'], row['quantity'], row['date'])
        fulfillment_plans += order_scheduler.plan_fulfillment(date)
    return json.dumps({'fulfillment_plans': [{
        'customer': plan[0],
        'product': plan[1],
        'order_date': plan[2],
        'site': plan[3],
        'fulfillment_date': plan[4],
        'quantity': plan[5]
    } for plan in fulfillment_plans]}, indent=4, sort_keys=True, default=str)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
