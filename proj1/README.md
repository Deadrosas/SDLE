# SDLE Project

SDLE Project for group T1G14.

Group members:

1. Gustavo Sena (up201806078@edu.fe.up.pt)
2. João Rosário (up201806334@edu.fe.up.pt)
3. Iohan Sardinha (up201801011@edu.fe.up.pt)
4. João Rocha (up201806261@edu.fe.up.pt)
### Dependencies

All python files were written in Python 3.9, using the libzmq python binding as required, for the use of ZeroMQ socket implementation.

### How to Run

Inside the **src** folder run:
- python3 server.py [publisher_port] [subscriber_port]
- python3 subscriber.py [subscriber_id] [subscriber_port]
- python3 publisher.py  [publisher_id] [publisher_port]
There can be an arbitrary number of subscribers and publishers

On the running subscriber there are 4 alternatives, either subscribe a topic with **"subscribe:topic"**, or unsubsribe a topic with, **"unsubscribe:topic"**. After that we can start getting messages with, **"get"**, which will return the first message (on a topic we subscribe) received by the server, or we can also do **"get:topic"** which will return us the first message from that specific topic, in case we don't subscribe the topic sent on this call, the server will return an error.

On the running publisher, simply send a message, followed by its topic in the following format, **"message:topic"**.

**NOTE**: subscribers will only be able to "get" messages that were sent after they subscribed the topic, thus making it essential to subscribe prior to sending a message to a specific topic.
