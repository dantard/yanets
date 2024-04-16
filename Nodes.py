import re
import sys
from datetime import datetime

import numpy

import defaults
import rng
from Events import EventTXStarted, EventEnterChannel, EventNewData, EventTXFinished, EventLeaveChannel
from Frame import Frame


class Node(object):
    def __init__(self, id, event_queue, channel):
        self.event_queue = event_queue
        self.channel = channel
        self.id = id
        self.fcnt = 0
        self.latitude = 0
        self.longitude = 0
        self.trackerid = None
        self.phy_payload = str()
        self.freq = defaults.freq
        self.sf = defaults.sf
        self.bw = defaults.bw
        self.codr = defaults.codr
        self.SNR_min = defaults.SNR_min
        self.tx_power_dBm = defaults.tx_power_dBm
        self.antenna_gain_dBi = defaults.antenna_gain_dBi
        self.noise_figure_dB = defaults.noise_figure_dB


    def get_fcnt(self):
        self.fcnt += 1
        return self.fcnt

    def get_node_id(self):
        return self.id

    def get_pos(self):
        return self.latitude, self.longitude

    def set_latlon(self, lat, lon):
        self.latitude = float(lat)
        self.longitude = float(lon)

    def get_phy_payload(self):
        return self.phy_payload

    def event_tx_finished(self, event):
        new_event = EventLeaveChannel(event.ts, event.get_frame(), self, self.channel)
        self.event_queue.push(new_event)


    def event_new_data(self, event):
        new_event = EventTXStarted(event.ts, self)
        self.event_queue.push(new_event)

    def event_tx_started(self, event):
        new_event = EventEnterChannel(event.ts, Frame(self, ts=event.ts), self, self.channel)
        self.event_queue.push(new_event)

    def process_event(self, event):

        if isinstance(event, EventNewData):
            self.event_new_data(event)

        elif isinstance(event, EventTXStarted):
            self.event_tx_started(event)

        elif isinstance(event, EventTXFinished):
            self.event_tx_finished(event)
        else:
            return False

        return True

    def get_trackerid(self):
        return self.trackerid

    def get_snr_min(self, sf):
        return self.SNR_min.get('SF' + str(sf))

    def get_tx_power(self):
        return self.tx_power_dBm

    def get_antenna_gain(self):
        return self.antenna_gain_dBi

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
        self.trackerid = info.get('trackerid', self.trackerid)




class LoraEndDevice(Node):

    def __init__(self, id, event_queue, channel):
        super(LoraEndDevice, self).__init__(id, event_queue, channel)
        self.busy = False
        self.traffic_period = defaults.traffic_period
        self.traffic_t_init = 0
        self.backoff = defaults.backoff


    def get_t_init(self):
        return self.traffic_t_init

    def event_new_data(self, event):
        # WARNING: Overrides parent method to add backoff
        if self.busy:
            print("Trama descartada por transmision concurrente", self.get_node_id())
        else:
            backoff = rng.get_random_int(0, self.backoff)
            new_event = EventTXStarted(event.ts + backoff, self)
            self.event_queue.push(new_event)
            self.busy = True

        # Generate subsequent data event
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

        if (datr := info.get("datr")) is not None:
            datr = datr[0] if type(datr) is list else datr
            pattern = r"SF(\d+)BW(\d+)"
            matches = re.findall(pattern, datr)
            if matches:
                self.sf = int(matches[0][0])
                self.bw = float(matches[0][1])

        self.tx_power_dBm = float(info.get('tx_power_dBm', self.tx_power_dBm))
        self.antenna_gain_dBi = float(info.get('antenna_gain_dBi', self.antenna_gain_dBi))
        self.noise_figure_dB = float(info.get('noise_figure_dB', self.noise_figure_dB))
        self.SNR_min = info.get('SNR_min', self.SNR_min)
        self.backoff = int(info.get('backoff', self.backoff))

        if (traffic := info.get('traffic')) is not None:
            self.traffic_period = float(traffic.get('period', self.traffic_period))
            if self.backoff >= self.traffic_period:
                raise ValueError("Node {}: Backoff must be shorter than period".format(self.get_trackerid()))

            t_init = traffic.get('t_init', defaults.traffic_t_init)
            init_ts = datetime.strptime(t_init, "%Y-%m-%dT%H:%M:%S.%fZ")
            epoch_time = datetime(1970, 1, 1)
            self.traffic_t_init = (init_ts - epoch_time).total_seconds()

        return True

    def __repr__(self):
        return ("EndDevice {}, t_init: {} "
                "lon: {}, lat: {}, freq: {}, "
                "sf: {}, bw: {}, codr: {}, "
                "tx_power_dBm: {}, antenna_gain_dBi: {}, "
                "noise_figure_dB: {}, backoff: {}").format(self.trackerid,self.traffic_t_init, self.longitude, self.latitude, self.freq, self.sf, self.bw, self.codr, self.tx_power_dBm, self.antenna_gain_dBi, self.noise_figure_dB, self.backoff)

class LoraGateway(Node):
    def __init__(self, id, event_queue, channel):
        super().__init__(id, event_queue, channel)

    def __repr__(self):
        return "Gateway   {}, lon: {}, lat: {}".format(self.trackerid, self.longitude, self.latitude)