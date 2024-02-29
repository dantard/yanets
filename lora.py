import math


def compute_lora_duration(B, sf, bw, cr, H):
    CRS = ["4/5", "4/6", "4/7", "4/8"]
    CR = CRS.index(cr) + 1
    L_preamble = 10
    t_symbol = (2.0 ** sf) / bw
    t_preamble = (L_preamble + 4.25) * t_symbol
    L_payload = 8 + math.ceil((8 * B - 4 * sf + 28 + 16 - 20 * H) / (4 * sf)) * (CR + 4)
    T_payload = t_symbol * (L_payload)
    T_oA = t_preamble + T_payload
    return T_oA