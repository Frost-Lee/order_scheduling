import React from 'react'
import { FileUploadPanel } from './file_upload_panel'

import Button from '@material-ui/core/Button';
import { DataGrid } from '@material-ui/data-grid';
import Grid from '@material-ui/core/Grid';
import LinearProgress from '@material-ui/core/LinearProgress';

import { download, format_date } from '../utils/utils'


const tableColumns = [
    { field: "id", headerName: "Index", width: 120 },
    { field: "customer", headerName: "Customer", width: 120 },
    { field: "product", headerName: "Product", width: 120 },
    { field: "order_date", headerName: "Order Date", width: 150 },
    { field: "site", headerName: "Site", width: 120 },
    { field: "fulfillment_date", headerName: "Fulfillment Date", width: 150 },
    { field: "quantity", headerName: "Quantity", width: 120 }
]

export class OrderSchedulerUI extends React.Component {
    constructor(props) {
        super(props)
        this.state = {
            supply_plans: null,
            sourcing_rules: null,
            orders: null,
            submitting: false,
            fulfillment_plans: []
        }
    }

    handleFileChange = (identifier, selected_file) => {
        this.setState({
            [identifier]: selected_file
        });
    };

    handleResetButtonClicked = (event) => {
        this.setState({
            supply_plans: null,
            sourcing_rules: null,
            orders: null
        });
    };

    handleSubmitButtonClicked = (event) => {
        this.setState({ submitting: true });
        const form_data = new FormData();
        form_data.append("supply_plans", this.state.supply_plans);
        form_data.append("sourcing_rules", this.state.sourcing_rules);
        form_data.append("orders", this.state.orders);
        fetch('/batchfulfillmentplan', {
            method: 'POST',
            body: form_data
        }).then(res => {
            this.setState({ submitting: false }); if (res.status !== 200) {
                alert("the uploaded file format is incorrect, please check the templates for reference")
            } else {
                res.json().then(data => {
                    const plans = data.fulfillment_plans.map((value, index, array) => {
                        array[index].id = index + 1;
                        array[index].order_date = array[index].order_date.split(" ")[0];
                        array[index].fulfillment_date = array[index].fulfillment_date.split(" ")[0];
                        return array[index];
                    });
                    this.setState({ fulfillment_plans: plans })
                })
            }
        });
    };

    handleDownloadCSVButtonClicked = (event) => {
        const fulfillment_dates = this.state.fulfillment_plans.map((value) => { return new Date(value.fulfillment_date) });
        fulfillment_dates.sort((a, b) => a - b);
        const start_date = fulfillment_dates[0];
        const end_date = fulfillment_dates.slice(-1)[0];
        const row_dict = {};
        for (const plan of this.state.fulfillment_plans) {
            const key = [plan.site, plan.customer, plan.product].join(',');
            if (key in row_dict) {
                row_dict[key].push(plan);
            } else {
                row_dict[key] = [plan];
            }
        }
        const column_dates = [];
        for (var date = start_date; date <= end_date; date.setDate(date.getDate() + 1)) {
            column_dates.push(new Date(date));
        }
        console.log(column_dates);
        const csv_content_rows = [];
        for (const row_key of Object.keys(row_dict)) {
            console.log(row_key);
            const plans = row_dict[row_key];
            console.log(plans);
            const fulfillment_quantities = [];
            for (const d of column_dates) {
                const sum_reducer = (accumulated, current) => accumulated + current;
                fulfillment_quantities.push(plans.filter(plan => (new Date(plan.fulfillment_date)).getTime() === d.getTime()).map(plan => plan.quantity).reduce(sum_reducer, 0));
            }
            csv_content_rows.push(row_key + "," + fulfillment_quantities.join(","));
        }
        const csv_title_row = ["site,customer,product", column_dates.map(date => format_date(date)).join(",")].join(",");
        download("fulfillment_plan.csv", [csv_title_row, csv_content_rows.join("\n")].join("\n"));
    };

    render() {
        return (
            <div>
                <p></p>
                <Grid container spacing={4} justify="center">
                    <Grid item>
                        <FileUploadPanel
                            title="Supply Data"
                            description="The supply data that specifies which site which site produces which product for how many on which day."
                            template={["site,product,date,quantity", "1206,P001,1-Jul-19,2000"].join("\n")}
                            identifier="supply_plans"
                            selected_file={this.state.supply_plans}
                            onChange={this.handleFileChange}
                        ></FileUploadPanel>
                    </Grid>
                    <Grid item>
                        <FileUploadPanel
                            title="Sourcing Rule Data"
                            description="The sourcing rule data that specifies which customer could get which product from which site."
                            template={["site,customer,product", "1206,C001,P001"].join("\n")}
                            identifier="sourcing_rules"
                            selected_file={this.state.sourcing_rules}
                            onChange={this.handleFileChange}
                        ></FileUploadPanel>
                    </Grid>
                    <Grid item>
                        <FileUploadPanel
                            title="Order Data"
                            description="The order data that specifies which customer ordered which product for how many on which day."
                            template={["site,product,date,quantity", "1206,P001,1-Jul-19,2000"].join("\n")}
                            identifier="orders"
                            selected_file={this.state.orders}
                            onChange={this.handleFileChange}
                        ></FileUploadPanel>
                    </Grid>
                </Grid>
                <p></p>
                <Grid container justify="center">
                    <Button
                        disabled={!this.state.supply_plans && !this.state.sourcing_rules && !this.state.orders}
                        onClick={this.handleResetButtonClicked}
                    >
                        Reset
            </Button>
                    <Button
                        color="primary"
                        disabled={!this.state.supply_plans || !this.state.sourcing_rules || !this.state.orders || this.state.submitting}
                        onClick={this.handleSubmitButtonClicked}
                    >
                        Submit
            </Button>
                </Grid>
                <p></p>
                <Grid container justify="center">
                    {this.state.submitting && <LinearProgress style={{ width: 900 }} />}
                </Grid>
                <p></p>
                {this.state.fulfillment_plans.length > 0 && <Grid container justify="center">
                    <Button
                        color="primary"
                        disabled={this.state.fulfillment_plans.length <= 0}
                        onClick={this.handleDownloadCSVButtonClicked}
                    >
                        Download CSV Result
            </Button>
                </Grid>}
                <p></p>
                <Grid container justify="center">
                    <div style={{ width: 900 }}>
                        {this.state.fulfillment_plans.length > 0 && <DataGrid
                            rows={this.state.fulfillment_plans}
                            columns={tableColumns}
                            pageSize={Math.min(10, this.state.fulfillment_plans.length)}
                            autoHeight={true}
                            disableSelectionOnClick={true}
                        />}
                    </div>
                </Grid>
                <p></p>
            </div>
        );
    }
}
