from Events import EventRX, EventTXStarted, EventTXFinished, EventEnterChannel, EventFreeCollisionDomain, EventChannelAssessment, \
    EventCollisionDomainFree, EventCollisionDomainBusy
from Frame import Frame
from lora import compute_lora_duration


def exclude(lst, ex):
    return [x for x in lst if x != ex]


class Channel:

    def __init__(self, event_queue):
        self.nodes = {}
        self.transmitting = []
        self.event_queue = event_queue
        self.ongoing_frames = []

    def get_transmitting(self):
        return self.transmitting

    def set_nodes(self, nodes):
        self.nodes = nodes
        self.transmitting.extend([False] * len(nodes))

    def start_tx(self, frame):
        self.transmitting[frame.get_source()] = True
        self.ongoing_frames.append(frame)

    def finish_tx(self, frame):
        self.transmitting[frame.get_source()] = False
        self.ongoing_frames.remove(frame)

    '''
    def process_event(self, event):

        if isinstance(event, EventEnterChannel):
            self.transmitting[event.frame.get_source()] = True
            self.ongoing_frames.append(event.get_frame())

            for frame in self.ongoing_frames:
                if frame.get_source() == event.frame.get_source():
                    continue
                event.get_frame().add_collision(frame.get_source())
                frame.add_collision(event.frame.get_source())

            bw = event.get_frame().get_info("bw")
            sf = event.get_frame().get_info('sf')
            cr = event.get_frame().get_info('codr')
            ToA = compute_lora_duration(80, sf, bw, cr, 1)
            new_event = EventFreeCollisionDomain(event.ts + ToA, event.get_frame())
            self.event_queue.push(new_event)

        elif isinstance(event, EventFreeCollisionDomain):
            self.transmitting[event.get_frame().get_source()] = False
            self.progagate_frame(event)

            new_event = EventTXFinished(event.ts, event.get_frame())
            self.event_queue.push(new_event)

            self.ongoing_frames.remove(event.get_frame())


    def progagate_frame(self, event):

        collisioners = event.get_frame().get_collisions()
        source_node = self.nodes[event.get_frame().get_source()]

        # I consider the receivers one by one (all the nodes except the source)
        for receiver in exclude(self.nodes.values(), source_node):
            # I also exclude from the receivers the collisioner because it was transmitting at the same time
            if collisioners is not None and receiver.id not in collisioners:
                # Compute for *that* receiver the SNR with the source
                snr_emitter_receiver = 1 / source_node.distance(receiver)

                # Now I compute the SNR of all the collisioners with the receiver
                collisioners_min_distance = 1e6
                for collisioner_id in collisioners:
                    collisioner = self.nodes[collisioner_id]
                    collisioners_min_distance = min(collisioner.distance(receiver), collisioners_min_distance)

                snr_collisioners_receiver_max = 1 / collisioners_min_distance

                # If the SNR of the source is higher than the SNR of the collisioners, the receiver will receive
                if snr_emitter_receiver > snr_collisioners_receiver_max:
                    new_event = EventRX(event.ts + 1, event.get_frame(), receiver.id)
                    self.event_queue.append(new_event)
    '''