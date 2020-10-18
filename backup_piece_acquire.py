while pieces_acquisition < total_pieces and client_no < len(peers_available) and piece_size_exceed == False:
		client_socket = peers_available[client_no]["socket"]
		j = 13
		lengt = j.to_bytes(4, "big")
		j = 6
		ids = j.to_bytes(1, "big")
		j = 0
		ind = index_piece.to_bytes(4, "big")
		beg = j.to_bytes(4, "big")
		leng = 0
		if index_piece == (total_pieces - 1):
			leng = last_piece_length.to_bytes(4, "big")
			expected = last_piece_length + 13
			print(f"Length = {last_piece_length}")
		else:
			leng = single_piece_len.to_bytes(4, "big")
			expected = single_piece_len + 13
			print(f"Length = {single_piece_len}")
		mess = lengt + ids + ind + beg + leng
		client_socket.send(mess)
		#expected = single_piece_len + 13
		try:
			res = client_socket.recv(8192)
		except:
			client_no += 1
			continue
		while len(res) < expected:
			re = client_socket.recv(8192)	
			res = res + re
		
		res = res[13: ]
		res_hash_val = hashlib.sha1(res).digest()
		if res_hash_val == index_pieces_acquired[index_piece]["info_hash"]:
			f.write(res)
			pieces_acquisition += 1
			index_piece += 1
			#print("The hash values of received piece matches with the original one")
			print(f"Piece {index_piece} with hashval = {res_hash_val} downloaded")
		else:
			print(f"Hash values aren't matching")
