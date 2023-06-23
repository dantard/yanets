class Event:
    def __init__(self, ts):
        self.ts = ts

    def get_ts(self):
        return self.ts


class NodeEvent(Event):
    def __init__(self, ts, node_id):
        super().__init__(ts)
        self.node_id = node_id

    def get_node(self):
        return self.node_id


class EventWithPayload(NodeEvent):
    def __init__(self, ts, node_id, size):
        super().__init__(ts, node_id)
        self.size = size

    def get_payload(self):
        return self.size


class EventDataEnqueued(EventWithPayload):
    pass


class EventTXStarted(EventWithPayload):
    pass


class EventTXFinished(NodeEvent):
    pass
