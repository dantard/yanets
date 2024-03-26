import re
import sys

import numpy

import defaults
from Events import EventTXStarted, EventEnterChannel, EventNewData, EventTXFinished, EventLeaveChannel, EventRX
from Frame import Frame


class Node(object):
    rng = None



    def __init__(self, id, event_queue, collision_domain):
        self.id = id
        self.event_queue = event_queue
        self.collision_domain = collision_domain
        self.latitude = 0
        self.longitude = 0
        self.phy_payload = str()

    def get_node_id(self):
        return self.id

    def get_pos(self):
        return self.latitude, self.longitude

    def process_event(self, event):
        pass

    def set_latlon(self, lat, lon):
        self.latitude = float(lat)
        self.longitude = float(lon)

    def get_phy_payload(self):
        return self.phy_payload

    def distance(self, node):
        return numpy.sqrt((self.latitude - node.latitude) ** 2 + (self.longitude - node.longitude) ** 2)

    def get_config(self):
        return {}

    def get(self, key):
        return self.get_config().get(key)

class AlohaNode(Node):

    def __init__(self, id, event_queue, collision_domain):
        super(AlohaNode, self).__init__(id, event_queue, collision_domain)
        self.received = []

    def event_rx(self, event):
        self.received.append(event.get_frame())

    def event_tx_finished(self, event):
        new_event = EventLeaveChannel(event.ts, event.get_frame())
        self.event_queue.push(new_event)

    def event_new_data(self, event):
        backoff = 0
        new_event = EventTXStarted(event.ts + backoff, self)
        self.event_queue.push(new_event)

    def event_tx_started(self, event):
        new_event = EventEnterChannel(event.ts, Frame(self))
        self.event_queue.push(new_event)

    def enqueue_new_data(self, event):
        # TODO! This is a very simple implementation
        new_event = EventNewData(event.ts + 1, self, Frame(self))  ### OJO
        self.event_queue.push(new_event)

    def process_event(self, event):

        # print("Node %d: processing event %s" % (self.id, type(event)))

        if isinstance(event, EventNewData):
            self.event_new_data(event)

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
        #
        self.tx_power_dBm = 0
        self.antenna_gain = 0
        self.noise_figure = 0
        self.G_dB = defaults.G_dB
        self.SNR_min = defaults.SNR_min

    def get_snr_min(self, sf):
        return self.SNR_min.get('SF' + str(sf))

    def get_tx_power(self):
        return self.tx_power_dBm

    def get_antenna_gain(self):
        return self.antenna_gain

    def get_bw(self):
        return self.bw

    def get_sf(self):
        return self.sf

    def get_cr(self):
        return self.codr

    def get_freq(self):
        return self.freq

    def update_config(self, info):
        self.latitude = float(info.get('latitude', self.latitude))
        self.longitude = float(info.get('longitude', self.longitude))

    def get_config(self):
        config = super().get_config()
        config.update({'freq': self.freq, 'sf': self.sf, 'bw': self.bw, 'codr': self.codr})
        return config

    def print(self):
        print("tracker_id: {}, freq: {}, sf: {}, bw: {}, codr: {}, lon: {}, lat: {} data: {}".format(self.tracker_id, self.freq, self.sf, self.bw, self.codr,
                                                                                                     self.longitude, self.latitude, self.data))


class LoraEndDevice(LoraNode):

    @staticmethod
    def set_rng(rng):
        Node.rng = rng

    MODE_RANDOM_EXPONENTIAL = 0  # lamba
    MODE_FIXED = 1  # t1, t2
    MODE_RANDOM_UNIFORM = 2  # t1, t2

    def __init__(self, id, event_queue, collision_domain):
        super(LoraEndDevice, self).__init__(id, event_queue, collision_domain)
        self.busy = False
        self.traffic = defaults.traffic
        self.traffic_mode = defaults.traffic_mode
        self.traffic_period = defaults.traffic_period
        self.traffic_t_init = defaults.traffic_t_init



    def event_new_data(self, event):
        if self.busy:
            print("Trama descartada por transmision concurrente", self.get_node_id())
        else:
            super().event_new_data(event)

        self.busy = True
        new_event = EventNewData(event.ts + self.traffic_period, self)
        self.event_queue.push(new_event)

    def event_tx_finished(self, event):
        super().event_tx_finished(event)
        self.busy = False


    def update_config(self, info):
        super().update_config(info)

        self.phy_payload = info.get('PHYPayload', self.phy_payload)

        freq = info.get('freq', self.freq)
        self.freq = float(freq[0] if type(freq) is list else freq)

        codr = info.get('codr', self.codr)
        self.codr = codr[0] if type(codr) is list else codr

        if (datr:= info.get("datr")) is not None:
            datr = datr[0] if type(datr) is list else datr
            pattern = r"SF(\d+)BW(\d+)"
            matches = re.findall(pattern, datr)
            if matches:
                self.sf = int(matches[0][0])
                self.bw = float(matches[0][1])

        self.tx_power_dBm = float(info.get('tx_power_dBm', self.tx_power_dBm))
        self.antenna_gain = float(info.get('antenna_gain', self.antenna_gain))
        self.noise_figure = float(info.get('noise_figure', self.noise_figure))
        self.G_dB = float(info.get('G_dB', self.G_dB))
        self.SNR_min = info.get('SNR_min', self.SNR_min)

        if (traffic:=info.get('traffic')) is not None:
            self.traffic_mode = traffic.get('mode', self.traffic_mode)
            self.traffic_period = traffic.get('period', self.traffic_period)
            self.traffic_t_init = traffic.get('t_init', self.traffic_t_init)



class LoraGateway(LoraNode):
    def __init__(self, id, event_queue, collision_domain):
        super().__init__(id, event_queue, collision_domain)
        self.snr_min = 0

    def event_rx(self, event):
        super().event_rx(event)

        #new_event = EventAckEnqueued(event.ts + 1000, Frame(self, type='ACK1'))
        #self.event_queue.push(new_event)

        #new_event = EventSecondAckEnqueued(event.ts + 2000, Frame(self, type='ACK2'))
        #self.event_queue.push(new_event)


