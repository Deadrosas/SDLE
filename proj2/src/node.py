import asyncio
from kademlia.network import Server
import logging

class Node:
    def __init__(self, id, listening_port, bootstrap_port,  address = "127.0.0.1"):
        self.server = Server()
        self.id = id
        self.listening_port = int(listening_port)
        self.bootstrap_port = int(bootstrap_port)
        self.address = address


        log = logging.getLogger('kademlia')
        log.setLevel(logging.DEBUG)
        log.addHandler(logging.StreamHandler())

        # print(result)
    

    async def connect(self):
        await self.server.listen(self.listening_port)

        # Bootstrap the node by connecting to other known nodes, in this case
        # replace 123.123.123.123 with the IP of another node and optionally
        # give as many ip/port combos as you can for other nodes.
        await self.server.bootstrap([(self.address, self.bootstrap_port)])
        


        # set a value for the key "my-key" on the network
        await self.server.set("{}".format(self.id), "{}:{}".format(self.address, self.listening_port))


        # get the value associated with "my-key" from the network
        # result = await self.server.get("my-key")

    
