from logging import exception
from time import sleep
import zmq
import random
import sys
import threading
import os
import requests
import pickle

from zmq.error import ZMQError

from post import Post
from node import *

###CONSTS
POSTS = "POSTS"
FOLLOWS = "FOLLOWS"
ARE_YOU_ALIVE = "ARE_YOU_ALIVE"
YES_IM_ALIVE = "YES_IM_ALIVE"
GET_POSTS_STR = "GET_POSTS"
GET_POSTS = lambda user: GET_POSTS_STR+" "+user
##/CONSTS

database = {}


# set up logging 

machine_public_ip = requests.get('https://api.ipify.org').content.decode('utf8')
# print('My public IP address is: {}'.format(machine_ip))

my_id = str(random.randint(3001, 5000))

connect_to_port = 8468
if len(sys.argv) > 1:
    connect_to_port =  sys.argv[1]

address = "127.0.0.1"


def saveDatabase(id):
    with open(".%sdata"%(id), 'wb') as file:
        pickle.dump(database,file)

async def connect_to_network_kademlia():
    node = Node(my_id, my_id, connect_to_port, address)
    await node.connect()

    return node


class Switcher(object):
    def execute_command(self, command, node):
        method_name = str(command).partition(' ')[0].lower()

        # print(method_name)

        # create the method object and create a lambda function for when invalid commands are sent to the server
        method = getattr(self, method_name)
        return method(node )

    async def follow(self, node):
        global database
        peer_id = input("Insert the id of the peer you would like to start following: ")
        content = await node.server.get(peer_id)
        print("CONTENT: {}".format(content))
        if(content):
            await node.server.set(peer_id, content + '|' + address + ":" + my_id)
            if FOLLOWS in database:
                database[FOLLOWS].append(peer_id)
            else:
                database[FOLLOWS] = [peer_id]
            
            socket = getSocketThatKnowsTimeline(content.split("|"))
            if not socket == None:
                socket.send(GET_POSTS(peer_id).encode())
                bin_posts = socket.recv()
                posts = pickle.loads(bin_posts)
                if POSTS in database:
                        database[POSTS][peer_id] = posts
                else:
                    database[POSTS] = {}
                    database[POSTS][peer_id] = posts
        else:
            print("Given user does not exist")
        saveDatabase(node.id)
        return

    async def get(self, node):
        peer_id = int(input("Insert the id of the peer you would like to see: "))
        print(await node.server.get(peer_id))
        return
    
    async def post(self, node):
        global database
        post_content = input("Insert the post content:")
        my_post = Post(my_id, post_content)
        if POSTS in database:
            if my_id in database[POSTS]:
                database[POSTS][my_id].append(my_post)
            else:
                database[POSTS][my_id] = [my_post]
        else:
            database[POSTS] = {}
            database[POSTS][my_id] = [my_post]
        my_post.setID(len(database[POSTS][my_id]))
        
        saveDatabase(node.id)
        return
    
    async def pdatabase(self, node):
        if FOLLOWS in database:
            print("Follows:")
            for follow in database[FOLLOWS]:
                print("\t @"+follow)
            print()
        else:
            print("No follows")
        if POSTS in database:
            print("Posts:")
            for user in database[POSTS]:
                print("\t@"+user)
                for post_ in database[POSTS][user]:
                    print(str(post_))
        else:
            print("No posts")
        return


    async def timeline(self,node):
        timeline = []
        if not FOLLOWS in database:
            print("Follow someone to fetch")
            return
        for follow in database[FOLLOWS]:
            follow_followers = await getFollowers(node,follow)
            socket = getSocketThatKnowsTimeline(follow_followers)
            if socket == None:
                print("Impossible to retreive information")
            else:
                #Retreive timeline
                socket.send(GET_POSTS(follow).encode())
                bin_posts = socket.recv()
                posts = pickle.loads(bin_posts)
                timeline += posts
                socket.close()
        
        print(timeline)
        if(len(timeline) > 0):
            for post in sorted(timeline, key= lambda post: post.timestamp):
                print(str(post))
        else:
            print("No posts were found")
        return
        


