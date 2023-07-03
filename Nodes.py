from Events import EventDataEnqueued, EventTXStarted, EventTXFinished, EventRX


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


class LoraNode(Node):
    def process_event(self, event):

        print("Node %d: processing event %s" % (self.id, type(event)))

        if isinstance(event, EventDataEnqueued):
            new_event = EventTXStarted(event.ts + 1, self.id, event.get_info())
            new_event.extend({'sf': 7, 'source': self.id})
            self.event_queue.push(new_event)

        elif isinstance(event, EventTXStarted):
            self.collision_domain.process(event)

        elif isinstance(event, EventTXFinished):
            self.collision_domain.process(event)

        elif isinstance(event, EventRX):
            print("Node {}: received data from node {}, data: {}".format(self.id, event.get('source'), event.get_info()))


class LoraGateway(LoraNode):
    pass
