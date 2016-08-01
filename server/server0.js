var http_server = require('http').createServer(handler)
  , sockjs_server = require('sockjs').createServer({sockjs_url: 'http://cdn.jsdelivr.net/sockjs/1.0.1/sockjs.min.js', websocket: false, log: log_all})
  , fs = require('fs')
  , redis = require("redis")

sockjs_server.installHandlers(http_server, {prefix:'/_sockjs'});
http_server.listen(3000);

/**
 * Our redis client which subscribes to channels for updates
 */
redisClient = redis.createClient();

//look for connection errors and log
redisClient.on("error", function (err) {
    console.log("error event - " + redisClient.host + ":" + redisClient.port + " - " + err);
});

/**
 * Dummy redis client which publishes new updates to redis
 */
redisDummyPublishClient = redis.createClient();

function log_all(level, message) {
  console.log(level + " : " + message);
}

/**
 * http handler, currently just sends index.html on new connection
 */
function handler (req, res) {
  fs.readFile(__dirname + '/../www/index0.html',
  function (err, data) {
    if (err) {
      res.writeHead(500);
      return res.end('Error loading index0.html' + __dirname);
    }

    res.writeHead(200);
    res.end(data);
  });
}

/**
 * set socket.io log level to warn
 *
 * uncomment below line to change debug level
 * 0-error, 1-warn, 2-info, 3-debug
 *
 * For more options refer https://github.com/LearnBoost/Socket.IO/wiki/Configuring-Socket.IO
 */
//io.set('log level', 3);

/**
 * socket io client, which listens for new websocket connection
 * and then handles various requests
 */
connections = [];

sockjs_server.on('connection', function (conn) {

  //on connect send a welcome message
  conn.write(JSON.stringify({ text : 'Welcome!' }));

  //on subscription request joins specified room
  //later messages are broadcasted on the rooms
  //conn.on('data', function(data){
  //  connections[data.channel] = [conn];
  //});
  connections.push(conn);
});

/**
 * subscribe to redis channel when client in ready
 */
redisClient.on('ready', function() {
  redisClient.subscribe('notif');
});

/**
 * wait for messages from redis channel, on message
 * send updates on the rooms named after channels.
 *
 * This sends updates to users.
 */
redisClient.on("message", function(channel, message){
    var resp = {'text': message, 'channel':channel}
    connections.forEach(function(conn){
      conn.write(JSON.stringify(resp));
    });
});

/**
 * Simulates publish to redis channels
 * Currently it publishes updates to redis every 5 seconds.
 */
setInterval(function() {
  var no = Math.floor(Math.random() * 100);
  redisDummyPublishClient.publish('notif', 'Generated random no ' + no);
}, 5000);
