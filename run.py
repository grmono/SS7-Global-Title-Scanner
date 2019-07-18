import socket
import sys
from argparse import ArgumentParser
import os
from struct import *
from threading import *
from binascii import *
from colorama import init
from termcolor import cprint
from pyfiglet import figlet_format
from prettytable import PrettyTable


def initM3UA():
    # M3UA Header
    m3ua_version = 1  # 1Byte
    m3ua_reserved = 0  # 1Byte

    # M3UA Message Classes, 1Byte
    m3ua_msg_class = {'ASPStateMaint': 3,
                      'ASPTrafficMaint': 4, 
                      'TransferMessages': 1, 
                      'SSNM': 2}
    # M3UA Message Types
    m3ua_msg_type = {
    				 'ASPUP': 1, 
    				 'ASPC': 1, 
    				 'ASPUP_Ack': 4,
                     'ASPAC_ACK': 3, 
                     'Payload': 1, 
                     'DAUD': 3}

    m3ua_param_tags = {
    					'TrafficMode': 11, 
    					'RoutingContext': 6,
                        'ASPIdentifier': 17, 
                        'ProtocolData': 528}  # 2Bytes

    # 4Bytes, total length of message to be the sum of all messages lenghts of the high layers (sccp,tcap) and be replaced with calcsize()
    msg_length = 0

    # M3UA ASP Identifier Parameter
    m3ua_asp_identifier = 3  # 4Bytes
    aspid_param_len = 8  # 2Bytes

    # M3UA Traffic Mode type Parameters
    m3ua_traffic_mode = {
    					 'Loadshare': 2,
                         'Broadcast': 3, 
                         'Override': 1}  # 4Bytes

    traffic_mode_param_len = 8  # 2Bytes

    # M3UA Routing Context Parameters
    m3ua_rc = 100  # 4Bytes
    rc_param_len = 8

    # M3UA Protocol Data Parameters
    protocol_data_param_len = 49

    opc = client_pc  # 4Bytes
    dpc = peer_pc  # 4Bytes

    # service indicator, SCCP
    SI = 3  # 1Byte

    NI = 0  # 1Byte, International, adjust to 2 for national
    sls = 1  # 1Byte
    mp = 0  # 1Byte

    try:
        m3ua_header_aspup = pack('!BBBBiHHi', m3ua_version, m3ua_reserved, m3ua_msg_class['ASPStateMaint'], m3ua_msg_type['ASPUP'], msg_length,
                                 m3ua_param_tags['ASPIdentifier'], aspid_param_len, m3ua_asp_identifier)
        sk.sendall(m3ua_header_aspup)
        reply_1 = sk.recv(4096)

        m3ua_recv = unpack('!BBBBiHHi', reply_1)
        #print(m3ua_recv)
        #if (1 and 0 and 3 and 4) in m3ua_recv:
        #    print('True')

        # ASPUP_ACK Received
        if m3ua_recv[3] == 4:
            m3ua_header_aspc = pack('!BBBBi', m3ua_version, m3ua_reserved,m3ua_msg_class['ASPTrafficMaint'], m3ua_msg_type['ASPC'], calcsize('BBBBi'))
            sk.sendall(m3ua_header_aspc)
        else:
            print('\033[31m[-]\033[0m M3UA ASP is Down..Probably not a Sigtran Node')

    except Exception as e:
        print("\033[31m[-]\033[0mError M3UA Stack Failed to Initialize: %s" %str(e))

    else:
        print("[+]M3UA Stack Initialized...\n")
        reply_2 = sk.recv(4096)
        #m3ua_reply = unpack('!BBBBiHHiHHi',reply_2)

        msg_length = 69

        # return m3ua header set to send data protocol class to be used by other stack layers
        m3ua_header_data = pack('!BBBBiHHiiBBBB', m3ua_version, m3ua_reserved, m3ua_msg_class['TransferMessages'], m3ua_msg_type['Payload'],
                                msg_length, m3ua_param_tags['ProtocolData'], protocol_data_param_len,
                                opc, dpc, SI, NI, sls, mp)

        return m3ua_header_data


