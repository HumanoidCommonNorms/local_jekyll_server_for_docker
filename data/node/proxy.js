var httpProxy = require('http-proxy');
var fs = require('fs');
var port_number = 8000;

for (var i = 0; i < process.argv.length; i++) {
    if (process.argv[i].indexOf('--port=') === 0) {
        port_number = process.argv[i].substring('--port='.length);
    }
}

var options = {
    hostnameOnly: true,
    router: {
        'test.local': '127.0.0.1:4000'
    }
}

httpProxy.createServer(options).listen(port_number);

console.log("proxy server: http://localhost:" + port_number);
