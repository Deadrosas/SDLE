# NetworkGraphMonitor
## A simple http graph visualization tool

### Before running
  ```
    npm install
    npm install express
  ```
  
### Start server
  ```
    node app.js
  ```
  
### Using
  - GET localhost:3000 to see the graph monitor

  - POST localhost:3000/draw/{nodes}/{edges}
  
        Draws a graph with the given data in the monitor
        nodes is an array of integers ex. [1,2,3]
        edges is an array of arrays of two integers ex. [[1,2], [2,3]]
 
  - POST localhost:3000/clear
  
        Clears the graph monitor
      
  - POST localhost:3000/addNode/{node}
   
        Adds a node to the graph
        node is an integer ex. 1
      
  - POST localhost:3000/addEdge/{edge}

        Adds an adge to the graph
        edge is an array with two integers ex. [1,2]
