//--------------------- Npm dependencies -------------------------
//Note: You will need to download these for the applciation to work.
require('dotenv').config()
var express = require('express');
var path = require('path');


//Instance of App
var app = express()

//Pull in the routes
const routes = require('./routes/app.routes');

//Set the view engine to use ejs as a templating language
app.set("view engine", "ejs");
app.set("views", path.join(__dirname, "views"));

//Static assets like JS,CSS, and images
app.use(express.static(__dirname + "/public"));

//set the express app to use routes 
app.use(routes);

//Start the server on the clients IP and port defined above.
app.listen(process.env.frontEndPORT, process.env.frontEndHOST);
console.log('Server started');