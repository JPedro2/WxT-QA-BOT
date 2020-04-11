var express = require('express');
var app = express();
var path = require('path');

app.get('/', function(req, res) {
    res.sendFile(path.join(__dirname + '/index.html'));
});


const server = app.listen(8080, () => {
    const host = server.address().address;
    const port = server.address().port;
  
    console.log(`Example app listening at http://${host}:${port}`);
  });