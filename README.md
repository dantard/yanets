# LoRaSim

The LoRaSim simulator is software for simulating LoRa networks. It is a discrete-time simulator in which the software sequentially processes a set of time-ordered events that are generated during the simulation itself.

## Introduction

This software is written in Python and uses Object-Oriented Programming (OOP), meaning that the entities involved in the simulation are Python objects.

Conceptually, the program has an event queue where events generated during the simulation execution are stored and processed sequentially. When an event is inserted (push operation), the queue is sorted according to the timestamp (ts) of the events in ascending order. When an element needs to be extracted from the queue for processing, a pop operation is executed, returning the event with the smallest ts. In this way, the passage of time is simulated discretely.

During the development of this simulator, an effort was made to maintain a correspondence between the elements involved in the real-world system and their representation within the program. For this reason, we distinguish three main classes (in the OOP sense): Node, Frame, and Channel. Additionally, the Event class must be mentioned.

Nodes represent LoRa devices and are further divided into LoraDevice and Gateway, both derived from Node, representing end devices and gateways respectively.

Objects of type Frame contain the information that a node intends to send or has sent, similar to what happens in real-world transmissions. They are created by the nodes themselves in response to certain events and are associated with the same event, as will be explained shortly.

The Channel (class Channel, of which there is a single instance) represents the communication channel where the nodes coexist. It is responsible for keeping track of which nodes are transmitting at each moment and with which parameters, and therefore determines which node(s) will receive a given Frame according to the propagation pattern and depending on whether any collisions occurred. It also handles statistics calculation.

Finally, the classes derived from the base class Event describe the specific event occurring at any given time, such as the arrival of new data or the start of a transmission. Although all events share the same parent class, in this simulator's hierarchy two branches are distinguished: NodeEvent and ChannelEvent. The first type is processed by Node objects while the second is processed by the Channel. Below are all the event types.

NodeEvent types:
EventNewData  
EventTXStarted  
EventTXFinished

ChannelEvent types:
EventEnterChannel  
EventLeaveChannel

To understand the simulator's basic functioning, consider the sequence of events that take place during a simple transmission by a single Node. For simplicity, let's assume the queue is empty. Before the simulation starts, at least one event must be generated to initiate the event loop.

Therefore:

An EventNewData is inserted into the queue, associated with one of the nodes—say Node with id=1—and with a timestamp equal to the initial time. This means the node has received new data to send (for example, a new sensor reading).

The event loop starts, extracting and processing the first element of the queue.

In this case, the event is EventNewData, which is a NodeEvent and thus will be processed by Node id=1. It then generates a new event of type EventTXStarted indicating the start of the transmission, which is inserted into the queue with the same timestamp.

The event loop resumes, extracting a new element from the queue—the Event inserted in step 2. Since EventTXStarted is also a NodeEvent, it is processed again by the same Node. In response to this event, the Node creates a Frame object in which it copies all its transmission parameters (SF, BW, etc.) and its current position, and then creates an EventEnterChannel event containing the Frame object. Finally, it inserts the EventEnterChannel object into the queue, again with the same timestamp.

The event loop runs again and extracts the newly generated EventEnterChannel, which, being a subtype of ChannelEvent, is processed by the Channel object. At this point, the Channel registers that node 1 has started its transmission and stores the frame among the "ongoing frames." It then calculates the ToA and generates a new EventTXFinished event with a timestamp equal to the sum of the EventEnterChannel's timestamp and the ToA, which is inserted into the queue.

## Output File Structure

[
   {
       "_id": {
           "$oid": 0            # Simulator-wide frame counter
       },
       "trackerid": "bb000008", # ED that has sent the frame
       "longitude": 42.9655609, # Longitude of the ED at moment of sending 
       "latitude": -2.6147869,  # Latitude of the ED at moment of sending
       "gateways": [            # List of all the gateways
           "gw000001",
           "gw000002"
       ],
       "fcnt": 1,               # Node-wide frame counter
       "date": "2023-07-30T05:56:01.237000Z", # Date of the sending
       "freq": [                
           868.3                # Frequency at which the frame has been sent
       ],
       "datr": "SF7BW125",      # Frame’s Spreading Factor and Bandwidth
       "lsnr": [
           16.86397811388605,   # SNR with which the frame has been
                                  received by the first gateway of the list


           17.147959363336327   # SNR with which the frame has been
                                  received by the second gateway of the list


                                # Same info for the next gateway in the list
       ],
       "rssi": [
           -100.16692175603339, # RSSI with which the frame has been
                                  received by the first gateway of the list


           -99.88294050658311   # RSSI with which the frame has been
                                  received by the second gateway of the list


                                # Same info for the next gateway in the list


       ],
       "th_snr": [              
           true,                # The frame SNR is above the threshold to at the
                                # receiver be received by the first gateway 


           true                 # The frame SNR is above the threshold at the 
                                # receiver to be received by the second gateway


                                # Same info for the next gateway in the list


       ],
       "th_sir": [
       [
           true                 # No collision for this frame at the first gateway
       ],
       [
           false,               # This frame collided with frame 2 at the second 
           2                    # gateway (2 is the global counter fcnt)
       ]
                                # Same info for the next gateway in the list
   ]
},
{...} # Same info for the subsequent frame
]
