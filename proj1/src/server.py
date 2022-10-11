import zmq
import asyncio
import os
import signal
import json
import sys


# peers will have to connect to the server in order to get messages published on a certain topic
# peers will have an unique ID so that the server can keep track of each peer individually

# Global variables used throughout the program
pub_port = "5556"
sub_port = "5557"

pub_id = "" # keeps track of which publisher is sending messages
sub_id = "" # keeps track of which subscriber is sending messages

total_message_line = 0

pub_list = []
sub_dict = {}

program_files_dir = "program_files/"

if len(sys.argv) > 1:
    pub_port =  sys.argv[1]
    int(pub_port)

if len(sys.argv) > 2:
    sub_port =  sys.argv[2]
    int(sub_port)

# create pub and sub sockets

context = zmq.Context()

# pub socket is used to communicate with publishers
pub_socket = context.socket(zmq.ROUTER)
pub_socket.bind("tcp://*:{}".format(pub_port))

# sub socket is used to communicate with subscribers

sub_socket = context.socket(zmq.ROUTER)
sub_socket.bind("tcp://*:{}".format(sub_port))


class Error(Exception):
    # Base class for exceptions in this module.
    pass

class NoTopicsSubscribed(Error):
    # Exception raised when there are no topics subscribed.

    # Attributes:
    #     expression -- input expression in which the error occurred
    #     message -- explanation of the error

    def __init__(self, message):
        self.message = message

class TopicNotSubscribed(Error):
    # Exception raised when a topic is not subscribed.

    # Attributes:
    #     expression -- input expression in which the error occurred
    #     message -- explanation of the error
    #
    def __init__(self, message):
        self.message = message

