class Event:
    event_counter = 0

    def __init__(self, ts, info=None):
        self.ts = ts
        self.info = dict() if info is None else info
        self.event_id = Event.event_counter
        Event.event_counter += 1

    def get_ts(self):
        return self.ts

    def set(self, key, value):
        self.info[key] = value

    def get(self, key):
        return self.info.get(key)

    def get_info(self):
        return self.info

    def inspect(self, key):
        return self.info.get(key)

    def set_info(self, info):
        self.info = info

    def add_info(self, info):
        self.info.update(info)


class InfoEvent(Event):
    def __init__(self, ts, node_id, info=None):
        super().__init__(ts, info)
        self.node_id = node_id
        self.longitude, self.latitude = None, None
        self.data = None

    def from_node(self, node):
        self.node_id = node.get_id()
        self.longitude, self.latitude = node.get_latlon()
        self.data = node.get_data()

    def get_node_id(self):
        return self.node_id


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
