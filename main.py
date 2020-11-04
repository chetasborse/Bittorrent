from collections import OrderedDict
from Decode import decode
from Encode import encode
from Tracker import convert_to_http, make_peer_id, convert_to_peers, escape
import subprocess, sys
from socket import *
import random
from struct import *
import threading
from subprocess import STDOUT, check_output
import time


from config import *
import config
from print_tor import print_torr
from tracker_contact import http_tracker_connect, udp_tracker_connect
from peers_contact import connect_to_peer


#to convert into hash values
import hashlib


#path = "/home/chetas/Desktop/ubuntu-20.04.1-desktop-amd64.iso.torrent"
path = "./torrent_files/trial.torrent"
#path = "/home/chetas/Desktop/sample.torrent"
#path = "/home/chetas/Desktop/amusementsinmath16713gut_archive.torrent"
#path = "/home/chetas/Desktop/big-buck-bunny.torrent"

# ____________________Part 1: Reading the torrent file____________________
f = open(path, "rb")
metainfo = f.read()
torrent, pos = decode(metainfo, 0)
# ____________________Part 1 ends here____________________

		
# ____________________Part 2: Converting the .torrent file into normal strings and storing the important values____________________		
for key, value in torrent.items():
	if type(value) == OrderedDict:
		info_hash = value
		for key1, value1 in value.items():
			if key1 == b'pieces':
				
				i = 0
				n = len(value1)
				while i < n:
					hashval = value1[i: i + 20]
					i += 20
					config.hash_code_list.append(hashval)
					config.index_pieces_acquired.append({"info_hash": hashval, "acquired": False})
					#print(hashval)
			elif key1 == b'files':
				is_file = False
				for lis in value1:
					for k, v in lis.items():
						if k == b'length':
							config.left = config.left + int(v)
			elif key1 == b'length':
				config.left = int(value1)
				#print(config.left)
			elif key1 == b'piece length':
				config.single_piece_len = value1
			elif key1 == b'name':
				file_name = value1.decode("utf-8")
	else:
		if key == b'announce-list':
			for trac in value:
				tracker1 = str(trac[0])
				n = len(tracker1)
				tracker1 = tracker1[2 : n-1]
				if tracker1[0] == "u":
					config.tracker_list.append({"trac": tracker1, "type": "udp"})
				elif tracker1[0] == "h":
					config.tracker_list.append({"trac": tracker1, "type": "http"})
		if key == b'announce':
			tracker = value.decode("utf-8")

config.total_pieces = int(config.left / config.single_piece_len) + 1
last_piece_length = config.left - (config.total_pieces - 1) * config.single_piece_len
print(f"Size: {config.left}, len: {config.single_piece_len}\ntot: {config.total_pieces}")

#creating an info hash for the file				
info_hash_bencode = encode(info_hash)
info_hash_sha1 = hashlib.sha1(info_hash_bencode).digest()
info_has = escape(info_hash_sha1)
#Creation ends here


#if there is no tracker list
if len(config.tracker_list) == 0:
	if tracker[0] == "u":
		config.tracker_list.append({"trac": tracker, "type": "udp"})
	elif tracker[0] == "h":
		config.tracker_list.append({"trac": tracker, "type": "http"})


#Print list of trackers	
print("Tracket-List:")
for t in config.tracker_list:
	print(t)
#Printing trackers ends here

#____________________Part 2 ends here____________________


#____________________Part 3: Http/ UDP request to the tracker is made here and list of peers is obtained____________________

tracker_thread_list = []

for tracker in config.tracker_list:
	if tracker["type"] == "http":
		httpreq = convert_to_http(tracker["trac"], info_has, peer_id, config.uploaded, config.downloaded, config.left, port)
		t1 = threading.Thread(target=http_tracker_connect, args=(tracker['trac'], httpreq, info_hash_sha1,))
		tracker_thread_list.append(t1)
		t1.setDaemon(True)
		t1.start()	
	else:
		t1 = threading.Thread(name="daemon", target=udp_tracker_connect, args=(tracker['trac'], info_hash_sha1,))
		tracker_thread_list.append(t1)
		t1.setDaemon(True)
		t1.start()	

for t in tracker_thread_list:
	t.join(10)
#____________________Part 3 ends here____________________


#Printing peers
print("Peer List")
for peer in config.peer_list:
	print(f"ip = {peer['ip']}\tport = {peer['port']}")
#Printing peers ends here