# Create the Switcher object
switcher = Switcher()

def sendSocketResponse(socket, senderID, message, encoded = True):
    print("Sent"+str(message))
    socket.send(senderID.encode(), zmq.SNDMORE)
    socket.send(message.encode() if encoded else message)

def processSocketMessage(senderID, message, socket):
    print("RECEIVED MESSAGE : %s"%(message))
    if message == ARE_YOU_ALIVE:
        sendSocketResponse(socket, senderID, YES_IM_ALIVE)
    
    if GET_POSTS_STR in message:
        command, user = message.split(" ") 
        if POSTS in database:
            if user in database[POSTS]:
                sendSocketResponse(socket, senderID, pickle.dumps(database[POSTS][user]), encoded=False)
            else:
                sendSocketResponse(socket, senderID, pickle.dumps([]), encoded=False)
        else:
            sendSocketResponse(socket, senderID, pickle.dumps([]), encoded=False)


def incoming_messages():
    context = zmq.Context()

    socket = context.socket(zmq.ROUTER)
    socket.bind("tcp://*:{}".format(my_id))

    poller = zmq.Poller()
    poller.register(socket, zmq.POLLIN)

    senderID = -1

    while True:
        if(poller.poll()):
            msg = socket.recv(zmq.NOBLOCK).decode()
            if(senderID == -1):
                senderID = msg
            else:
                processSocketMessage(senderID, msg, socket)
                senderID = -1

            # socket.send(id_peer, zmq.SNDMORE)
            # socket.send(msg.encode())

async def getFollowers(node, peer_id):
    for i in range(10):
        content = await node.server.get(peer_id)
        if not content == None:
            break
        sleep(0.01)
    return content.split("|")

def getSocketThatKnowsTimeline(followers):
    for follower in followers:
        if follower.split(":")[1] == my_id:
            continue
        context = zmq.Context()
        socket = context.socket(zmq.DEALER)
        socket.setsockopt_string(zmq.IDENTITY, my_id)
        
        #Try to connect...
        socket.connect("tcp://%s"%(follower))
        
        socket.send(ARE_YOU_ALIVE.encode())

        socket.setsockopt(zmq.RCVTIMEO, 1000) 
        socket.setsockopt(zmq.LINGER, 0)
        
        response = socket.recv()

        try:
            response.decode()
            return socket
        except:
            socket.close()
           

    return None

async def pollTimeline(node):
    while True:
        if(not FOLLOWS in database):
            continue
        print(database[FOLLOWS])
        for follow in database[FOLLOWS]:
            follow_followers = await getFollowers(node,follow)
            socket = getSocketThatKnowsTimeline(follow_followers)
            if socket == None:
                ##Impossible to retreive information, no follower is online
                continue

def pollTimelineLauncher(args):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    loop.run_until_complete(pollTimeline(args))
    loop.close()

async def main_loop(node):
    print("Connected as %s"%(node.id))
    while True:
        print(":")
        inp = input()
        try:
            await switcher.execute_command(inp, node)
        #except Exception as ex:
        #    print(ex)
        except AttributeError:
            print("Command '{}' not found".format(inp))
        # await node.server.set(peer_id, await node.server.get(peer_id) + inp)
        # print(await node.server.get(peer_id))
        

async def start_peer():
    global database
    node = await connect_to_network_kademlia()
    temp = await node.server.get(my_id)

    if(os.path.isfile(".%sdata"%(node.id))):
        with open(".%sdata"%(node.id), 'rb') as file:
            database = pickle.load(file)

    if (temp != None):
        recv_thread = threading.Thread(target=incoming_messages)
        recv_thread.start()

        #timeline_thread = threading.Thread(target=pollTimelineLauncher, args=(node,))
        #timeline_thread.start()

        
        await main_loop(node)
    
    node.server.stop()


def start_first_peer():
    os.system("rm -rr __pycache__")
    node = Server()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.set_debug(True)
    loop.run_until_complete(node.listen(connect_to_port))

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        node.stop()
        loop.close()

asyncio.run(start_peer())

start_first_peer()

