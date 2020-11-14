import React from 'react';

import Button from '@material-ui/core/Button';
import CheckCircleIcon from '@material-ui/icons/CheckCircle';
import { DataGrid } from '@material-ui/data-grid';
import Grid from '@material-ui/core/Grid';
import HelpIcon from '@material-ui/icons/Help';
import Paper from '@material-ui/core/Paper';


function App() {
  return (
    <OrderSchedulerUI>

    </OrderSchedulerUI>
  );
}


class OrderSchedulerUI extends React.Component {
  constructor(props) {
    super(props)
    this.state = {
      supply_plans: null,
      sourcing_rules: null,
      orders: null,
      fulfillment_plans: []
    }
    this.tableColumns = [
      {field: "id", headerName: "Index"},
      {field: "customer", headerName: "Customer"},
      {field: "product", headerName: "Product"},
      {field: "order_date", headerName: "Order Date"},
      {field: "site", headerName: "Site"},
      {field: "Fulfillment Date", headerName: "Fulfillment Date"},
      {field: "quantity", headerName: "Quantity"}
    ]
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
    const form_data = new FormData();
    form_data.append("supply_plans", this.state.supply_plans);
    form_data.append("sourcing_rules", this.state.sourcing_rules);
    form_data.append("orders", this.state.orders);
    fetch('/batchfulfillmentplan', {
      method: 'POST',
      body: form_data
    }).then(res => {res.json().then(data => {
      const plans = data.fulfillment_plans.map((value, index, array) => {
        array[index].id = index + 1
        return array[index]
      });
      this.setState({fulfillment_plans: plans})
    })});
  };

  render() {
    return (
      <div>
        <Grid container spacing={4} justify="center">
          <Grid item>
            <FileUploadPanel
              title="Supply Data"
              description="The supply data for the sites. A csv file that contain columns 'site', 'product', 'date', 'quantity'."
              identifier="supply_plans"
              selected_file={this.state.supply_plans}
              onChange={this.handleFileChange}
            ></FileUploadPanel>
          </Grid>
          <Grid item>
            <FileUploadPanel
              title="Sourcing Rule Data"
              description="The sourcing rule data that specifies which customer could get which product from which site. A csv file that contains columns 'site', 'customer', 'product'."
              identifier="sourcing_rules"
              selected_file={this.state.sourcing_rules}
              onChange={this.handleFileChange}
            ></FileUploadPanel>
          </Grid>
          <Grid item>
            <FileUploadPanel
              title="Order Data"
              description="The order data. A csv file that contains 'customer', 'product', 'quantity', 'date'"
              identifier="orders"
              selected_file={this.state.orders}
              onChange={this.handleFileChange}
            ></FileUploadPanel>
          </Grid>
        </Grid>
        <div>
          <Button
            onClick={this.handleResetButtonClicked}
          >
            Reset
          </Button>
          <Button
            color="primary"
            disabled={!this.state.supply_plans || !this.state.sourcing_rules || !this.state.orders}
            onClick={this.handleSubmitButtonClicked}
          >
            Submit
          </Button>
        </div>
        <div style={{ height: 400, width: '100%' }}>
          <DataGrid
            rows={this.state.fulfillment_plans}
            columns={this.tableColumns}
            pageSize={Math.min(10, this.state.fulfillment_plans.length)}
          />
        </div>
        <Button>Download as CSV</Button>
      </div>
    );
  }
}


class FileUploadPanel extends React.Component {
  constructor(props) {
    super(props)
    this.state = {selected_file: null}
  }

  fileSelectedHandler = event => {
    this.props.onChange(this.props.identifier, event.target.files[0]);
  };

  render() {
    return <Grid item>
      <Paper elevation={3}>
          <h2>{this.props.title}</h2>
          <p>{this.props.description}</p>
          <p>{this.props.selected_file ? <CheckCircleIcon/> : <HelpIcon/>}</p>
          <p>{this.props.selected_file ? this.props.selected_file.name : "No file selected"}</p>
          <div>
            <Button>download an example</Button>
            <Button
              color="primary"
              component="label"
            >
              Upload File
              <input hidden type="file" accept=".csv" onChange={this.fileSelectedHandler}/>
            </Button>
          </div>
      </Paper>
    </Grid>
  }
}

export default App;
