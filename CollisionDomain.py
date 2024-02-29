from Events import EventRX, EventTXStarted, EventTXFinished, EventOccupyCollisionDomain, EventFreeCollisionDomain, EventChannelAssessment, \
    EventCollisionDomainFree, EventCollisionDomainBusy
from lora import compute_lora_duration


def exclude(lst, ex):
    return [x for x in lst if x != ex]


class CollisionDomain:

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

    def get_transmitting(self):
        return self.transmitting

    def process_event(self, event):

        if isinstance(event, EventOccupyCollisionDomain):
            self.transmitting[event.node_id] = True
            self.ongoing_frames.append((event.node_id, event.get_info()))

            if event.get_info().get('collisions') is None:
                event.get_info().update({'collisions': set()})

            for o_node_id, o_info in self.ongoing_frames:
                if o_node_id != event.node_id:
                    event.get_info().get('collisions').add(o_node_id)
                    o_info.get('collisions').add(event.node_id)


            bw = event.inspect('bw')
            sf = event.inspect('sf')
            cr = event.inspect('codr')
            ToA = compute_lora_duration(804, sf, bw, cr, 1)
            new_event = EventFreeCollisionDomain(event.ts + ToA, event)
            self.event_queue.push(new_event)

        elif isinstance(event, EventFreeCollisionDomain):
            self.transmitting[event.node_id] = False
            self.progagate_frame(event)
            new_event = EventTXFinished(event.ts, event)
            self.event_queue.push(new_event)

            self.ongoing_frames.remove((event.node_id, event.get_info()))

        elif isinstance(event, EventChannelAssessment):
            #print(self.transmitting, any(self.transmitting))
            if not any(self.transmitting):
                new_event = EventCollisionDomainFree(event.ts + 1, event.node_id, event.get_info())
                self.event_queue.push(new_event)
            else:
                new_event = EventCollisionDomainBusy(event.ts + 1, event.node_id, event.get_info())
                self.event_queue.push(new_event)

    def progagate_frame(self, event):

        collisioners = event.get_info().get('collisions')
        source_node = self.nodes[event.node_id]
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
                    new_event = EventRX(event.ts + 1, event, handler=receiver.id)
                    self.event_queue.append(new_event)
