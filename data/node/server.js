var http = require("http");
var fs = require('fs');
var port_number = 8000;

for (var i = 0; i < process.argv.length; i++) {
    if (process.argv[i].indexOf('--port=') === 0) {
        port_number = process.argv[i].substring('--port='.length);
    }
}

function getType(_url) {
    var types = {
        ".html": "text/html",
        ".css": "text/css",
        ".js": "text/javascript",
        ".png": "image/png",
        ".gif": "image/gif",
        ".svg": "svg+xml"
    }
    for (var key in types) {
        if (_url.endsWith(key)) {
            return types[key];
        }
    }
    return "text/plain";
}

var server = http.createServer(function (req, res) {
    var url = "public" + (req.url.endsWith("/") ? req.url + "index.html" : req.url);
    if (fs.existsSync(url)) {
        fs.readFile(url, (err, data) => {
            if (!err) {
                res.writeHead(200, { "Content-Type": getType(url) });
                res.end(data);
            } else {
                res.statusCode = 500;
                res.end();
            }
        });
    } else {
        res.statusCode = 404;
        res.end();
    }
});

var port = process.env.PORT || port_number;
server.listen(port, function () {
    console.log("Open this link in your browser: http://localhost:" + port);
});