# a class that serves as a switch statement
class Switcher(object):
    def execute_command(self, command, sub_id, topic = None):
        method_name = str(command)

        # print(method_name)

        # create the method object and create a lambda function for when invalid commands are sent to the server
        method = getattr(self, method_name, lambda sub_id, topic: print("Invalid command"))
        return method(sub_id, topic)

    async def subscribe(self, sub_id, topic):

        # the file keeps the id of the subscriber and what topics he subscribes in the following format -> ID_1,TOPIC_1,TOPIC_2:ID_2,TOPIC_1,TOPIC_3

        # check if the file exists and if it does open it
        if os.path.exists(program_files_dir + "subscriber_info.json"):

            file = open(program_files_dir + "subscriber_info.json", "r+")
            # sub_info = file.read()
            try:
                sub_info = json.load(file)
            except:
                sub_info = {}
            file.seek(0)

            if(sub_id in sub_info):
                if(topic not in sub_info[sub_id]):
                    sub_info[sub_id][topic] = total_message_line
                    sub_socket.send(sub_id.encode(),zmq.SNDMORE)
                    sub_socket.send("You are now subscribed to the topic: {}".format(topic.upper()).encode())
                else:
                    sub_socket.send(sub_id.encode(),zmq.SNDMORE)
                    sub_socket.send("You were already subscribed to the topic: {}".format(topic.upper()).encode())
            else:
                sub_info[sub_id] = {topic : total_message_line}
                sub_socket.send(sub_id.encode(),zmq.SNDMORE)
                sub_socket.send("You are now subscribed to the topic: {}".format(topic.upper()).encode())

            json.dump(sub_info, file, indent=4)


            file.truncate()
            file.close()

        return

    async def unsubscribe(self, sub_id, topic):

        # print("sub_id = {}".format(sub_id))

        # check if the file exists and if it does open it
        if os.path.exists(program_files_dir + "subscriber_info.json"):

            file = open(program_files_dir + "subscriber_info.json", "r+")

            try:
                sub_info = json.load(file)
                if(sub_id in sub_info and topic in sub_info[sub_id]):
                    del sub_info[sub_id][topic]
                    sub_socket.send(sub_id.encode(),zmq.SNDMORE)
                    sub_socket.send("You are now not subscribed to the topic: {}".format(topic.upper()).encode())
                else:
                    sub_socket.send(sub_id.encode(),zmq.SNDMORE)
                    sub_socket.send("You were already not subscribed to the topic: {}".format(topic.upper()).encode())
            except:
                sub_info = {}
                sub_socket.send(sub_id.encode(),zmq.SNDMORE)
                sub_socket.send("You were already not subscribed to the topic: {}".format(topic.upper()).encode())
            file.seek(0)



            json.dump(sub_info, file, indent=4)
            file.truncate()
            file.close()
        return

    async def get(self, sub_id, topic):
        # read sub_id current line
        # read first message from subscribed topic after that line
        # send message

        # print(sub_id)
        # print(topic)

        if os.path.exists(program_files_dir + "subscriber_info.json"):

            # If subscriber lines exist we open it
            file_info = open(program_files_dir + "subscriber_info.json", "r+")
            try:
                subs_subs = json.load(file_info)
                subscriber_info = subs_subs[sub_id]
                if(len(subscriber_info) == 0) : raise NoTopicsSubscribed("No topics")
                if(topic!= None and topic not in subscriber_info.keys()): raise TopicNotSubscribed("Not subscribed")
            except (NoTopicsSubscribed, KeyError, json.decoder.JSONDecodeError):
                sub_socket.send(sub_id.encode(),zmq.SNDMORE)
                sub_socket.send("You don't subscribe any topic as of now. You can do so by sending 'subscribe:topic' ...".encode())
                return
            except TopicNotSubscribed:
                sub_socket.send(sub_id.encode(),zmq.SNDMORE)
                sub_socket.send("You don't subscribe that topic as of now. You can do so by sending 'subscribe:{}' ...".format(topic.lower()).encode())
                return

            file_info.seek(0)

            if os.path.exists(program_files_dir + "messages.txt"):
                messages_file = open(program_files_dir + "messages.txt")
                line_counter = 0
                sent_message = False

                min_line = min(subscriber_info.values())
                for line in messages_file:

                    line_counter += 1
                    if (min_line >= line_counter): continue
                    line_information = line.split(":")

                    line_topic = line_information[0]
                    line_message = line_information[1]


                    if(line_topic not in subscriber_info or subscriber_info[line_topic] >= line_counter): continue

                    if(topic != None and line_topic != topic): continue

                    sent_message = True

                    subscriber_info[line_topic] = line_counter

                    sub_socket.send(sub_id.encode(),zmq.SNDMORE)
                    sub_socket.send("Topic: {} Message: {}".format(line_topic,line_message).encode())
                    break

                if(not sent_message):
                    subscriber_info = {x: line_counter if subscriber_info[x] == min_line else subscriber_info[x] for x in subscriber_info}

                    sub_socket.send(sub_id.encode(),zmq.SNDMORE)
                    sub_socket.send("There are no new messages on the topics you subscribe.".encode())

                messages_file.close()


            json.dump(subs_subs, file_info, indent=4)

            return

        print("Some critical error has occurred while reading subscriber information. Server will now close...")
        sub_socket.send(sub_id.encode(),zmq.SNDMORE)
        sub_socket.send("Server encoutered a critical error while loading request...".encode())
        exit(1)

# Create the Switcher object
sub_message_switcher = Switcher()

# Aux function to check if subkey exists in a dictionary
def checkIfSubKeyExists(key):
    try:
        file_info = open(program_files_dir + "subscriber_info.json", "r+")
        dict = json.load(file_info)
        file_info.close()
        for k in dict.keys():
            if (key in dict.get(k).keys()):
                return True
        return False
    except:
        return False

async def save_message(message, pub_id, topic):
    global total_message_line
    # Create a file descriptor and save a message to a new file or append to the end of one that already exists
    # To remove ambiguity we keep all messages on the same file and read them one by one.
    # No need for pub_id but we still keep it appended to the message that was written

    # If subscriber lines exist we open it
    if(checkIfSubKeyExists(topic)):
        print("Saving contents to file...")
        file = open(program_files_dir + "messages.txt", "a")
        file.write(topic + ":" + message + ":" +  pub_id + '\n')
        file.close()

        total_message_line += 1
        print("Contents saved.")
        print()
    else:
        print("Topic doesn't have any active subscriptions. Not saving contents to file...")

    return

