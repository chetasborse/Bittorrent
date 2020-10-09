from collections import OrderedDict
from Decode import decode
from Encode import encode
from Tracker import convert_to_http, make_peer_id, convert_to_peers, escape
import subprocess, sys
from socket import *

#to convert into hash values
import hashlib


path = "/home/chetas/Desktop/ubuntu-20.04.1-desktop-amd64.iso.torrent"
#path = "/home/chetas/Desktop/Chapter_2_v8.0.pptx.torrent"
#path = "/home/chetas/Desktop/vidmate_201912_archive.torrent"
#path = "/home/chetas/Desktop/s1.png.torrent"

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
peer_list = []


#Creation and opening of socket for peer to peer connection
torrent_socket = socket(AF_INET, SOCK_STREAM)

try:
	torrent_socket.bind(('', port))
except socket.error as e:
	print(str(e))



#To print metainfo file
for key, value in torrent.items():
	if type(value) == OrderedDict:
		print(f"key: {key}")
		print("OrderedDict2")
		for key1, value1 in value.items():
			if key1 == b'files':
				print(f"{key1}=>{value1}\n")
			elif key1 == b'pieces':
				print(f"{key1}=>\n\t{value1}")
			else:
				print(f"{key1}")
	else:
		print(f"{key}=>{value}\n")

		
		
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
	else:
		if key == b'announce':
			tracker = str(value)
			n = len(tracker)
			tracker = tracker[2:n - 1]


#info_hash_bencode = Encoder(info_hash).encode()
info_hash_bencode = encode(info_hash)
info_hash_sha1 = hashlib.sha1(info_hash_bencode).digest()
info_has = escape(info_hash_sha1)
#info_hash_sha1 = hashlib.sha1(info_hash_bencode).hexdigest()
#print(hashlib.sha1(info_hash_bencode).hexdigest())

#print(f"VAlue:\n{info_hash_bencode}")
#print(f"\nTracker: {tracker}\n")
#print("Hash Values:")
#print(f"Length = {left}")
#for has in hash_code_list:
#	print(has)


#Http request to the tracker is made here
peer_id = make_peer_id()
httpreq = convert_to_http(tracker, info_has, peer_id, uploaded, downloaded, left, port)


data1 = subprocess.Popen(['wget', '-O', '-', httpreq],
     stdout=subprocess.PIPE).communicate()[0].strip()
#print(data1)
t, pos1 = decode(data1, 0)
for key, val in t.items():
	if key == b'peers':
		peer_list = convert_to_peers(val)

#Printing peers
print("Peer List")
for peer in peer_list:
	print(f"ip = {peer['ip']}\tport = {peer['port']}")


#Send message to peer
print("Send message to peer");
message1 = (bytes(chr(19), 'utf-8') + bytes("BitTorrent protocol", 'utf-8') + bytes(8 * chr(0), "utf-8") + info_hash_sha1 + bytes(peer_id, "utf-8"));
print(message1)

#Connecting to the peers

connection_established = True

for peer in peer_list:
	ip1 = peer["ip"]
	port1 = peer["port"]
	
	try:
		torrent_socket.connect((ip1, port1))
	except:
		print(f"Error in connecting peer: {ip1}")
		connection_established = False
	if connection_established:
		break

"""
ip1 = peer_list[1]["ip"]
port1 = peer_list[1]["port"]


try:
	torrent_socket.connect((ip1, port1))
except:
	print("Error in connecting")
	sys.exit()
"""

torrent_socket.send(message1)
Response = torrent_socket.recv(2048)
print(Response.decode("utf-8"))

torrent_socket.close()
