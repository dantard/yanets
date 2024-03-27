import math
import geopy.distance

from Events import EventEnterChannel, EventLeaveChannel, EventTXFinished, EventRX
from Frame import Frame
from Nodes import LoraGateway, LoraEndDevice
from lora import compute_lora_duration


def exclude(lst, ex):
    return [x for x in lst if x != ex]


class Channel:
    SNR_thresholds = [-7.5, -10.0, -12.5, -15.0, -17.5, -20.0]

    def __init__(self, event_queue, channel_model):
        self.nodes = {}
        self.transmitting = []
        self.event_queue = event_queue
        self.ongoing_frames = []
        self.alpha = channel_model.get('alpha')
        self.L0 = channel_model.get('L0')
        self.SIR_thresholds = channel_model.get('SIR_thresholds')

    def get_transmitting(self):
        return self.transmitting

    def set_nodes(self, nodes):
        self.nodes = nodes
        self.transmitting.extend([False] * len(nodes))

    def process_event(self, event):

        if isinstance(event, EventEnterChannel):
            frame = event.get_frame()
            node = frame.get_source()
            self.transmitting[node.get_node_id()] = True

            self.propagation(frame)

            self.ongoing_frames.append(event.get_frame())

            phy_payload_len = len(frame.get_phy_payload()) * 4 / 8
            ToA = compute_lora_duration(phy_payload_len, frame.get_sf(), frame.get_bw(), frame.get_cr())
            new_event = EventTXFinished(event.ts + ToA, self, event.get_frame(), node)
            self.event_queue.push(new_event)

        elif isinstance(event, EventLeaveChannel):
            frame = event.get_frame()
            source_node = frame.get_source()
            self.transmitting[source_node.get_node_id()] = False
            self.ongoing_frames.remove(event.get_frame())
            gws = [n for n in self.nodes.values() if isinstance(n, LoraGateway)]
            for gateway in gws:
                new_event = EventRX(event.ts, self, event.get_frame(), gateway)
                self.event_queue.push(new_event)

    def path_loss(self, pos1, pos2):
        dist = geopy.distance.geodesic(pos1, pos2).km
        return self.L0 + 10 * self.alpha * math.log10(dist)

    def propagation(self, frame):

        gws = [n for n in self.nodes.values() if isinstance(n, LoraGateway)]

        # print(self.nodes, gws)

        for gateway in gws:

            frame.set_receive_status(gateway.get_node_id(), True)

            P_rx_dBm = frame.get_eirp() - self.path_loss(frame.get_pos(), gateway.get_pos())
            p_noise_dBm = -174 + 10 * math.log10(frame.get_bw() * 1000) + gateway.noise_figure_dB
            SNR = P_rx_dBm - p_noise_dBm
            #print("SNR: ", SNR, "P_rx_dB: ", P_rx_dBm, "p_noise: ", p_noise_dBm, "frame.get_eirp(): ", frame.get_eirp(), "frame.get_bw(): ", frame.get_bw())

            if SNR < gateway.get_snr_min(frame.get_sf()):
                frame.set_receive_status(gateway.get_node_id(), False, Frame.Reason.NO_SNR)
                continue

            for ongoing_frame in self.ongoing_frames:

                if frame.get_freq() == ongoing_frame.get_freq():

                    ongoing_source = ongoing_frame.get_source()
                    ongoing_P_rx_dBm = ongoing_frame.get_eirp() - self.path_loss(ongoing_frame.get_pos(), gateway.get_pos())
                    delta_P_rx = ongoing_P_rx_dBm - P_rx_dBm

                    ongoing_sf = ongoing_frame.get_sf()
                    frame_sf = frame.get_sf()

                    if delta_P_rx < self.SIR_thresholds[frame_sf - 7][ongoing_sf - 7]:
                        reason = frame.set_receive_status(gateway.get_node_id(), False, Frame.Reason.COLLISION)
                        reason.add_collision(ongoing_source.get_node_id())

                    if -delta_P_rx < self.SIR_thresholds[ongoing_sf - 7][frame_sf - 7]:
                        reason = ongoing_frame.set_receive_status(gateway.get_node_id(), False, Frame.Reason.COLLISION)
                        reason.add_collision(frame.get_source().get_node_id())
