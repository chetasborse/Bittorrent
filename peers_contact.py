from socket import *
from config import *
import config
from struct import *

#In this function I have connected to peers -> sent handshake message -> asked to unchoke me -> add them to the list of available peers if they unchoke else close the connection

def connect_to_peer(ip, port, message1, info_hash_sha1):
	global peers_available
	bitfield = b''
	handshake_completed = False # Sees that we get the bitpattern from the remote peer successfully
	choke = True #Sees if the peer has choked us
	pres = True # Sees if connection to remote peer is successfull
	client_socket = socket(AF_INET, SOCK_STREAM)
	try:
		client_socket.connect((ip, int(port)))
	except:
		pres = False
		config.peer_list.remove({"ip": ip, "port": port})
	if pres:
		print(f"Connected to peer {ip}")
		connect = True # Sees if we get a response from peer after connection
		client_socket.send(message1)
		try:
			Response = client_socket.recv(4096)
		except:
			connect = False
			config.peer_list.remove({"ip": ip, "port": port})
		if connect:
			if len(Response) != 0:
				pstrlen = unpack("B", Response[0: 1])[0]
				nu = 9 + pstrlen
				info_hash_rep = Response[nu: nu + 20]
				if info_hash_rep == info_hash_sha1:
					#print(f"\nFrom: {ip}\nMessage1: {Response}\nLength: {len(Response)}\n")
					bitfield = b''
					handshake_len = pstrlen + 49
					hand1 = handshake_len
					try:
						if len(Response) == handshake_len:
							res = client_socket.recv(4096)
							leng = unpack(">I", res[0: 4])
							ids1 = unpack("b", res[4: 5])
							if ids1[0] != 5:
								res = res[leng[0] + 4:]
								leng = unpack(">I", res[0: 4])
							handshake_len += 4 + leng[0]
							Response = Response + res
							while len(Response) < handshake_len:
								res = client_socket.recv(4096)
								Response = Response + res
							handshake_completed = True
							bitfield = Response[hand1 + 5: hand1 + leng[0] + 4]
						elif len(Response) > handshake_len:
							leng = unpack(">I", Response[handshake_len: handshake_len + 4])
							handshake_len += 4 + leng[0]
							while len(Response) < handshake_len:
								res = client_socket.recv(4096)
								Response = Response + res
							bitfield = Response[hand1 + 5: hand1 + leng[0] + 4]
							handshake_completed = True
						if len(Response) > handshake_len:
							leng = unpack(">I", Response[handshake_len: handshake_len + 4])
							if leng[0] == 1:
								id1 = unpack("b", Response[handshake_len: handshake_len + 1])
								if id1[0] == 1:
									choke = False
					except:
						handshake_completed = False
	if handshake_completed and choke:
		message = b''
		j = 1
		leng = j.to_bytes(4, "big")
		j = 2
		interested = j.to_bytes(1, "big")
		message = leng + interested
		client_socket.send(message)
		try:
			res = client_socket.recv(1024)
			#print(f"\nFrom: {ip}\nMessage1: {Response}\nMessage2: {res}\n")
			if res == b'\x00\x00\x00\x01\x01':
				choke = False 
		except:
			handshake_completed = False
			#To throw away the peer not connecting with us
	
	if handshake_completed:
		h = bitfield.hex()
		h = bin(int(h, 16))
		h = h[2: ]
		if len(h) > config.total_pieces:
			h = h[0: config.total_pieces]
		elif len(h) < config.total_pieces:
			needed = config.total_pieces - len(h)
			pref = "0" * needed
			h = pref + h
		config.peers_available.append({"ip": ip, "port": port, "choke": choke, "socket" : client_socket, "bitpattern": h, "count": h.count("1")})
	else:	
		client_socket.close()
