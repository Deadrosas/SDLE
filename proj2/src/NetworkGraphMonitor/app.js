// app.js
import express from 'express';
import WebSocket from 'ws';
import http from 'http';
import path from 'path';
import { WebSocketServer } from 'ws'

// Create Express app
const app = express();
const port = 3000;
const server = http.createServer(app);
// const wss = new WebSocket.Server({ server });
const wss = new WebSocketServer({ server });

wss.on('connection', (ws) => {
    console.log('Establish websocket connection');
  });

app.get('/', (req, res) => {

  res.sendFile(path.join(path.resolve(), '/index.html'));

});

app.post('/draw/:nodes/:edges', (req, res) => {
    wss.clients.forEach((client) => {
      if (client.readyState === WebSocket.OPEN) {
        client.send(`draw:${req.params.nodes}:${req.params.edges}`);
      }
    });
    res.sendStatus(200);
});

app.post('/clear/', (req, res) => {
  wss.clients.forEach((client) => {
    if (client.readyState === WebSocket.OPEN) {
      client.send(`clear`);
    }
  });
  res.sendStatus(200);
});

app.post('/addNode/:node', (req, res) => {
  wss.clients.forEach((client) => {
    if (client.readyState === WebSocket.OPEN) {
      client.send(`addNode:${req.params.node}`);
    }
  });
  res.sendStatus(200);
});

app.post('/addEdge/:edge', (req, res) => {
  wss.clients.forEach((client) => {
    if (client.readyState === WebSocket.OPEN) {
      client.send(`addEdge:${req.params.edge}`);
    }
  });
  res.sendStatus(200);
});

// Start the Express server
server.listen(port, () => console.log(`http server is listening on http://localhost:${port}`));