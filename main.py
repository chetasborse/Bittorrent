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
from download_pieces import download_pieces, keep_alive_thread, set_rarest_first
from write import write_to_file, write_to_multifile
from seed import seed
#to convert into hash values
import hashlib
import os


#path = "/home/chetas/Desktop/Python All-In-One for Dummies.f60e849f18020861.torrent"
#path = "/home/chetas/Desktop/ubuntu-20.04.1-desktop-amd64.iso.torrent"
path = "./torrent_files/t1.torrent"

#path = "/home/chetas/Desktop/t3.torrent"
#path = "/home/chetas/Desktop/[KiruaSubs] Yesterday wo Utatte - Extra 06.ass.torrent"
#path = "/home/chetas/Desktop/big-buck-bunny.torrent"

# ____________________Part 1: Reading the torrent file and create Downloads folder____________________

f = open(path, "rb")
metainfo = f.read()
torrent, pos = decode(metainfo, 0)

#Creates downloads folder if not present
directory = "Downloads"
cwd = os.getcwd()
path = os.path.join(cwd, directory)
try:
	os.mkdir(path)
except FileExistsError:
	pass

config.download_path = path

seeding_enabled = True
seeding_socket = socket(AF_INET, SOCK_STREAM)
try:
	seeding_socket.bind(('', config.port))
	seeding_socket.listen(5) #Limit set to 5 
	print("\nSeeding socket enabled\n")
except:
	seeding_enabled = False

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
					fold = dict()
					for k, v in lis.items():
						if k == b'length':
							fold["length"] = int(v)
							config.left = config.left + int(v)
						if k == b'path':
							fold["file_name"] = v[len(v) - 1].decode("utf-8")
							p = ''
							for i in range(len(v) - 1):
								p += f'/{v[i].decode("utf-8")}'
							fold["path"] = p
					config.folder_dets.append(fold)
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
# config.file_size = (config.total_pieces - 1) * config.single_piece_len + config.last_piece_len
config.file_size = config.total_pieces * config.single_piece_len

#creating an info hash for the file				
info_hash_bencode = encode(info_hash)
info_hash_sha1 = hashlib.sha1(info_hash_bencode).digest()
config.info_hash = info_hash_sha1
info_has = escape(info_hash_sha1)
#Creation ends here
print(f'infoHash: {info_hash_sha1}\n')
config.global_tracker_list = config.tracker_list		

#____________________Part 2 ends here____________________


#____________________Part 3: Http/ UDP request to the tracker is made here and list of peers is obtained____________________


#if there is no tracker list then use the tracker mentioned in announce
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

get_the_peers(info_has, peer_id, port, info_hash_sha1)
#____________________Part 3 ends here____________________


#Printing peers
print("Peer List")
for peer in config.peer_list:
	print(f"ip = {peer['ip']}\tport = {peer['port']}")
#Printing peers ends here


#config.peer_list = [] #For seeding locally
#config.peer_list = [{"ip": '127.0.0.3', "port": 7000}]


#____________________Part 4: Connecting to the peers, handshaking____________________
peer_thread_list = []
message1 = (bytes(chr(19), 'utf-8') + bytes("BitTorrent protocol", 'utf-8') + bytes(8 * chr(0), "utf-8") + info_hash_sha1 + bytes(peer_id, "utf-8"));
config.peers_available = []
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


#Sort the peers based on their rate of data transfer for top4
def sor(peer):
	return peer['rate']
config.peers_available.sort(key=sor)
#____________________Part 4 ends here____________________


print("\n Requesting begins \n")
print(f"Available peers: {len(config.peers_available)}\n")

if len(config.peers_available) == 0:
	print("\nNo peers found\n")
	sys.exit()

set_rarest_first()

#____________________Part 5: Requesting pieces from available peers with top 4 at a time based on rate of download____________________


config.index_pieces_acq = [0] * config.total_pieces #Stores currently available pieces. 1 being present and 0 being not acquired yet

top4_pos = 0
download_complete = False
keep_alive_thread_started = False
peer_deplete = False

while True:

	if len(config.top4_peer_list) == 0 and config.peer_no == len(config.peers_available): #This part requests for more peers if peers get depleted
		print("Connecting to trackers again\n")
		status = get_the_peers(info_has, peer_id, port, info_hash_sha1)
		if not status:
			try: #Here connection to the tracket is made again if the peers provided by all the trackers deplete
				print("\nContact to trackers made again\n")
				peer_id = make_peer_id()
				config.tracker_list = config.global_tracker_list
				if len(config.tracker_list) == 0:
					if tracker[0] == "u":
						config.tracker_list.append({"trac": tracker, "type": "udp"})
					elif tracker[0] == "h":
						config.tracker_list.append({"trac": tracker, "type": "http"})
			except:
				print("Peers depleted")
				break
		#else:
		peer_thread_list = []
		message1 = (bytes(chr(19), 'utf-8') + bytes("BitTorrent protocol", 'utf-8') + bytes(8 * chr(0), "utf-8") + info_hash_sha1 + bytes(peer_id, "utf-8"));
		config.peers_available = []	
		for peer in config.peer_list:
			ip1 = peer["ip"]
			port1 = peer["port"]
			t1 = threading.Thread(name='daemon', target=connect_to_peer, args=(ip1, port1, message1, info_hash_sha1))
			peer_thread_list.append(t1)
			t1.setDaemon(True)
			t1.start()
		for thr in peer_thread_list:
			thr.join(4)
		if len(config.peers_available) == 0:
			print("No peers found")
			break
		config.peers_available.sort(key=sor)
		keep_alive_thread_started = False
		peer_deplete = False
		config.peer_no = 0

	while len(config.top4_peer_list) < 4 and config.peer_no < len(config.peers_available): #This loop maintains 4 peers at a time
		lock = threading.Lock()
		config.top4_peer_list.append(config.peers_available[config.peer_no])
		t = threading.Thread(target = download_pieces, args=(lock, config.peers_available[config.peer_no],))
		t.setDaemon(True)
		t.start()
		top4_pos += 1
		print(f"\nPeer number is {config.peer_no}\n")
		config.peer_no += 1
	
	if config.pieces_acquisition == config.total_pieces: 
		print("Download complete")
		download_complete = True
		break

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


if not config.is_file:
	write_to_multifile()

#____________________Part 5 ends here____________________

#____________________Part 6 Seeding peers____________________


if seeding_enabled:

	res = input("\nDo you want to seed? (Y / N)")
	if res.lower() == n:
		if config.is_file:
			config.single_f.close()
		else:
			config.f.close()
			if os.path.exists("temporary"):
                os.remove("temporary")
	else:
		sys.exit()

	#Notifying the trackers that we have completed the download process
	config.tracker_list = config.global_tracker_list
	if len(config.tracker_list) == 0:
		if tracker[0] == "u":
			config.tracker_list.append({"trac": tracker, "type": "udp"})
		elif tracker[0] == "h":
			config.tracker_list.append({"trac": tracker, "type": "http"})
	print("Notified tracker successfully")
	#Notifying ends here

	seeding_peer_threads = []
	print("Waiting to connect to a seeder")
	try:
		while True:
			client, address = seeding_socket.accept()
			print(f"\nConnection established with peer with id {address[0]} at port {address[1]}")
			# seed_thread = threading.Thread(name = "seed_thread", target = seed, args= (client, message1, ))
			seed_thread = threading.Thread(name = "seed_thread", target = seed, args= (client, message1, ))
			seed_thread.start()
			seeding_peer_threads.append(seed_thread)
	except KeyboardInterrupt:
		print("\nSeeding stopped\n")

	
	seeding_socket.close()

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


