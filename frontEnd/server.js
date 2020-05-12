var express = require('express');
var app = express();
var path = require('path');

app.use(express.static(__dirname + "/public"));

app.get('/', function(req, res) {
    res.sendFile(path.join(__dirname + '/html/login.html'));
});
app.get('/main.html', function(req, res) {
    res.sendFile(path.join(__dirname + '/html/main.html'));
});
app.get('/query.html', function(req, res) {
    res.sendFile(path.join(__dirname + '/html/query.html'));
});
app.get('/update.html', function(req, res) {
    res.sendFile(path.join(__dirname + '/html/update.html'));
});
app.get('/login.html', function(req, res){
    res.sendFile(path.join(__dirname + '/html/login.html'));
})

app.listen(3006, '0.0.0.0');
console.log('Server started');