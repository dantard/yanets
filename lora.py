import math


def compute_lora_duration(B, sf, bw, cr):
    #print("B: ", B, "sf: ", sf, "bw: ", bw, "cr: ", cr)
    CRS = ["4/5", "4/6", "4/7", "4/8"]
    CR = CRS.index(cr) + 1
    L_preamble = 8 # 8 Symbols according to regional parameters V 1.1
    H = 0 # According to standard there is always a header (H=0 means header is present)
    t_symbol = (2.0 ** sf) / (bw * 1000)
    t_preamble = (L_preamble + 4.25) * t_symbol
    L_payload = 8 + math.ceil((8 * B - 4 * sf + 28 + 16 - 20 * H) / (4 * sf)) * (CR + 4)
    T_payload = t_symbol * L_payload
    ToA = t_preamble + T_payload
    return ToA


'''
/*!
 * \brief Computes the packet time on air in ms for the given payload
 *
 * \Remark Can only be called once SetRxConfig or SetTxConfig have been called
 *
 * \param [IN] modem      Radio modem to be used [0: FSK, 1: LoRa]
 * \param [IN] bandwidth    Sets the bandwidth
 *                          FSK : >= 2600 and <= 250000 Hz
 *                          LoRa: [0: 125 kHz, 1: 250 kHz,
 *                                 2: 500 kHz, 3: Reserved]
 * \param [IN] datarate     Sets the Datarate
 *                          FSK : 600..300000 bits/s
 *                          LoRa: [6: 64, 7: 128, 8: 256, 9: 512,
 *                                10: 1024, 11: 2048, 12: 4096  chips]
 * \param [IN] coderate     Sets the coding rate (LoRa only)
 *                          FSK : N/A ( set to 0 )
 *                          LoRa: [1: 4/5, 2: 4/6, 3: 4/7, 4: 4/8]
 * \param [IN] preambleLen  Sets the Preamble length
 *                          FSK : Number of bytes
 *                          LoRa: Length in symbols (the hardware adds 4 more symbols)
 * \param [IN] fixLen       Fixed length packets [0: variable, 1: fixed]
 * \param [IN] payloadLen   Sets payload length when fixed length is used
 * \param [IN] crcOn        Enables/Disables the CRC [0: OFF, 1: ON]
 *
 * \retval airTime        Computed airTime (ms) for the given packet payload length
 */
'''


def compute_lora_duration_2(bandwidth, datarate, coderate, preambleLen, fixLen, payloadLen, crcOn):
    crDenom = coderate + 4
    lowDatareOptimize = False

    if datarate in [5, 6]:
        if preambleLen < 12:
            preambleLen = 12

    if (bandwidth == 0 and datarate in [11, 12]) or (bandwidth == 1 and datarate == 12):
        lowDatareOptimize = True

    ceilNumerator = (payloadLen << 3) + (16 if crcOn else 0) - (4 * datarate) + (0 if fixLen else 20)

    if datarate <= 6:
        ceilDenominator = 4 * datarate
    else:
        ceilNumerator += 8
        ceilDenominator = 4 * (datarate - 2) if lowDatareOptimize else 4 * datarate

    if ceilNumerator < 0:
        ceilNumerator = 0

    intermediate = ((ceilNumerator + ceilDenominator - 1) // ceilDenominator) * crDenom + preambleLen + 12

    if datarate <= 6:
        intermediate += 2

    return int((4 * intermediate + 1) * (1 << (datarate - 2)))