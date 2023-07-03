from Events import EventRX, EventTXStarted, EventTXFinished


class CollisionDomain:

    def __init__(self, event_queue):
        self.nodes = []
        self.transmitting = []
        self.event_queue = event_queue

    def append_nodes(self, nodes):
        self.nodes.extend(nodes)
        self.transmitting.extend([False] * len(nodes))

    def process(self, event):

        if isinstance(event, EventTXStarted):
            self.transmitting[event.node_id] = True

            new_event = EventTXFinished(event.ts + 1, event.node_id, event.get_info())
            self.event_queue.push(new_event)

        if isinstance(event, EventTXFinished):
            self.transmitting[event.node_id] = False

            for n in self.nodes:  # type n: LoraNode
                new_event = EventRX(event.ts + 1, n.id, event.get_info())
                self.event_queue.append(new_event)
