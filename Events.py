from Frame import Frame


class Event:
    event_counter = 0
    def __init__(self, ts):
        self.ts = ts
        self.event_id = Event.event_counter
        Event.event_counter += 1

    def get_ts(self):
        return self.ts

class NodeEvent(Event):
    def __init__(self, ts, node, handler=None):
        super().__init__(ts)
        self.node = node
        self.handler = handler if handler is not None else node.get_node_id()
        Event.event_counter += 1
    def get_node(self):
        return self.node

    def get_handler(self):
        return self.handler


class NodeEventWithFrame(NodeEvent):
    def __init__(self, ts, node, frame, handler=None):
        super().__init__(ts, node, handler)
        self.frame = frame

    def get_frame(self):
        return self.frame

class ChannelEvent(Event):
    pass

class ChannelEventWithFrame(ChannelEvent):
    def __init__(self, ts, frame):
        super().__init__(ts)
        self.frame = frame

    def get_frame(self):
        return self.frame

class EventNewData(NodeEvent):
    pass

class EventTXStarted(NodeEvent):
    pass

class EventEnterChannel(ChannelEventWithFrame):
    pass

class EventLeaveChannel(ChannelEventWithFrame):
    pass

class EventTXFinished(NodeEventWithFrame):
    pass

class EventRX(NodeEventWithFrame):
    pass