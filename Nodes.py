import random

import numpy

from Events import EventDataEnqueued, EventTXStarted, EventTXFinished, EventRX, EventOccupyCollisionDomain, EventFreeCollisionDomain, EventChannelAssessment, \
    EventCollisionDomainFree, EventCollisionDomainBusy


class Node(object):
    def __init__(self, id, event_queue, collision_domain):
        self.id = id
        self.event_queue = event_queue
        self.collision_domain = collision_domain
        self.x = 0
        self.y = 0

    def process_event(self, event):
        pass

    def set_pose(self, x, y):
        self.x = x
        self.y = y

    def distance(self, node):
        return numpy.sqrt((self.x - node.x) ** 2 + (self.y - node.y) ** 2)


class LoraDevice(Node):

    def __init__(self, id, event_queue, collision_domain):
        super(LoraDevice, self).__init__(id, event_queue, collision_domain)
        self.received = []
        self.serial = 0
        self.csma_fail = 0

    def process_event(self, event):

        # print("Node %d: processing event %s" % (self.id, type(event)))

        if isinstance(event, EventDataEnqueued):
            new_event = EventChannelAssessment(event.ts, self.id, event.get_info())
            self.event_queue.push(new_event)

            new_event = EventDataEnqueued(event.ts + 5000, self.id)
            new_event.set_info({'source': self.id, 'payload': 50})
            self.event_queue.push(new_event)

        elif isinstance(event, EventCollisionDomainFree):
            new_event = EventTXStarted(event.ts, self.id, event.get_info())
            self.event_queue.push(new_event)

        elif isinstance(event, EventCollisionDomainBusy):
            info = event.get_info()
            retries = info.get('retries', 0)
            if retries < 5:
                info['retries'] = retries + 1
                new_event = EventChannelAssessment(event.ts+1, self.id, info)
                self.event_queue.push(new_event)
            else:
                self.csma_fail += 1

        elif isinstance(event, EventTXStarted):
            new_event = EventOccupyCollisionDomain(event.ts, self.id, event.get_info())
            new_event.extend({'sf': 7, 'serial': self.serial})
            self.event_queue.push(new_event)
            self.serial += 1

            new_event = EventTXFinished(event.ts + numpy.random.randint(1, 1000), self.id, new_event.get_info())
            self.event_queue.push(new_event)

        elif isinstance(event, EventTXFinished):
            new_event = EventFreeCollisionDomain(event.ts + 1, self.id, event.get_info())
            self.event_queue.push(new_event)

        elif isinstance(event, EventRX):
            self.received.append(event.get_info())

    def get_received(self):
        return self.received


class LoraNode(LoraDevice):
    pass


class LoraGateway(LoraDevice):
    pass
