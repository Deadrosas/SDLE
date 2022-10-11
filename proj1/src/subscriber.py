import zmq
import random
import sys
import threading
import os
import time


# get() consumes a message from a topic

# subscribe() subscribes a topic
# unsubscribe() unsubscribes a topic

sub_id = str(random.randint(4000, 8000))

program_files_dir = "program_files/"

lock = threading.Lock()

if len(sys.argv) > 1:
    sub_id =  sys.argv[1]

port = "5557" # For now default port for subscribers is 5557

if len(sys.argv) > 2:
    port =  sys.argv[1]
    int(port)


# Create the socket that the publisher connects to
context = zmq.Context()
socket = context.socket(zmq.DEALER)
socket.setsockopt_string(zmq.IDENTITY, sub_id)
socket.connect("tcp://localhost:{}".format(port))

def recv_messages():
    while True:
        msg = socket.recv().decode()
        print("\nReceived message from server:")
        print(" - {}".format(msg))
        print()
        print("Insert your message in the following format command:topic - ", end="", flush=True)
        lock.acquire()
        f = open(program_files_dir + "sub_{}.txt".format(sub_id), "r+")
        lines = f.readlines()
        lines.pop(0)
        f.seek(0)
        for line in lines:
            f.write(line)
        f.truncate()
        f.close()
        lock.release()

def save_message(message):
    lock.acquire()
    f = open(program_files_dir + "sub_{}.txt".format(sub_id), "a")
    f.write(message + '\n')
    f.close()
    lock.release()

def send_message(message):
    try:

        temp = message.split(":")
        print("Sending request to server...")
        
        if(len(temp)>1):
            save_message(message)
            socket.send("{}".format(message).encode())
        else:
            save_message("{}:".format(temp[0]))
            socket.send("{}".format("{}:".format(temp[0])).encode())
        print()
        return

    except:
        print("Some critical error has ocurred closing socket and terminating program...")
        socket.close()
        exit(1)

def send_leftover_commands():

    if not os.path.exists(program_files_dir):
        os.makedirs(program_files_dir)
        
    if not os.path.exists(program_files_dir + "sub_{}.txt".format(sub_id)):
        f = open(program_files_dir + "sub_{}.txt".format(sub_id), "w")
        f.close()
        return
    f = open(program_files_dir + "sub_{}.txt".format(sub_id), "r+")
    lines = f.readlines()
    for line in lines:
        print(line[:-1])
        socket.send(line[:-1].encode())

def main_loop():

    send_leftover_commands()
    recv_thread = threading.Thread(target=recv_messages)
    recv_thread.start()
    # This loop will listen to keyboard inputs and proceed accordingly
    print("Started subscriber with id: {}".format(sub_id))
    while True:
        print("Insert your message in the following format command:topic - ", end="", flush=True)
        send_message(input())

main_loop()