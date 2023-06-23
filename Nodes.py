from Events import EventDataEnqueued, EventTXStarted, EventTXFinished


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
            self.event_queue.push(EventTXStarted(event.ts + 1, self.id, event.get_payload()))

        elif isinstance(event, EventTXStarted):
            self.collision_domain.set_transmitting(self.id, True)
            self.event_queue.push(EventTXFinished(event.ts + 1, self.id))

        elif isinstance(event, EventTXFinished):
            self.collision_domain.set_transmitting(self.id, False)


class LoraGateway(LoraNode):
    pass
