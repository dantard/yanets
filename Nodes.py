import math
import random
import re

import numpy

from Events import EventDataEnqueued, EventTXStarted, EventTXFinished, EventRX, EventOccupyCollisionDomain, EventFreeCollisionDomain, EventChannelAssessment, \
    EventCollisionDomainFree, EventCollisionDomainBusy, EventAckEnqueued, EventSecondAckEnqueued
from lora import compute_lora_duration


class Node(object):

    MODE_RANDOM_EXPONENTIAL = 0 # lamba
    MODE_FIXED = 1 # t1, t2
    MODE_RANDOM_UNIFORM = 2 # t1, t2

    def __init__(self, id, event_queue, collision_domain):
        self.id = id
        self.event_queue = event_queue
        self.collision_domain = collision_domain
        self.latitude = 0
        self.longitude = 0
        self.mode = Node.MODE_RANDOM_EXPONENTIAL
        self.data = []
        self.t1 = 10
        self.t2 = 1000

    def get_id(self):
        return self.id

    def process_event(self, event):
        pass

    def set_latlon(self, lat, lon):
        self.latitude = float(lat)
        self.longitude = float(lon)


    def set_data(self, data):
        self.data = data

    def get_data(self):
        return self.data

    def distance(self, node):
        return numpy.sqrt((self.latitude - node.latitude) ** 2 + (self.longitude - node.longitude) ** 2)

    def get_config(self):
        return {"latitude": self.latitude, "longitude": self.longitude}

    def get(self, key):
        return self.get_config().get(key)

    def set_frame_generation_mode(self, mode, p1, p2=None):
        self.mode = mode
        self.t1 = p1
        self.t2 = p2

    def get_next_ts(self):
        if self.mode == Node.MODE_RANDOM_EXPONENTIAL:
            return numpy.random.exponential(1000 / self.t1)
        elif self.mode == Node.MODE_FIXED:
            return self.t1
        elif self.mode == Node.MODE_RANDOM_UNIFORM:
            return numpy.random.uniform(self.t1, self.t2)
        else:
            return 0

class AlohaNode(Node):

    def __init__(self, id, event_queue, collision_domain):
        super(AlohaNode, self).__init__(id, event_queue, collision_domain)
        self.received = []
        self.serial = 0

    def event_rx(self, event):
        self.received.append(event.get_info())

    def event_tx_finished(self, event):
        new_event = EventFreeCollisionDomain(event.ts + 1, self.id, event.get_info())
        self.event_queue.push(new_event)

    def event_data_enqueued(self, event):
        new_event = EventTXStarted(event.ts, self.id, event.get_info())
        self.event_queue.push(new_event)

    def event_tx_started(self, event):
        new_event = EventOccupyCollisionDomain(event.ts, self.id, event.get_info())
        self.event_queue.push(new_event)
        self.serial += 1

        bw = event.inspect('bw')
        sf = event.inspect('sf')
        cr = event.inspect('codr')
        ToA = compute_lora_duration(80, sf, bw, cr, 1)
        #print(ToA)

        new_event = EventTXFinished(event.ts + ToA, self.id, new_event.get_info())
        new_event.add_info(self.get_config())
        self.event_queue.push(new_event)



    def enqueue_new_data(self, event):
        new_event = EventDataEnqueued(event.ts + self.get_next_ts(), self.id)
        new_event.set_info(self.get_config())
        self.event_queue.push(new_event)

    def process_event(self, event):

        # print("Node %d: processing event %s" % (self.id, type(event)))

        if isinstance(event, EventDataEnqueued):
            self.event_data_enqueued(event)

        elif isinstance(event, EventTXStarted):
            self.event_tx_started(event)

        elif isinstance(event, EventTXFinished):
            self.event_tx_finished(event)

        elif isinstance(event, EventRX):
            self.event_rx(event)
        else:
            return False

        return True

    def get_received(self):
        return self.received


class LoraNode(AlohaNode):
    def __init__(self, id, event_queue, collision_domain):
        super().__init__(id, event_queue, collision_domain)
        self.tracker_id = 0
        self.freq = 868.5
        self.sf = 7
        self.bw = 125
        self.codr = "4/5"

    def configure(self, tracker_id, freq=None, sf=None, bw=None, codr=None, lon=None, lat=None):
        super().set_latlon(lat, lon)
        self.tracker_id = tracker_id
        self.freq = float(freq) if freq is not None else self.freq
        self.sf = float(sf) if sf is not None else self.sf
        self.bw = float(bw) if bw is not None else self.bw
        self.codr = codr if codr is not None else self.codr

    def get_config(self):
        config = super().get_config()
        config.update({'freq': self.freq, 'sf': self.sf, 'bw': self.bw, 'codr': self.codr})
        return config


    def print(self):
        print("tracker_id: {}, freq: {}, sf: {}, bw: {}, codr: {}, lon: {}, lat: {} data: {}".format(self.tracker_id, self.freq, self.sf, self.bw, self.codr, self.longitude, self.latitude, self.data))

class UserNode(LoraNode):
    def event_data_enqueued(self, event):
        super().event_data_enqueued(event)
        self.enqueue_new_data(event)

class CafcoNode(UserNode):
    def __init__(self, id, event_queue, collision_domain):
        super().__init__(id, event_queue, collision_domain)

    def set_config(self, info):
        pattern = r"SF(\d+)BW(\d+)"

        # Extracting sf and bw from the datr field
        sf, bw = None, None
        if (datr:= info.get('datr')) is not None:
            matches = re.findall(pattern, datr[0])
            if matches:
                sf = matches[0][0]
                bw = matches[0][1]
        if (freq:= info.get('freq')) is not None:
            freq = freq[0]

        if (codr:= info.get('codr')) is not None:
            codr = codr[0]
        super().configure(info.get('trackerid'), freq, sf, bw, codr, info.get('longitude'), info.get('latitude'))
        self.set_data(info.get('data'))

class LoraGateway(LoraNode):
    def event_rx(self, event):
        super().event_rx(event)
        new_event = EventAckEnqueued(event.ts + 11, self.id )
        info = self.get_config()
        new_event.add_info(info)
        self.event_queue.push(new_event)
        new_event = EventSecondAckEnqueued(event.ts + 12, self.id)
        new_event.add_info(event.get_info())
        self.event_queue.push(new_event)


class CSMANode(AlohaNode):

    def __init__(self, node_id, event_queue, collision_domain):
        super(CSMANode, self).__init__(node_id, event_queue, collision_domain)
        self.csma_fail = 0
        self.retry_limit = 5

    def set_retry_limit(self, limit):
        self.retry_limit = limit

    def event_data_enqueued(self, event):
        new_event = EventChannelAssessment(event.ts, self.id, event.get_info())
        self.event_queue.push(new_event)
        self.enqueue_new_data(event)

    def event_collision_domain_free(self, event):
        new_event = EventTXStarted(event.ts, self.id, event.get_info())
        self.event_queue.push(new_event)

    def event_collision_domain_busy(self, event):
        info = event.get_info()
        retries = info.get('retries', 0)
        if retries < self.retry_limit:

            info['retries'] = retries + 1
            new_event = EventChannelAssessment(event.ts + 1, self.id, info)
            self.event_queue.push(new_event)
        else:
            self.csma_fail += 1

    def process_event(self, event):
        if super().process_event(event):
            return True

        elif isinstance(event, EventCollisionDomainFree):
            self.event_collision_domain_free(event)

        elif isinstance(event, EventCollisionDomainBusy):
            self.event_collision_domain_busy(event)
