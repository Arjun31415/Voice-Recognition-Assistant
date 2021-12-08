ws = new ReconnectingWebSocket("ws://" + location.host + "/zeromq");

ws.onmessage = function (message) {
  console.log("Hii");
  payload = JSON.parse(message.data);
  $("#latest_data").html("<h2> Data: " + message.data + "</h2>");
};
