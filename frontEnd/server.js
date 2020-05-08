var express = require('express');
var app = express();
var path = require('path');

app.use(express.static(__dirname + "/public"));

app.get('/', function(req, res) {
    res.sendFile(path.join(__dirname + '/login.html'));
});
app.get('/main.html', function(req, res) {
    res.sendFile(path.join(__dirname + '/main.html'));
});
app.get('/query.html', function(req, res) {
    res.sendFile(path.join(__dirname + '/query.html'));
});
app.get('/update.html', function(req, res) {
    res.sendFile(path.join(__dirname + '/update.html'));
});

app.listen(8080, '0.0.0.0');
console.log('Server started');