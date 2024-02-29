class Frame:

    serial = 0

    def __init__(self, node, **kwargs):
        self.latitude = node.get_latlon()[0]
        self.longitude = node.get_latlon()[1]
        self.collisions = set()
        self.data = str(node.get_data())
        self.type = kwargs.get('type', 'DATA')
        self.source = node.get_node_id()
        self.destination = kwargs.get('dest', None)
        self.info = node.get_config().copy()
        self.serial = Frame.serial
        Frame.serial += 1

    def get_serial(self):
        return self.serial

    def get_info(self, param=None):
        if param:
            return self.info.get(param)
        return self.info


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

