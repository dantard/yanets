class Frame:
    class Status:
        NO_SNR = 0
        COLLISION = 1
        OK = 2

        def __init__(self, received, reason, rssi=None, lsnr=None):
            self.received = received
            self.error_reason = reason
            self.collision_with = []
            self.rssi = rssi
            self.lsnr = lsnr

        def get_collision_with(self):
            return self.collision_with

        def add_collision(self, node_id):
            self.collision_with.append(node_id)
        def set_rssi(self, rssi):
            self.rssi = rssi

        def get_rssi(self):
            return self.rssi

        def set_lsnr(self, lsnr):
            self.lsnr = lsnr

        def get_lsnr(self):
            return self.lsnr

        def __str__(self):
            if self.received:
                return 'OK'
            else:
                return "NO_SNR" if self.error_reason == 0 else "COLLIS" + ' ' + str(self.collision_with)

        def __repr__(self):
            return str(self.received) + ' ' + str(self.error_reason) + ' ' + str(self.collision_with)

    serial = 0

    def __init__(self, node, **kwargs):
        self.source = node
        self.fcnt = node.get_fcnt()
        self.ts = kwargs.get('ts', 0)
        self.receive_status = {}
        self.type = kwargs.get('type', 'DATA')
        self.pos = node.get_pos()
        self.phy_payload = str(node.get_phy_payload())
        self.bw = node.get_bw()
        self.sf = node.get_sf()
        self.cr = node.get_cr()
        self.freq = node.get_freq()
        self.eirp = node.get_tx_power() + node.get_antenna_gain()
        self.serial = Frame.serial
        Frame.serial += 1

    def set_receive_status(self, gw_id, receive_ok, why=None, rssi=None, lsnr=None):
        status = self.receive_status.get(gw_id, None)
        if status is None:
            status = Frame.Status(receive_ok, why, rssi, lsnr)
            self.receive_status[gw_id] = status

        status.received = receive_ok
        status.error_reason = why

        return status

    def get_fcnt(self):
        return self.fcnt

    def get_receive_status(self, index=None):
        if index is None:
            return self.receive_status

        return self.receive_status[index]

    def get_eirp(self):
        return self.eirp

    def get_serial(self):
        return self.serial

    def get_source(self):
        return self.source

    def get_type(self):
        return self.type

    def get_pos(self):
        return self.pos

    def get_phy_payload(self):
        return self.phy_payload

    def get_bw(self):
        return self.bw

    def get_sf(self):
        return self.sf

    def get_cr(self):
        return self.cr

    def get_freq(self):
        return self.freq

    def get_ts(self):
        return self.ts

    def __repr__(self):
        repr = "{:3d} {:8s} {:4s} {:2d}B SF{:02d} BW{:03.0f} {:3.1f}Mhz".format(
            self.source.get_node_id(),
            self.source.get_trackerid(),
            self.type, len(self.phy_payload),
            self.sf,
            self.bw,
            self.freq,
        )
        return repr
