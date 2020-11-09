import config
from struct import *
import hashlib
import time

def download_pieces(lock ,peer):
	last_piece_len = config.last_piece_len
	sizes = config.sizes
	choked = True
	client_change = False
	got_response = False #Tells if unchoked message was sent
	client_socket = peer["socket"]
	if peer["choke"] == True:
		j = 1
		leng = j.to_bytes(4, "big")
		j = 2
		interested = j.to_bytes(1, "big")
		message = leng + interested
		
		try:
			client_socket.send(message)
			Response = client_socket.recv(1024)
			if Response == b'\x00\x00\x00\x01\x01':
				peer["choke"] = False
				choked = False
			else:
				end_point = 0
				have_pieces = [] 
				while end_point < len(Response): #This checks the have messages
					leng = unpack(">I", Response[end_point: end_point + 4])[0]
					if end_point + leng + 4 > len(Response):
						try:
							res = client_socket.recv(4096)
							Response += res
						except:
							break	
					id = unpack("b", Response[end_point + 4: end_point + 5])[0]
					if id != 4:
						if id == 1:
							peer["choke"] = False
							choked = False
						break
					piece = unpack(">I", Response[end_point + 5: end_point + 9])[0]
					have_pieces.append(piece)
					end_point = end_point + 9
				
				if len(have_pieces) != 0:
					h = peer["bitpattern"]
					while len(have_pieces) > 0:
						ind = have_pieces.pop(0)
						part1 = h[0: ind]
						part2 = h[ind + 1: len(h)]
						h = part1 + "1" + part2
					peer["bitpattern"] = h
				
			print(f"\nMessage on interested: {Response}\n")
		except Exception as e:
			print(f"Error: {e}\n")
			pass
	else:
		choked = False
	if choked == False: 
		while True:
			if len(config.request_queue) == 0:
				continue
			j = 13
			lengt = j.to_bytes(4, "big")
			j = 6
			ids = j.to_bytes(1, "big")
			offset = 0
			lock.acquire()
			index_piece = -1
			for num in config.request_queue:
				if peer["bitpattern"][num] == "1":
					index_piece = num
					config.request_queue.remove(num)
					break
			lock.release()
			if index_piece == -1:
				client_change = True
				break
			ind = index_piece.to_bytes(4, "big")
			beg = offset.to_bytes(4, "big")
			leng = 0
			if index_piece == (config.total_pieces - 1):
				leng = config.last_piece_len
			else:
				leng = config.single_piece_len
			block =  sizes
			fix_len = block.to_bytes(4, "big")
			tot = leng
			res = b''
			test = []
			while offset < leng:
				expected = block + 13
				if leng - offset < sizes:
					last = leng - offset
					fix_len = last.to_bytes(4, "big")
					expected = last + 13
				beg = offset.to_bytes(4, "big")
				mess = lengt + ids + ind + beg + fix_len
				try:
					client_socket.send(mess)
				except:
					client_change = True
					break
				try:
					r = client_socket.recv(8192)
					preff = unpack(">I", r[0: 4])[0]
					while len(r) > 0:
						idd = unpack("B", r[4: 5])[0]
						if preff == 0:
							r = r[preff + 4:]
							preff = unpack(">I", r[0: 4])[0]				
						elif idd == 7:
							break
						else:
							r = r[preff + 5:]
							preff = unpack(">I", r[0: 4])[0]		
					if len(r) == 0:
						client_no += 1
						print("Client changed")
						client_change = True
						break
				except:
					client_change = True
					break
				while len(r) < expected:
					re = client_socket.recv(8192)
					r = r + re
				res += r[13: preff + 4]
				test.append(r)
				offset += block
			if client_change:
				lock.acquire()
				config.request_queue.insert(0, num)
				lock.release()
				break
			res_hash_val = hashlib.sha1(res).digest()
			if res_hash_val == config.index_pieces_acquired[index_piece]["info_hash"]:
				offset = 0
				config.pieces_acquisition += 1
				per = config.pieces_acquisition * 100 / config.total_pieces
				print(f"\nPiece with hashval = {res_hash_val} downloaded from {peer['ip']}\nProgress: {round(per, 2)}%\n")
				lock.acquire()
				config.index_pieces_acquired[index_piece]["acquired"] = True
				config.index_pieces_acq[index_piece] = 1
				config.write_buffer.append({"index": index_piece, "piece": res})
				lock.release()
			else:
				print(f"Message len: {len(res)}\nHash values aren't matching\nMessage: {r}")
				for b in test:
					print(f"----->{b[0: 20]}")
				lock.acquire()
				config.request_queue.insert(0, num)
				lock.release()
	else:
		client_change = True


	if client_change:
		client_socket.close()
		lock.acquire()
		for i in range(len(config.top4_peer_list)):
			if config.top4_peer_list[i]['ip'] == peer["ip"] and config.top4_peer_list[i]['port'] == peer["port"]: #Remove the peer from top4 if it closes the connection
				del config.top4_peer_list[i]
				break
		lock.release()

def keep_alive_thread():
	start_peer_from = config.peer_no
	end_peer = len(config.peers_available)
	j = 0
	mess = j.to_bytes(1, "big")
	while config.peer_no != end_peer:
		start = config.peer_no
		for i in range(start, end_peer):
			soc = config.peers_available[i]["socket"]
			soc.send(mess)
		time.sleep(100)		
	print("Keep alive thread ends here")

def sor(pieces):
	return pieces['freq']

def set_rarest_first():
	pieces_freq = []
	for pie in range(config.total_pieces):
		item = dict()
		item["index"] = pie
		item["freq"] = 0
		pieces_freq.append(item)
	
	for peer in config.peers_available:
		for i, ch in enumerate(peer["bitpattern"]):
			if ch == "1":
				pieces_freq[i]["freq"] += 1

	pieces_freq.sort(key=sor)

	for pie in pieces_freq:
		config.request_queue.append(pie["index"])
	

	