#____________________Part 4: Connecting to the peers, handshaking and requesting to unchoke____________________
peer_thread_list = []
print(f"\nInfo hash: {info_hash_sha1}\n")
message1 = (bytes(chr(19), 'utf-8') + bytes("BitTorrent protocol", 'utf-8') + bytes(8 * chr(0), "utf-8") + info_hash_sha1 + bytes(peer_id, "utf-8"));
print(f"\nHandshake Message: {message1}\n")

#This loop starts connect to peers thread		
for peer in config.peer_list:
	ip1 = peer["ip"]
	port1 = peer["port"]
	t1 = threading.Thread(name='daemon', target=connect_to_peer, args=(ip1, port1, message1, info_hash_sha1))
	peer_thread_list.append(t1)
	t1.setDaemon(True)
	t1.start()
	#t1.join(4)

#This loop waits for the connect_to_peers loop to join
for thr in peer_thread_list:
	thr.join(4)


#Sort the peers based on number of pieces they posses based for top 4 algorithm
def sor(peer):
	return peer['count']
config.peers_available.sort(key=sor, reverse=True)
#____________________Part 4 ends here____________________


print("\n Requesting begins \n")


#____________________Part 5: Requesting pieces from available peers____________________


if not is_file: #This function called when it is a multiple file system
	file_name = "temporary.txt"
f = open(file_name, "wb+")

sizes = 16384 #Block size in which the pieces need to be requested
config.index_pieces_acq = [0] * config.total_pieces #Stores currently available pieces. 1 being present and 0 being not acquired yet

###Functions for Part 5
#Acquire top 4 peers	
def keep_alive_thread():
	global peer_no
	start_peer_from = peer_no
	end_peer = len(config.peers_available)
	j = 0
	mess = j.to_bytes(1, "big")
	while peer_no != end_peer:
		start = peer_no
		for i in range(start, end_peer):
			soc = config.peers_available[i]["socket"]
			soc.send(mess)
		time.sleep(100)		
	print("Keep alive thread ends here")
	
def make_queues_for_top4(num_of_peers):
	top4_queue = []
	for i in range(0, num_of_peers):
		top4_queue.append([])
	return top4_queue
	
def download_pieces(lock ,peer, pos):
	global top4_queue
	global f
	global top4_peer_list
	global request_queue
	global index_pieces_acq
	global last_piece_len
	global sizes
	global pieces_acquisition
	client_change = False
	client_socket = peer["socket"]
	while True:
		#if len(top4_queue[0]) == 0:
		#	continue
		if len(request_queue) == 0:
			continue
		j = 13
		lengt = j.to_bytes(4, "big")
		j = 6
		ids = j.to_bytes(1, "big")
		offset = 0
		#index_piece = top4_queue[0].pop(0)
		lock.acquire()
		index_piece = -1
		#index_piece = request_queue.pop(0)
		for num in request_queue:
			if peer["bitpattern"][num] == "1":
				index_piece = num
				request_queue.remove(num)
				break
		lock.release()
		if index_piece == -1:
			client_change = True
			break
		#print(f"Packet no. {index_piece} started")
		ind = index_piece.to_bytes(4, "big")
		beg = offset.to_bytes(4, "big")
		leng = 0
		if index_piece == (config.total_pieces - 1):
			leng = last_piece_length
			#print(f"Length = {last_piece_length}")
		else:
			leng = config.single_piece_len
			#print(f"Length = {config.single_piece_len}")
		block =  sizes
		fix_len = block.to_bytes(4, "big")
		#rem = leng % fix_len
		tot = leng
		#expected = leng + 13
		res = b''
		test = []
		while offset < leng:
			expected = block + 13
			#print(f"offset = {offset}")
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
			#expected = fix_len + 13
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
					"""	
					if preff < 9:
						r = r[preff + 4:]
						preff = unpack(">I", r[0: 4])[0]
					elif preff > 9:
						preff2 = unpack("B", r[4: 5])[0]
						if preff2 != 7:
							r = r[preff + 4: ]
						preff = unpack(">I", r[0: 4])[0]
					"""
						
				#print(f"Message received: {r}\n")
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
		#print(f"Message len: {len(res)}")
		if client_change:
			#continue
			lock.acquire()
			request_queue.insert(0, num)
			lock.release()
			break
		res_hash_val = hashlib.sha1(res).digest()
		if res_hash_val == config.index_pieces_acquired[index_piece]["info_hash"]:
			#piece_array.append(res)
			#f.write(res)
			
			#index_piece += 1
			offset = 0
			print(f"Message len: {len(res)}\nPiece {index_piece} with hashval = {res_hash_val} downloaded from {peer['ip']}\n")
			lock.acquire()
			config.index_pieces_acquired[index_piece]["acquired"] = True
			index_pieces_acq[index_piece] = 1
			temp_list = index_pieces_acq[0 : index_piece]
			coun = temp_list.count(1)
			total_offset = coun * single_piece_len
			f.seek(total_offset, 0)
			rem_piece = f.read()
			f.seek(total_offset, 0)
			f.write(res)
			f.write(rem_piece)
			pieces_acquisition += 1
			#Code for writing to the file
			#Code ends here
			lock.release()
		else:
			print(f"Message len: {len(res)}\nHash values aren't matching\nMessage: {r}")
			for b in test:
				print(f"----->{b[0: 20]}")
			lock.acquire()
			request_queue.insert(0, num)
			lock.release()
	if client_change:
		client_socket.close()
		lock.acquire()
		if peer in top4_peer_list:
			top4_peer_list.remove(peer) #Remove the peer from top4 if it closes the connection
		lock.release()
	