def initSCCP(source_GT, destination_GT, destination_ssn):
    # Mandatory Fixed Parameters
    sccp_msg_type = 9  # 1Byte

    # SCCP data transfer message class, in-sequence delievery
    sccp_msg = b'\x81'
    # sccp_msg_handling = 8 #1Byte
    sccp_pointer_var1 = 3  # 1Byte
    sccp_pointer_var2 = 14  # 1Byte
    sccp_pointer_var3 = 24  # 1Byte

    # Mandatory Variable Parameters
    # Called Party Address
    # Address Indicator
    # Address indicator is 1 byte in length its value determined based on the bits that are included\
    # in our case a value of 18(0x12) indicated that routing based on GT, GT format is 0100, SSN is included, no PC is included
    called_addr_length = (5 + dGT_len)  # 1Byte
    called_addr_indicator = b'\x12'  # 0x12 in hex, 1Byte
    called_ssn = destination_ssn  # 1Byte

    # Global title
    called_translation_type = b'\x00'  # 1Byte
    called_numbering_plan = b'\x12'  # 1Byte
    # International Number
    called_nature_of_address_indicator = b'\x04'  # 1Byte
    called_GT = destination_GT  # 6-8 Bytes

    # Calling Party Address
    calling_addr_length = (5 + sGT_len)  # 1Byte
    calling_addr_indicator = b'\x12'  # 0x12 in hex, 1Byte
    calling_ssn = source_ssn  # 1Byte

    # Global title
    calling_translation_type = b'\x00'  # 1Byte
    calling_numbering_plan = b'\x12'  # 1Byte

    # International Number
    
    calling_nature_of_address_indicator = b'\x04'  # 1Byte
    calling_GT = source_GT  # 6-8 Bytes
   

    # try:
    sccp_header = pack('!B1sBBBB1sB1s1s1s6sB1sB1s1s1s6s', sccp_msg_type, sccp_msg,
                       sccp_pointer_var1, sccp_pointer_var2, sccp_pointer_var3, called_addr_length, called_addr_indicator,
                       called_ssn, called_translation_type, called_numbering_plan, called_nature_of_address_indicator,
                       called_GT, calling_addr_length, calling_addr_indicator, calling_ssn, calling_translation_type, calling_numbering_plan,
                       calling_nature_of_address_indicator, calling_GT)

    return sccp_header


def initTCAP():

    # Transaction
    # TCAP Message Type(Empty TCAP)
    # Incase that the destination GT listens on the scanned SSN, it will return with a TCAP Abort message, else it will respond with UDTS error message of
    # No translation on this specific address, as internally in core network GT is translated to pc+ssn

    message_type = 96  # 1Byte, 0x60 as hex
    tcap_length = 0  # 1byte, 0x04 as hex

    # Component Tags - Mandatory
    component_tag = b'\xa1'  # 1Byte
    component_length = b'\x1d'  # 1Byte

    try:
        tcap_header = pack('!BB1s1s', message_type, calcsize('BB1s1s'), component_tag, component_length)
        return tcap_header
    except Exception as e:
        print('\033[31m[-]\033[0mError in TCAP Layer: %s  ' %str(e))
        sys.exit(2)


