from Frame import Frame


class Event:
    event_counter = 0

    def __init__(self, ts, creator=None, handler=None):
        self.ts = ts
        self.creator = creator
        self.handler = handler if handler is not None else creator
        self.event_id = Event.event_counter
        Event.event_counter += 1

    def get_ts(self):
        return self.ts

    def get_creator(self):
        return self.creator

    def get_handler(self):
        return self.handler

    def process(self):
        self.handler.process_event(self)


class NodeEvent(Event):
    pass


class NodeEventWithFrame(NodeEvent):
    def __init__(self, ts, node, frame, handler=None):
        super().__init__(ts, node, handler)
        self.frame = frame

    def get_frame(self):
        return self.frame


class ChannelEvent(Event):
    pass


class ChannelEventWithFrame(ChannelEvent):
    def __init__(self, ts, frame, creator=None, handler=None):
        super().__init__(ts, creator, handler)
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
