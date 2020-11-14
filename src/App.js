import React from 'react';

import Button from '@material-ui/core/Button';
import Card from '@material-ui/core/Card';
import CardActions from '@material-ui/core/CardActions';
import CardContent from '@material-ui/core/CardContent';
import { DataGrid } from '@material-ui/data-grid';
import Grid from '@material-ui/core/Grid';
import LinearProgress from '@material-ui/core/LinearProgress';
import Typography from '@material-ui/core/Typography';


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
      submitting: false,
      fulfillment_plans: []
    }
    this.tableColumns = [
      {field: "id", headerName: "Index", width: 120},
      {field: "customer", headerName: "Customer", width: 120},
      {field: "product", headerName: "Product", width: 120},
      {field: "order_date", headerName: "Order Date", width: 150},
      {field: "site", headerName: "Site", width: 120},
      {field: "fulfillment_date", headerName: "Fulfillment Date", width: 150},
      {field: "quantity", headerName: "Quantity", width: 120}
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
    this.setState({submitting: true});
    const form_data = new FormData();
    form_data.append("supply_plans", this.state.supply_plans);
    form_data.append("sourcing_rules", this.state.sourcing_rules);
    form_data.append("orders", this.state.orders);
    fetch('/batchfulfillmentplan', {
      method: 'POST',
      body: form_data
    }).then(res => {this.setState({submitting: false}); if (res.status === 400) { 
      alert("the uploaded file format is incorrect, please check the templates for reference")
    } else {res.json().then(data => {
      const plans = data.fulfillment_plans.map((value, index, array) => {
        array[index].id = index + 1;
        array[index].order_date = array[index].order_date.split(" ")[0];
        array[index].fulfillment_date = array[index].fulfillment_date.split(" ")[0];
        return array[index];
      });
      this.setState({fulfillment_plans: plans})
    })}});
  };

  handleDownloadCSVButtonClicked = (event) => {
    const csv_titles = '';
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
          {this.state.submitting && <LinearProgress style={{width: 900}}/>}
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
              columns={this.tableColumns}
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


class FileUploadPanel extends React.Component {
  constructor(props) {
    super(props);
  }

  fileSelectedHandler = event => {
    this.props.onChange(this.props.identifier, event.target.files[0]);
    event.target.value = "";
  };

  handleDownloadTemplateClicked = event => {
    download(this.props.identifier + ".csv", this.props.template);
  };

  render() {
    return <Grid item>
      <Card elevation={3} style={{ height: 250, width: 300 }}>
        <CardContent>
          <Typography color="textPrimary" variant="h5" component="h2">
            {this.props.title}
          </Typography>
          <p></p>
          <Typography color="textSecondary" gutterBottom>
            {this.props.description}
          </Typography>
          <Typography color="textSecondary">
            {this.props.selected_file ? this.props.selected_file.name : "No file selected"}
          </Typography>
        </CardContent>
        <CardActions>
          <Button
            onClick={this.handleDownloadTemplateClicked}
          >
            Download Template
          </Button>
          <Button
            color="primary"
            component="label"
          >
            Upload
            <input hidden type="file" accept=".csv" onChange={this.fileSelectedHandler}/>
          </Button>
        </CardActions>
      </Card>
    </Grid>
  }
}

function download(filename, text) {
  // reference https://stackoverflow.com/a/18197341/10068755
  var element = document.createElement('a');
  element.setAttribute('href', 'data:text/plain;charset=utf-8,' + encodeURIComponent(text));
  element.setAttribute('download', filename);

  element.style.display = 'none';
  document.body.appendChild(element);

  element.click();

  document.body.removeChild(element);
}

export default App;
