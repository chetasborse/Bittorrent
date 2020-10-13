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

#to convert into hash values
import hashlib


#path = "/home/chetas/Desktop/ubuntu-20.04.1-desktop-amd64.iso.torrent"
path = "/home/chetas/Desktop/t1.torrent"
#path = "/home/chetas/Desktop/vidmate_201912_archive.torrent"
#path = "/home/chetas/Desktop/amusementsinmath16713gut_archive.torrent"

f = open(path, "rb")
metainfo = f.read()
#print(type(metainfo))
torrent, pos = decode(metainfo, 0)

tracker = ""
hash_code_list = []
uploaded = 0
downloaded = 0
left = 0
peer_id = make_peer_id()
port = 6889
info_hash = ''
is_file = True
single_piece_len = 0
peer_list = []
available_peers = []
tracker_list = []



#To print metainfo file
for key, value in torrent.items():
	if type(value) == OrderedDict:
		print(f"key: {key}")
		print("OrderedDict2")
		for key1, value1 in value.items():
			if key1 == b'files':
				print(f"{key1}=>{value1}\n")
			#elif key1 == b'pieces':
			#	print(f"{key1}=>\n\t{value1}")
			else:
				print(f"{key1}")
	else:
		print(f"{key}=>{value}\n")
#Printing part ends here

		
		
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
					hash_code_list.append(hashval)
					#print(hashval)
			elif key1 == b'files':
				is_file = False
				for lis in value1:
					for k, v in lis.items():
						if k == b'length':
							left = left + int(v)
			elif key1 == b'length':
				left = int(value1)
				#print(left)
			elif key1 == b'piece length':
				single_piece_len = value1
	else:
		if key == b'announce-list':
			for trac in value:
				tracker1 = str(trac[0])
				n = len(tracker1)
				tracker1 = tracker1[2 : n-1]
				if tracker1[0] == "u":
					tracker_list.append({"trac": tracker1, "type": "udp"})
				elif tracker1[0] == "h":
					tracker_list.append({"trac": tracker1, "type": "http"})


print(f"Size: {left}, len: {single_piece_len}\ntot: {left / single_piece_len}")


#creating an info hash for the file				
info_hash_bencode = encode(info_hash)
info_hash_sha1 = hashlib.sha1(info_hash_bencode).digest()
info_has = escape(info_hash_sha1)
#Creation ends here


#Print list of trackers
print("Tracket-List:")
for t in tracker_list:
	print(t)
#Printing trackers ends here


#Http/ UDP request to the tracker is made here and list of peers is obtained
tracker_thread_list = []

def http_tracker_connect(tracker, httpreq):
	global peer_list
	connect = True
	#print(httpreq)
	try:
		#data = subprocess.Popen(['wget', '-O', '-', httpreq], stdout=subprocess.PIPE).communicate()[0].strip()
		data = check_output(['wget', '-O', '-', httpreq], timeout=10)
	except:
		print(f"\nUnable to connect to the tracker {tracker}\n")
		connect = False
	if connect and len(data) != 0:
		print(f"\n\nConnected to tracker {tracker}\n\n")
		t, pos = decode(data, 0)
		for key, val in t.items():
			if key == b'peers':
				peer_list1 = convert_to_peers(val)
				peer_list += peer_list1		
	
	
