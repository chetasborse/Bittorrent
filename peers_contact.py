from socket import *
from config import *
import config
from struct import *
import time

#In this function I have connected to peers -> sent handshake message -> asked to unchoke me -> add them to the list of available peers if they unchoke else close the connection

def connect_to_peer(ip, port, message1, info_hash_sha1):
	bitfield = b''
	handshake_completed = False # Sees that we get the bitpattern from the remote peer successfully
	choke = True #Sees if the peer has choked us
	pres = True # Sees if connection to remote peer is successfull
	try: 
		client_socket = socket(AF_INET, SOCK_STREAM)
		have_pieces = []
		end_point = 0 #Where the bitfield message ends
		total_time_needed = 0
		total_data_trans = 0
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
				time1 = time.time()
				Response = client_socket.recv(4096)
				time2 = time.time()
				total_time_needed += time2 - time1
				total_data_trans += len(Response)
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
								time1 = time.time()
								res = client_socket.recv(4096)
								time2 = time.time()
								total_time_needed += time2 - time1
								total_data_trans += len(res)
								leng = unpack(">I", res[0: 4])
								ids1 = unpack("b", res[4: 5])
								if ids1[0] != 5:
									res = res[leng[0] + 4:]
									leng = unpack(">I", res[0: 4])
								handshake_len += 4 + leng[0]
								Response = Response + res
								while len(Response) < handshake_len:
									time1 = time.time()
									res = client_socket.recv(4096)
									time2 = time.time()
									total_time_needed += time2 - time1
									total_data_trans += len(res)
									Response = Response + res
								handshake_completed = True
								end_point = hand1 + leng[0] + 4
								bitfield = Response[hand1 + 5: end_point]
								while end_point < len(Response): #This checks the have messages
									leng = unpack(">I", Response[end_point: end_point + 4])[0]
									if end_point + leng + 4 > len(Response):
										try:
											time1 = time.time()
											res = client_socket.recv(4096)
											time2 = time.time()
											total_time_needed += time2 - time1
											total_data_trans += len(res)
											Response += res
										except:
											break	
									id = unpack("b", Response[end_point + 4: end_point + 5])[0]
									if id != 4:
										break
									piece = unpack(">I", Response[end_point + 5: end_point + 9])[0]
									have_pieces.append(piece)
									end_point = end_point + 9
									handshake_len = end_point							
							elif len(Response) > handshake_len:
								leng = unpack(">I", Response[handshake_len: handshake_len + 4])
								handshake_len += 4 + leng[0]
								while len(Response) < handshake_len:
									time1 = time.time()
									res = client_socket.recv(4096)
									time2 = time.time()
									total_time_needed += time2 - time1
									total_data_trans += len(res)
									Response = Response + res
								end_point = hand1 + leng[0] + 4
								bitfield = Response[hand1 + 5: end_point]
								handshake_completed = True
								while end_point < len(Response): #This checks the have messages
									leng = unpack(">I", Response[end_point: end_point + 4])[0]
									if end_point + leng + 4 > len(Response):
										try:
											time1 = time.time()
											res = client_socket.recv(4096)
											time2 = time.time()
											total_time_needed += time2 - time1
											total_data_trans += len(res)
											Response += res
										except:
											break	
									id = unpack("b", Response[end_point + 4: end_point + 5])[0]
									if id != 4:
										break
									piece = unpack(">I", Response[end_point + 5: end_point + 9])[0]
									have_pieces.append(piece)
									end_point = end_point + 9
									handshake_len = end_point
							if len(Response) > handshake_len:
								leng = unpack(">I", Response[handshake_len: handshake_len + 4])
								if leng[0] == 1:
									id1 = unpack("b", Response[handshake_len: handshake_len + 1])
									if id1[0] == 1:
										choke = False
							#print(f"Message: {Response}")
						except:
							handshake_completed = False

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
			while len(have_pieces) > 0:
				ind = have_pieces.pop(0)
				part1 = h[0: ind]
				part2 = h[ind + 1: len(h)]
				h = part1 + "1" + part2
			rate = total_data_trans / total_time_needed
			config.peers_available.append({"ip": ip, "port": port, "choke": choke, "socket" : client_socket, "bitpattern": h, "rate": rate})
			# print(f"\nip: {ip}, \nchoke = {choke}\nrate = {rate}\nbitpattern: {h}\n")
		else:	
			client_socket.close()
	except:
		pass