def set_top_4():
	global top4_peer_list, peer_no, pieces_acquisition
	top4_pos = 0
	while pieces_acquisition < config.total_pieces:
		if len(top4_peer_list) < 4 and peer_no < len(config.peers_available):
			while len(top4_peer_list) < 4 and peer_no < len(config.peers_available):
				lock = threading.Lock()
				t = threading.Thread(target = download_pieces, args=(lock, config.peers_available[peer_no], 0))
				t.start()
				#top4_peer_list.append({"thread": t, "peers": config.peers_available[peer_no]})
				#config.peers_available[peer_no]["pos"] = top4_pos
				top4_peer_list.append(config.peers_available[peer_no])
				top4_pos += 1
				peer_no += 1
		else:
			time.sleep(10)
			
###Functions for Part 5 end here

peer_no = 0
for start_piece_no in range(0, config.total_pieces):
	request_queue.append(start_piece_no)

print(request_queue)
	
##top4_thread = threading.Thread(target=set_top_4)
##top4_thread.start()

#Only demo delete later
top4_pos = 0
while pieces_acquisition < config.total_pieces:
		if len(top4_peer_list) < 4 and peer_no < len(config.peers_available):
			while len(top4_peer_list) < 4 and peer_no < len(config.peers_available):
				lock = threading.Lock()
				top4_peer_list.append(config.peers_available[peer_no])
				t = threading.Thread(target = download_pieces, args=(lock, config.peers_available[peer_no], 0))
				t.start()
				#top4_peer_list.append({"thread": t, "peers": config.peers_available[peer_no]})
				#confif.peers_available[peer_no]["pos"] = top4_pos
				top4_pos += 1
				print(f"\nPeer number is {peer_no}\n")
				peer_no += 1
		else:
			time.sleep(10)

#demo ends here

#set_top_4()
keep_alive = threading.Thread(target = keep_alive_thread)
#top4_queue = make_queues_for_top4(len(top4_peer_list))


start_piece_no = 0 #piece from which to start downloading
#increment_in_pieces = len(top4_peer_list)

#for thr in top4_peer_list:
#	t11 = threading.Thread(target = download_pieces, args=(thr, 0))
#	t11.start()

#while pieces_acquisition < config.total_pieces:

	
##top4_thread.join()
for i in range(0, config.total_pieces):
	print(f"{i}: {config.index_pieces_acquired[i]['acquired']}")

#____________________Part 5 ends here____________________

#____________________Part 6 Seeding peers____________________



#____________________Part 6 ends here____________________


print("\nPeers with bitpattern\n")
for peer in config.peers_available:
	cli_soc = peer["socket"]
	cli_soc.close()
	for key, val in peer.items():
		print(f"{key}: {val}")
	#print(f"ip: {peer['ip']}\nport: {peer['port']}\nlen: {len(peer['bitpattern'])}\n rate: {peer['rate']}")
	print("\n")
	
"""
print("\nPeers with bitpattern\n")
for peer in config.peers_available:
	cli_soc = peer["socket"]
	cli_soc.close()
	for key, val in peer.items():
		print(f"{key}: {val}")
	#print(f"ip: {peer['ip']}\nport: {peer['port']}\nlen: {len(peer['bitpattern'])}\n rate: {peer['rate']}")
	print("\n")
"""
print("Done")	

f.close()
	
#Connecting to peers ends here

#torrent_socket.close()