def udp_tracker_connect(tracker):
	global peer_list, downloaded, uploaded, left
	i = int("41727101980", 16)
	j = 0
	Protocol_id = i.to_bytes(8, "big")
	Action = j.to_bytes(4, "big")
	random_num = random.randint(1, 65535)
	Transaction_id = random_num.to_bytes(4, "big")
	mess = Protocol_id + Action + Transaction_id
	udp_socket = socket(AF_INET, SOCK_DGRAM)
	ur = tracker[6:]
	urp = ur.split(":")
	por = urp[1].split('/')
	udp_socket.sendto(mess, (urp[0], int(por[0])))
	reply, addr = udp_socket.recvfrom(1024)
	trans_id = reply[4: 8]
	conn_id = reply[8: 16]
	if trans_id == Transaction_id:
		j = 1
		Action = j.to_bytes(4, "big")
		pe_id = bytes(peer_id, "utf-8")
		d = downloaded.to_bytes(8, "big")
		u = uploaded.to_bytes(8, "big")
		l = left.to_bytes(8, "big")
		j = 0
		eve = j.to_bytes(4, "big")
		ips = j.to_bytes(4, "big")
		j = random.randint(1, 65535)
		key = j.to_bytes(4, "big")
		j = 20
		num_want = j.to_bytes(4, "big")
		j = 6889
		po = j.to_bytes(8, "big")
		mess = conn_id + Action + trans_id + info_hash_sha1 + pe_id + d + l + u + eve + ips + key + num_want + po
		udp_socket.sendto(mess, (urp[0], int(por[0])))
		reply, addr = udp_socket.recvfrom(1024)
		#print(f"Reply: {len(reply)}")
		pee = reply[20:]
		peer_list1 = convert_to_peers(pee)
		peer_list += peer_list1
		#print(f"PeerList: {peer_list1}")
		print(f"\nConnected to tracker {tracker}\n")
	udp_socket.close()

for tracker in tracker_list:
	if tracker["type"] == "http":
		httpreq = convert_to_http(tracker["trac"], info_has, peer_id, uploaded, downloaded, left, port)
		t1 = threading.Thread(target=http_tracker_connect, args=(tracker['trac'], httpreq,))
		tracker_thread_list.append(t1)	
	else:
		t1 = threading.Thread(target=udp_tracker_connect, args=(tracker['trac'],))
		tracker_thread_list.append(t1)


for t in tracker_thread_list:
	t.start()
for t in tracker_thread_list:
	t.join()
#Connecting to trackers ends here


#Printing peers
print("Peer List")
for peer in peer_list:
	print(f"ip = {peer['ip']}\tport = {peer['port']}")
#Printing peers ends here


#Connecting to the peers
peer_thread_list = []
message1 = (bytes(chr(19), 'utf-8') + bytes("BitTorrent protocol", 'utf-8') + bytes(8 * chr(0), "utf-8") + info_hash_sha1 + bytes(peer_id, "utf-8"));

def connect_to_peer(ip, port):
	global message1
	global peer_list
	global info_hash_sha1
	pres = True
	client_socket = socket(AF_INET, SOCK_STREAM)
	#client_socket.settimeout(5.0)
	try:
		client_socket.connect((ip, int(port)))
	except:
		pres = False
	if pres:
		print(f"Connected to peer {ip}")
		client_socket.send(message1)
		Response = client_socket.recv(4096)
		Response2 = b''
		
		pstrlen = unpack("B", Response[0: 1])[0]
		nu = 9 + pstrlen
		info_hash_rep = Response[nu: nu + 20]
		if len(Response) != 0 and info_hash_rep == info_hash_sha1:
			print(f"\nFrom: {ip}\nMessage1: {Response}\nLength: {len(Response)}\n")
			"""
			Response2 = client_socket.recv(4096)
			print(f"\nFrom: {ip}\nMessage1: {Response}\nMessage2: {Response2}\nLength: {len(Response)}\n")
			try:
				Res = client_socket.recv(4096)
				print(f"\nFrom: {ip}, Mess: {Res}")
			except:
				print(f"Error for {ip}")
			"""
		else:
			peer_list.remove({"ip": ip, "port": port})
			
	client_socket.close()
		
for peer in peer_list:
	ip1 = peer["ip"]
	port1 = peer["port"]
	t1 = threading.Thread(target=connect_to_peer, args=(ip1, port1,))
	peer_thread_list.append(t1)
	t1.start()
	
for thr in peer_thread_list:
	thr.join()

print("Available Peer List")
for peer in peer_list:
	print(f"ip = {peer['ip']}\tport = {peer['port']}")
	
	
#Connecting to peers ends here

#torrent_socket.close()
