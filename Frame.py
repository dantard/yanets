class Frame:
    def __init__(self, ts, node, **kwargs):
        self.latitude = node.get_latlon()[0]
        self.longitude = node.get_latlon()[1]
        self.collisions = set()
        self.data = node.get_data().copy()
        self.type = kwargs.get('type', 'DATA')
        self.ts = ts
        self.source = node.get_node_id()
        self.destination = kwargs.get('dest', None)
        self.handler = kwargs.get('handler', node.get_node_id())
        self.info = node.get_config().copy()

    def get_info(self):
        return self.info

    def get_ts(self):
        return self.ts

    def get_source(self):
        return self.source


    def get_destination(self):
        return self.destination

    def get_type(self):
        return self.type

    def get_latlon(self):
        return self.latitude, self.longitude

    def get_data(self):
        return self.data

    def get_collisions(self):
        return self.collisions

    def add_collision(self, node_id):
        self.collisions.add(node_id)

    def get_handler(self):
        return self.handler
