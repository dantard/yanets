class Event:
    event_counter = 0

    def __init__(self, ts, info=None):
        self.ts = ts
        self.info = dict() if info is None else info.copy()
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
    def get_event_id(self):
        return self.event_id


class InfoEvent(Event):
    def __init__(self, ts, obj, **kwargs):
        if not type(obj) == int:
            super().__init__(ts, kwargs.get('info', obj.get_config()))
            self.generator = obj.get_node_id()
            self.node_id = kwargs.get('handler', obj.get_node_id())
            self.latitude, self.longitude = kwargs.get("latlon", obj.get_latlon())
            self.data = kwargs.get('data', obj.get_data())
        else:
            super().__init__(ts, kwargs.get("info",{}))
            self.node_id = obj
            self.generator = obj
            self.latitude, self.longitude = kwargs.get("latlon", (0, 0))
            self.data = kwargs.get("data", [])

    def get_config(self):
        return self.info

    def get_latlon(self):
        return self.latitude, self.longitude

    def from_node(self, node):
        self.node_id = node.get_id()
        self.longitude, self.latitude = node.get_latlon()
        self.data = node.get_data()
        self.info = node.get_config()

    def get_data(self):
        return self.data

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
    def __init__(self, ts, obj, **kwargs):
        super().__init__(ts, obj, **kwargs)
        self.info.update({"type": "DATA"})


class EventTXStarted(NodeEvent):
    pass

class EventAckEnqueued(EventDataEnqueued):
    def __init__(self, ts, obj, **kwargs):
        super().__init__(ts, obj, **kwargs)
        self.info.update({"type": "ACK1"})
        self.info.update({"collisions": set()})

class EventSecondAckEnqueued(EventDataEnqueued):
    def __init__(self, ts, obj, **kwargs):
        super().__init__(ts, obj, **kwargs)
        self.info.update({"type":"ACK2"})
        self.info.update({"collisions": set()})

class EventTXFinished(NodeEvent):
    pass


class EventRX(NodeEvent):
    pass


class EventCollisionDomainFree(NodeEvent):
    pass


class EventCollisionDomainBusy(NodeEvent):
    pass
