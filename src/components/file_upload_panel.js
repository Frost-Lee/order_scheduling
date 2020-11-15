import React from 'react'

import Button from '@material-ui/core/Button';
import Card from '@material-ui/core/Card';
import CardActions from '@material-ui/core/CardActions';
import CardContent from '@material-ui/core/CardContent';
import Grid from '@material-ui/core/Grid';
import Typography from '@material-ui/core/Typography';

import { download } from '../utils/utils'


export class FileUploadPanel extends React.Component {

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
                    <input hidden type="file" accept=".csv" onChange={this.fileSelectedHandler} />
                    </Button>
                </CardActions>
            </Card>
        </Grid>
    }
}