# This method is called 2 times due to the way that zmq sockets work.
async def process_pub_message(message):
    global pub_id
    message_topic_arr = message.decode("UTF-8").split(":")

    processed_message = message_topic_arr[0].strip()
    processed_topic = "PUB_ID"

    if(len(message_topic_arr) > 1):
        processed_topic = message_topic_arr[1].upper().strip()
        print("Received message: {} | Sent by publisher: {} | Topic: {}".format(processed_message, pub_id, processed_topic))
        await save_message(processed_message,pub_id, processed_topic)
        pub_socket.send(pub_id.encode(),zmq.SNDMORE)
        pub_socket.send(message)
        return

    print("Publisher with ID: {} is trying to send a message...".format(processed_message))
    pub_id = processed_message

    return


async def process_sub_message(message):
    global sub_id
    command_topic_arr = message.decode("UTF-8").split(":")

    processed_command = command_topic_arr[0].lower().strip()
    processed_topic = "SUB_ID"

    if(len(command_topic_arr) > 1):
        # print(message.decode())
        processed_topic = command_topic_arr[1].upper().strip()
        print("Received command: {} | Sent by subscriber: {} | Topic: {}".format(processed_command, sub_id, processed_topic))
        try:
            if(processed_topic != ''):
                await sub_message_switcher.execute_command(processed_command, sub_id, processed_topic)
                return
            elif(processed_command == "get"):
                await sub_message_switcher.execute_command(processed_command, sub_id)
            else:
                raise Error
        except:
            sub_socket.send(sub_id.encode(),zmq.SNDMORE)
            sub_socket.send("The message: {}, isn't valid.".format(message.decode()).encode())
        return

    print("Subscriber with ID: {} is trying to send a message...".format(processed_command))
    sub_id = processed_command
    return


def read_message(args):
    # Read from a file a message that belongs to a certain topic
    # We need to keep track of subscribers id so that we know where to start reading and what to read
    return

async def main_loop():
    # Server must be listening to incoming messages from publishers.
    # Server must also be listening for get requests from subscribers.

    # Start polling

    poller = zmq.Poller() # At the moment we only need to listen to 2 sockets

    # Register both sockets for polling

    poller.register(pub_socket, zmq.POLLIN)
    poller.register(sub_socket, zmq.POLLIN)

    print("Server is online!")
    while True:

        # Create a dictionary with the sockets we created
        sockets = dict(poller.poll()) # we can setup a timeout for exiting blocking calls poll(1000) will block for 1s an then timeout

        # Using the socket as a key we can find if the socket has content to poll
        if(pub_socket in sockets and sockets[pub_socket] == zmq.POLLIN):
            pub_message = pub_socket.recv(zmq.NOBLOCK)
            await process_pub_message(pub_message)

        if(sub_socket in sockets and sockets[sub_socket] == zmq.POLLIN):
            sub_message = sub_socket.recv(zmq.NOBLOCK)
            await process_sub_message(sub_message)

    return

def build_vars():
    global sub_dict
    global pub_list
    global total_message_line

    if(os.path.exists(program_files_dir + "pub_file.txt")):
        pub_file = open(program_files_dir + "pub_file.txt")
        pub_list = pub_file.read().split(":")

    total_message_line = sum(1 for line in open(program_files_dir + "messages.txt"))
    return

# Create folders and files where content will be saved
def create_program_files():
    if not os.path.exists(program_files_dir):
        os.makedirs(program_files_dir)

    if not os.path.exists(program_files_dir + "subscriber_info.json"):
        f = open(program_files_dir + "subscriber_info.json", "w")
        f.close()
    if not os.path.exists(program_files_dir + "messages.txt"):
        f = open(program_files_dir + "messages.txt", "w")
        f.close()


# Call the main loop and startup functions
def start():
    print("Creating program files...")
    create_program_files()
    print("Building dictionaries...")
    build_vars()
    print("Starting server...")
    asyncio.run(main_loop())


# A bit of cleanup code in case we use ctrl-c to end the server
def handler(signum, frame):
    msg = "Do you really want to exit? y/n "
    print(msg, end="", flush=True)
    res = input()
    if res == 'y':
        print()
        exit(1)

signal.signal(signal.SIGINT, handler)

# Start the server
start()