if __name__ == '__main__':

    global client_pc
    global peer_pc
    global sGT_len
    global dGT_len

    init(strip=not sys.stdout.isatty())
    banner = "GTScan"
    cprint(figlet_format(banner, font="standard"), "blue")
    print ("\033[33m[+]\033[0m	\tGlobalTitle Scanner		\033[33m[+]\033[0m")
    print ("\033[33m[+]\033[0m	\t    Version 1			\033[33m[+]\033[0m")
    print ("\033[33m[+]\033[0m\t      Author: LoayAbdelrazek		\033[33m[+]\033[0m")
    print ("\033[33m[+]\033[0m	\t  (@SigPloiter)			\033[33m[+]\033[0m\n")



    table = PrettyTable()
    table.field_names=['Global Title', 'Subsytem Number', 'Node']
    
    

    parser = ArgumentParser()

    parser.add_argument("-l", dest="client_ip",
                        default=False, action="store",
                        help="\tSpecify local IP listening for sctp")

    parser.add_argument("-p", dest="client_port",
                        default=2905, type=int, action="store",
                        help="\tSpecify local sctp port,default 2905")

    parser.add_argument("-r", dest="peer_ip",
                        default=False, action="store",
                        help="\tSpecify Remote STP IP")

    parser.add_argument("-P", dest="peer_port",
                        default=False, type=int, action="store",
                        help="\tSpecify Remote SCTP port")

    parser.add_argument("-c", dest="client_pc",
                        default=False, type=int, action="store",
                        help="\tSpecify local point code")

    parser.add_argument("-C", dest="peer_pc",
                        default=False, type=int, action="store",
                        help="\tSpecify STP point code")

    parser.add_argument("-g", dest="sGT",
                        default=False, action="store",
                        help="\tSpecify local global title")

    parser.add_argument("-G", dest="dGT",
                        default=False, action="store",
                        help="\tSpecify global title(s) to scan,comma-sperated list or range (-) sperated")

    parser.add_argument("-s", dest="source_ssn",
                        default=7, type=int, action="store",
                        help="\tSpecify SSN to use, default is 7")

    args = parser.parse_args()

    if (args.client_ip is False) or (args.client_port is False) or (args.sGT is False) or (args.dGT is False) or (args.client_pc is False) or (args.peer_pc is False):
        print("not enought number of arguments\n\nExample: ./GTScan.py -G 201500000000,201500000002 -g 965123456780 -c 1 -C 2 -p 2905 -P 2906 -l 192.168.56.1 -r 192.168.56.102\n")
        sys.exit(1)

    client_ip = args.client_ip
    client_port = args.client_port
    peer_ip = args.peer_ip
    peer_port = args.peer_port
    client_pc = args.client_pc
    peer_pc = args.peer_pc
    sGT = args.sGT
    dGT = args.dGT
    source_ssn = args.source_ssn

    destination_ssn = {
            6:'HLR', 
            7:'VLR', 
            8:'MSC',
            9:'EIR',
            10:'AuC',
            142:'RANAP',
            143:'RNSAP',
            145:'GMLC',
            146:'gsmSCF_CAP',
            147:'gsmSCF_MAP',
            148:'SIWF',
            149:'SGSN',
            150:'GGSN',
            249:'PCAP',
            250:'BCS',
            251:'MCS_BSSAP-LE',
            252:'SMLC',
            253:'BSS_O&M',
            254:'A_Interface'}

    if len(sGT) % 2 == 0:
        source_GT = unhexlify(''.join([sGT[x:x + 2][::-1] for x in range(0, len(sGT), 2)]))
        sGT_len = len(source_GT)
    

    # Initializing SCTP
    try:
        sk = socket.socket(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_SCTP)
        sk.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sk.bind((client_ip, client_port))
        sk.connect((peer_ip, peer_port))
        sk.settimeout(1)

        
    except socket.error as msg:
        print('\033[31m[-]\033[0mError Socket could not be created: %s' %str(msg))
        sys.exit(1)
    else:
        print('[+]SCTP Stack Initialized...')
        m3ua_header_data = initM3UA()
        

        if "," in dGT:
            dGT = dGT.split(',')

            if len(dGT[0]) % 2 == 0:
                dGT_len = len(unhexlify(''.join([dGT[0][x:x + 2][::-1] for x in range(0, len(dGT[0]), 2)])))
            else:
                dGT_temp = dGT[0] + '0'
                dGT_len = len(unhexlify(''.join([dGT_temp[x:x + 2][::-1] for x in range(0, len(dGT_temp), 2)])))

            for gt in dGT:
                if len(gt) % 2 == 0:
                    destination_GT = unhexlify(''.join([gt[x:x + 2][::-1] for x in range(0, len(gt), 2)]))
                else:
                    gt_temp = gt + '0'
                    destination_GT = len(unhexlify(''.join([gt_temp[x:x + 2][::-1] for x in range(0, len(gt_temp), 2)])))

                for ssn in destination_ssn:
                    try:
                        sccp_header = initSCCP(source_GT, destination_GT, ssn)
                        tcap_header = initTCAP()
                        sk.sendall(m3ua_header_data + sccp_header + tcap_header)
                        print('\033[34m[*]\033[0m Scanning +{} on SSN: {}'.format(gt, ssn))

                        tcap_reply = sk.recv(4096)
                        tcap_recv = unpack_from('!BBB', tcap_reply, offset=66)
                        if tcap_recv == (73,0,74):
                            print('\033[32m[+] {} Detected on GT:+{} ,SSN:{}\033[0m '.format(destination_ssn[ssn], gt, ssn))
                            table.add_row([gt, ssn, destination_ssn[ssn]])
                    except socket.timeout:
                        continue
                        

        elif "-" in dGT:
            dGT = dGT.split('-')

            if len(dGT[0]) % 2 == 0:
                dGT_len = len(unhexlify(''.join([dGT[0][x:x + 2][::-1] for x in range(0, len(dGT[0]), 2)])))
            else:
                #dGT[0] = dGT[0] + '0'
                dGT_len = len(unhexlify(''.join([dGT[0][x:x + 2][::-1] for x in range(0, len(dGT[0]), 2)])))
                dGT[0] = dGT[0][:-1]

            dGT1 = int(dGT[0])
            dGT2 = int(dGT[1])
            

            for gt in range(dGT1, dGT2 + 1):
                if len(str(gt)) % 2 == 0:
                    destination_GT = unhexlify(''.join([str(gt)[x:x + 2][::-1] for x in range(0, len(str(gt)), 2)]))
                else:
                    gt = int(str(gt) + '0')
                    destination_GT = unhexlify(''.join([str(gt)[x:x + 2][::-1] for x in range(0, len(str(gt)), 2)]))

                for ssn in destination_ssn:
                    try:
                        sccp_header = initSCCP(source_GT, destination_GT, ssn)
                        tcap_header = initTCAP()
                        sk.sendall(m3ua_header_data + sccp_header + tcap_header)
                        print('\033[34m[*]\033[0mScanning +{} on SSN: {}'.format(gt, ssn))

                        tcap_reply = sk.recv(4096)
                    
                        if len(tcap_reply) > 0:
                            tcap_recv = unpack_from('!BBB', tcap_reply, offset=66)
                            if tcap_recv == (73,0,74):
                                print('\033[32m[+] {} Detected on GT:+{} ,SSN:{}\033[0m '.format(destination_ssn[ssn], str(gt), ssn))
                                table.add_row([str(gt), ssn, destination_ssn[ssn]])
                    except socket.timeout:
                        continue

        else:
            if len(dGT) % 2 == 0:
                dGT_len = len(unhexlify(''.join([dGT[x:x + 2][::-1] for x in range(0, len(dGT), 2)])))
                destination_GT = unhexlify(''.join([dGT[x:x + 2][::-1] for x in range(0, len(dGT), 2)]))
                
            else:
                dGT_len = len(dGT)
                dGT = dGT + '0'
                #dGT_len = len(unhexlify(''.join([dGT[x:x + 2][::-1] for x in range(0, len(dGT), 2)]))) & 0xf
                #print(len(unhexlify(''.join([dGT[x:x + 2][::-1] for x in range(0, len(dGT), 2)]))))
                destination_GT = unhexlify(''.join([dGT[x:x + 2][::-1] for x in range(0, len(dGT), 2)])) 
                

            for ssn in destination_ssn:
                try:
                    sccp_header = initSCCP(source_GT, destination_GT, ssn)
                    tcap_header = initTCAP()
                    sk.sendall(m3ua_header_data + sccp_header + tcap_header)
                    print('\033[34m[*]\033[0m Scanning +{} on SSN: {}'.format(dGT, ssn))
                    tcap_reply = sk.recv(4096)
                
                    if len(tcap_reply) > 0:
                        tcap_recv = unpack_from('!BBB', tcap_reply, offset=66)
                        if tcap_recv == (73,0,74):
                            print('\033[32m[+] {} Detected on GT:+{} ,SSN:{}\033[0m '.format(destination_ssn[ssn], dGT, ssn))
                            table.add_row([dGT, ssn, destination_ssn[ssn]])
                except socket.timeout:
                    continue

        print()
        print('\033[32m*** Detected GT ***\033[0m')
        print(table)

sk.close()
