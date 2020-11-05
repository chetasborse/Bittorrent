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
from tracker_contact import http_tracker_connect, udp_tracker_connect, get_the_peers
from peers_contact import connect_to_peer
from download_pieces import download_pieces, keep_alive_thread
from write import write_to_file
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
				config.is_file = False
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
				config.file_name = value1.decode("utf-8")
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
config.last_piece_len = config.left - (config.total_pieces - 1) * config.single_piece_len
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

get_the_peers(info_has, peer_id, port, info_hash_sha1)
#____________________Part 3 ends here____________________


#Printing peers
print("Peer List")
for peer in config.peer_list:
	print(f"ip = {peer['ip']}\tport = {peer['port']}")
#Printing peers ends here


#____________________Part 4: Connecting to the peers, handshaking____________________
peer_thread_list = []
message1 = (bytes(chr(19), 'utf-8') + bytes("BitTorrent protocol", 'utf-8') + bytes(8 * chr(0), "utf-8") + info_hash_sha1 + bytes(peer_id, "utf-8"));

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


#Sort the peers based on their rate of data transfer
def sor(peer):
	return peer['rate']
config.peers_available.sort(key=sor)
#____________________Part 4 ends here____________________


print("\n Requesting begins \n")
print(f"Available peers: {len(config.peers_available)}\n")

if len(peers_available) == 0:
	print("\nNo peers found\n")
	sys.exit()


#____________________Part 5: Requesting pieces from available peers____________________


config.index_pieces_acq = [0] * config.total_pieces #Stores currently available pieces. 1 being present and 0 being not acquired yet
print(f"\nindex_pieces_acquired = {config.index_pieces_acq}\n")


for start_piece_no in range(0, config.total_pieces):
	config.request_queue.append(start_piece_no)

print(config.request_queue)


top4_pos = 0
download_complete = False
keep_alive_thread_started = False
peer_deplete = False
while True:
	while len(config.top4_peer_list) < 4 and config.peer_no < len(config.peers_available):
		lock = threading.Lock()
		config.top4_peer_list.append(config.peers_available[config.peer_no])
		t = threading.Thread(target = download_pieces, args=(lock, config.peers_available[config.peer_no],))
		t.setDaemon(True)
		t.start()
		#top4_peer_list.append({"thread": t, "peers": config.peers_available[peer_no]})
		#config.peers_available[peer_no]["pos"] = top4_pos
		top4_pos += 1
		print(f"\nPeer number is {config.peer_no}\n")
		config.peer_no += 1
	if config.pieces_acquisition == config.total_pieces:
		print("Peers depleted")
		download_complete = True
		break
	# if config.peer_no + 1 == len(config.peers_available):
	# 		peer_deplete = True
	# 		break
	if keep_alive_thread_started == False:
		keep_alive_thread_started = True
		keep_alive = threading.Thread(target = keep_alive_thread)
		lock = threading.Lock()
		write_fil = threading.Thread(target = write_to_file, args = (lock,))
		write_fil.setDaemon("True")
		keep_alive.setDaemon("True")
		write_fil.start()
		keep_alive.start()
	time.sleep(5)

	
for i in range(0, config.total_pieces):
	print(f"{i}: {config.index_pieces_acquired[i]['acquired']}")

#____________________Part 5 ends here____________________

#____________________Part 6 Seeding peers____________________



#____________________Part 6 ends here____________________


# print("\nPeers with bitpattern\n")
# for peer in config.peers_available:
# 	cli_soc = peer["socket"]
# 	cli_soc.close()
# 	for key, val in peer.items():
# 		print(f"{key}: {val}")
# 	#print(f"ip: {peer['ip']}\nport: {peer['port']}\nlen: {len(peer['bitpattern'])}\n rate: {peer['rate']}")
# 	print("\n")
	
print("Done")	

f.close()
	
#Connecting to peers ends here

#torrent_socket.close()

