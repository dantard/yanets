class CollisionDomain():

    def __init__(self):
        self.nodes = []
        self.transmitting = []

    def append_nodes(self, nodes):
        self.nodes.extend(nodes)
        self.transmitting.extend([False] * len(nodes))

    def set_transmitting(self, node_id, value):
        self.transmitting[node_id] = value

        print("Node {} started transmitting".format(node_id), self.transmitting)
