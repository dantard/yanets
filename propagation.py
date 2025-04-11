from Nodes import LoraEndDevice, LoraGateway

class Status:
    def __init__(self):
        self.SNR_ok = False
        self.SIR_same_SF_ok = False
        self.SIR_dif_SF_ok = False
        self.P_rx_dB = 0
        self.path_loss = 0
        self.P_tx_dB = 0
        self.SF = 0
        self.state = 0
        self.id = 0


