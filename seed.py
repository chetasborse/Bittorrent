from socket import *
from struct import *
import config
import threading

def send_piece(client, index, begin, length, f, lock):
    offset = index * config.single_piece_len
    offset += begin
    lock.acquire()
    f.seek(offset)
    block = f.read(length)
    lock.release()
    mess_len = 9 + length
    mess_len = mess_len.to_bytes(4, "big")
    mess_id = (7).to_bytes(1, "big")
    mess_index = index.to_bytes(4, "big")
    mess_begin = begin.to_bytes(4, "big")
    message = mess_len + mess_id + mess_index + mess_begin + block
    client.send(message)
    

def seed(client, message1):
    data = client.recv(2048)
    peer_choked = True
    peer_interested = False
    pstr_len = unpack("b", data[0:1])[0]
    pstr_len += 8
    peer_info_hash = data[pstr_len + 1: pstr_len + 21]
    peer_peer_id = data[pstr_len + 21: pstr_len + 41]
    pieces_available = [1] * config.total_pieces #All pieces set to 1 as we start seeding once we have all the pieces
    f = ''
    if config.is_file:
        f = config.single_f
    else:
        f = config

    #Code to convert bitpattern to bitfield
    bitpattern = "1" * config.total_pieces 
    addi = 8 - len(bitpattern) % 8
    bitpattern = bitpattern + "0" * addi
    bitpattern = hex(int(bitpattern, 2))
    bitpattern = bitpattern[2: len(bitpattern)]
    bitpattern = bytes.fromhex(bitpattern)
    bitfield_len = len(bitpattern) + 1
    bitpattern_len = bitfield_len.to_bytes(4, "big")
    bitfield_id = (5).to_bytes(1, "big")
    bitfield = bitpattern_len + bitfield_id + bitpattern
    #ends

    if config.info_hash != peer_info_hash:
        client.close() #Closing connection if info hash don't match
    else:
        try:
            client.send(message1) #Sends handshake back
            client.send(bitfield) #Sends bitfield
            while peer_choked:
                data = client.recv() #Expects interested message and unchokes
                peer_interested = True
                if len(data) >= 5:
                    if data[0: 5] == b'\x00\x00\x00\x01\x02':
                        peer_choked = False
                        unchoke_mess = b'\x00\x00\x00\x01\x01'
                        client.send(unchoke_mess)

            while peer_interested:
                start = 0
                request = client.recv(1024)
                if len(request) == 0:
                	break
                while start < len(request):
                    if len(request) - start < 17:
                        res = client.recv(1024)
                        request += res
                    id = unpack("B", request[start + 4: start + 5])[0]
                    if id != 6:
                        start += 5
                        continue
                    index = unpack(">I", request[start + 5: start + 9])[0]
                    if index >= config.total_pieces:
                        start += 17
                        continue
                    begin = unpack(">I", request[start + 9: start + 13])[0]
                    length = unpack(">I", request[start + 13: start + 17])[0]
                    lock = threading.Lock()
                    send_piece_thread = threading.Thread(name = "send thread", target = send_piece, args = (client, index, begin, length, f, lock,))
                    send_piece_thread.setDaemon(True)
                    send_piece_thread.start()
                    send_piece_thread.join(5)
                    start += 17
        except:
            client.close()




