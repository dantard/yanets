from Events import EventRX, EventTXStarted, EventTXFinished, EventOccupyCollisionDomain, EventFreeCollisionDomain, EventChannelAssessment, \
    EventCollisionDomainFree, EventCollisionDomainBusy


def exclude(lst, ex):
    return [x for x in lst if x != ex]


class CollisionDomain:

    def __init__(self, event_queue):
        self.nodes = {}
        self.transmitting = []
        self.event_queue = event_queue
        self.ongoing_frames = []

    def set_nodes(self, nodes):
        self.nodes = nodes
        self.transmitting.extend([False] * len(nodes))

    def get_transmitting(self):
        return self.transmitting

    def process_event(self, event):

        if isinstance(event, EventOccupyCollisionDomain):
            self.transmitting[event.node_id] = True
            self.ongoing_frames.append((event.get_node_id(), event.get_info()))
            for node_id, info in self.ongoing_frames:

                # For each frame in the collision domain queue, mark all other frames
                # as collided if another transmission is started on the same channel
                collisions = [f_node_id for f_node_id, f_info in self.ongoing_frames if f_node_id != node_id]

                # Create the 'collissions' field if it doesn't exist
                info['collisions'] = info.get('collisions', set())

                # Upate the collisions field with the new collisions (notice that this is a set)
                info['collisions'].update(collisions)

        elif isinstance(event, EventFreeCollisionDomain):
            self.transmitting[event.node_id] = False
            self.progagate_frame(event)
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
                    new_event = EventRX(event.ts + 1, receiver.id, event.get_info())
                    self.event_queue.append(new_event)
