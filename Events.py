from Frame import Frame


class Event:
    event_counter = 0
    def __init__(self, ts):
        self.ts = ts
        self.event_id = Event.event_counter
        Event.event_counter += 1

    def get_ts(self):
        return self.ts

class NodeEvent:
    def __init__(self, ts, node, handler=None):
        super().__init__(ts)
        self.node = node
        self.handler = handler if handler is not None else node.get_node_id()
        Event.event_counter += 1
    def get_node(self):
        return self.node

    def get_handler(self):
        return self.handler

class EventWithFrame(Event):
    def __init__(self, ts, node, frame, handler=None):
        super().__init__(ts, node, handler)
        self.frame = frame

class NodeEvent:
    pass

class ChannelEvent:
    pass

class EventNewData(Event, NodeEvent):
    pass

class EventTXStarted(Event, NodeEvent):
    pass


class EventEnterChannel(EventWithFrame, ChannelEvent):
    pass

