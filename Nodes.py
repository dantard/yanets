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


class AlohaNode(Node):

    def __init__(self, id, event_queue, collision_domain):
        super(AlohaNode, self).__init__(id, event_queue, collision_domain)
        self.received = []
        self.serial = 0

    def event_rx(self, event):
        self.received.append(event.get_info())

    def event_tx_finished(self, event):
        new_event = EventFreeCollisionDomain(event.ts + 1, self.id, event.get_info())
        self.event_queue.push(new_event)

    def event_data_enqueued(self, event):
        new_event = EventTXStarted(event.ts, self.id, event.get_info())
        self.event_queue.push(new_event)
        self.enqueue_new_data(event)

    def event_tx_started(self, event):
        new_event = EventOccupyCollisionDomain(event.ts, self.id, event.get_info())
        new_event.extend({'sf': 7, 'serial': self.serial})
        self.event_queue.push(new_event)
        self.serial += 1

        new_event = EventTXFinished(event.ts + numpy.random.randint(1, 1000), self.id, new_event.get_info())
        self.event_queue.push(new_event)

    def enqueue_new_data(self, event):
        new_event = EventDataEnqueued(event.ts + 5000, self.id)
        new_event.set_info({'source': self.id, 'payload': 50})
        self.event_queue.push(new_event)

    def process_event(self, event):

        # print("Node %d: processing event %s" % (self.id, type(event)))

        if isinstance(event, EventDataEnqueued):
            self.event_data_enqueued(event)

        elif isinstance(event, EventTXStarted):
            self.event_tx_started(event)

        elif isinstance(event, EventTXFinished):
            self.event_tx_finished(event)

        elif isinstance(event, EventRX):
            self.event_rx(event)
        else:
            return False

        return True

    def get_received(self):
        return self.received


class LoraNode(AlohaNode):
    pass


class LoraGateway(AlohaNode):
    pass


class CSMANode(AlohaNode):

    def __init__(self, node_id, event_queue, collision_domain):
        super(CSMANode, self).__init__(node_id, event_queue, collision_domain)
        self.csma_fail = 0
        self.retry_limit = 5

    def set_retry_limit(self, limit):
        self.retry_limit = limit

    def event_data_enqueued(self, event):
        new_event = EventChannelAssessment(event.ts, self.id, event.get_info())
        self.event_queue.push(new_event)
        self.enqueue_new_data(event)

    def event_collision_domain_free(self, event):
        new_event = EventTXStarted(event.ts, self.id, event.get_info())
        self.event_queue.push(new_event)

    def event_collision_domain_busy(self, event):
        info = event.get_info()
        retries = info.get('retries', 0)
        if retries < self.retry_limit:

            info['retries'] = retries + 1
            new_event = EventChannelAssessment(event.ts + 1, self.id, info)
            self.event_queue.push(new_event)
        else:
            self.csma_fail += 1

    def process_event(self, event):
        if super().process_event(event):
            return True

        elif isinstance(event, EventCollisionDomainFree):
            self.event_collision_domain_free(event)

        elif isinstance(event, EventCollisionDomainBusy):
            self.event_collision_domain_busy(event)
