from Frame import Frame


class Event:
    event_counter = 0

    def __init__(self, ts, frame, handler=None):
        self.ts = ts
        self.frame = frame
        self.handler = frame.get_source() if handler is None else handler
        self.event_id = Event.event_counter
        Event.event_counter += 1

    def get_ts(self):
        return self.ts

    def get_handler(self):
        return self.handler

    def get_frame(self) -> Frame:
        return self.frame


class InfoEvent(Event):
    pass

class NodeEvent(InfoEvent):
    pass


class CollisionDomainEvent(InfoEvent):
    pass


class EventOccupyCollisionDomain(CollisionDomainEvent):
    pass


class EventFreeCollisionDomain(CollisionDomainEvent):
    pass


class EventChannelAssessment(CollisionDomainEvent):
    pass


class EventDataEnqueued(NodeEvent):
    pass

class EventTXStarted(NodeEvent):
    pass

class EventAckEnqueued(EventDataEnqueued):
    pass

class EventSecondAckEnqueued(EventDataEnqueued):
    pass

class EventTXFinished(NodeEvent):
    pass


class EventRX(NodeEvent):
    pass


class EventCollisionDomainFree(NodeEvent):
    pass


class EventCollisionDomainBusy(NodeEvent):
    pass
