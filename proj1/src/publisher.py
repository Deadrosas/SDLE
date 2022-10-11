import zmq
import random
import sys
import threading
import os
import time


# put() publishes a message on a topic

# subscribe() subscribes a topic
# unsubscribe() unsubscribes a topic

pub_id = str(random.randint(0, 4000))

program_files_dir = "program_files/"

lock = threading.Lock()

if len(sys.argv) > 1:
    pub_id =  sys.argv[1]

port = "5556" # For now default port for publishers is 5556

if len(sys.argv) > 2:
    port =  sys.argv[1]
    int(port)


# Create the socket that the publisher connects to
context = zmq.Context()
socket = context.socket(zmq.DEALER)
socket.setsockopt_string(zmq.IDENTITY, pub_id)
socket.connect("tcp://localhost:{}".format(port))

def recv_messages():
    while True:
        msg = socket.recv().decode()
        msg_arr = msg.split(":")
        print("\nSuccessfully sent:")
        print(" - Message : {}".format(msg_arr[0]))
        print(" - Topic : {}".format(msg_arr[1]))
        print("Insert your message in the following format message:topic - ", end="", flush=True)
        lock.acquire()
        f = open(program_files_dir + "pub_{}.txt".format(pub_id), "r+")
        lines = f.readlines()
        lines.remove(msg+'\n')
        f.seek(0)
        for line in lines:
            f.write(line)
        f.truncate()
        f.close()
        lock.release()

def save_message(message):
    lock.acquire()
    f = open(program_files_dir + "pub_{}.txt".format(pub_id), "a")
    f.write(message + '\n')
    f.close()
    lock.release()

def put(message):
    
    try:
        if message!= None and ":" in message:
            print("Publishing message...")
            save_message(message)
            socket.send("{}".format(message).encode())
            return
        print("Message has no topic. Try again with a valid topic.")
    except zmq.error.Again:
        # Server didn't confirm the reception of the message in time so we need to ask for it again
        print("Error")
    except:
        print("Some critical error has ocurred closing socket and terminating program...")
        socket.close()
        exit(1)
    
    return

def send_leftover_messages():
    if not os.path.exists(program_files_dir):
        os.makedirs(program_files_dir)
        
    if not os.path.exists(program_files_dir + "pub_{}.txt".format(pub_id)):
        f = open(program_files_dir + "pub_{}.txt".format(pub_id), "w")
        f.close()
        return
    f = open(program_files_dir + "pub_{}.txt".format(pub_id), "r+")
    lines = f.readlines()
    for line in lines:
        print(line[:-1])
        socket.send(line[:-1].encode())


def main_loop():

    send_leftover_messages()
    recv_thread = threading.Thread(target=recv_messages)
    recv_thread.start()
    # This loop will listen to keyboard inputs and proceed accordingly
    print("Started publisher with id: {}".format(pub_id))
    while True:
        print("Insert your message in the following format message:topic - ", end="", flush=True)
        inp = input()
        put(inp)

main_loop()
