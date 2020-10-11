from collections import OrderedDict
from Decode import decode
from Encode import encode
from Tracker import convert_to_http, make_peer_id, convert_to_peers, escape
import subprocess, sys
from socket import *
import random
from struct import *

#to convert into hash values
import hashlib


#path = "/home/chetas/Desktop/ubuntu-20.04.1-desktop-amd64.iso.torrent"
path = "/home/chetas/Desktop/t4.torrent"
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
peer_list = []
tracker_list = []


#Creation and opening of socket for peer to peer connection
#torrent_socket = socket(AF_INET, SOCK_STREAM)

#try:
#	torrent_socket.bind(('', port))
#except:
#	print("error")


"""
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
"""
		
		
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
		if key == b'announce-list':
			for trac in value:
				tracker1 = str(trac[0])
				n = len(tracker1)
				tracker1 = tracker1[2 : n-1]
				if tracker1[0] == "u":
					tracker_list.append({"trac": tracker1, "type": "udp"})
				elif tracker1[0] == "h":
					tracker_list.append({"trac": tracker1, "type": "http"})

#creating a info hash for the file				
info_hash_bencode = encode(info_hash)
info_hash_sha1 = hashlib.sha1(info_hash_bencode).digest()
info_has = escape(info_hash_sha1)

#print(f"Info Hash: {info_hash_sha1}")

#Print list of trackers
print("Tracket-List:")
for t in tracker_list:
	print(t)


#Http/ UDP request to the tracker is made here
peer_id = make_peer_id()
for tracker in tracker_list:
	if tracker["type"] == "http":
		a = 3
		httpreq = convert_to_http(tracker["trac"], info_has, peer_id, uploaded, downloaded, left, port)
	
		try:
			data1 = subprocess.Popen(['wget', '-O', '-', httpreq], stdout=subprocess.PIPE).communicate()[0].strip()

			t, pos1 = decode(data1, 0)
			for key, val in t.items():
				if key == b'peers':
					peer_list = convert_to_peers(val)
		except:
			a = 3
	else:
		i = int("41727101980", 16)
		j = 0
		Protocol_id = i.to_bytes(8, "big")
		Action = j.to_bytes(4, "big")
		random_num = random.randint(1, 65535)
		Transaction_id = random_num.to_bytes(4, "big")
		mess = Protocol_id + Action + Transaction_id
		udp_socket = socket(AF_INET, SOCK_DGRAM)
		ur = tracker["trac"][6:]
		urp = ur.split(":")
		por = urp[1].split('/')
		#print(f"url: {urp[0]}, port: {por[0]}")
		udp_socket.sendto(mess, (urp[0], int(por[0])))
		reply, addr = udp_socket.recvfrom(1024)
		trans_id = reply[4: 8]
		#print(f"new: {trans_id}, old: {Transaction_id}")
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
		udp_socket.close()


#Printing peers
print("Peer List")
for peer in peer_list:
	print(f"ip = {peer['ip']}\tport = {peer['port']}")



#Connecting to the peers
connection_established = True
for peer in peer_list:
	torrent_socket = socket(AF_INET, SOCK_STREAM)

	ip1 = peer["ip"]
	port1 = peer["port"]
	try:
		torrent_socket.connect((ip1, int(port1)))

	except:
		print(f"Error in connecting peer: {ip1}")
		connection_established = False

	if connection_established:
		print(f"Connected to peer: {ip1}")
		print("Send message to peer");
		message1 = (bytes(chr(19), 'utf-8') + bytes("BitTorrent protocol", 'utf-8') + bytes(8 * chr(0), "utf-8") + info_hash_sha1 + bytes(peer_id, "utf-8"));
		


		torrent_socket.send(message1)
		Response = torrent_socket.recv(2048)
		print(Response)
		#Response = torrent_socket.recv(2048)
		#print(Response)
		torrent_socket.close()


"""
#Send message to peer
print("Send message to peer");
message1 = (bytes(chr(19), 'utf-8') + bytes("BitTorrent protocol", 'utf-8') + bytes(8 * chr(0), "utf-8") + info_hash_sha1 + bytes(peer_id, "utf-8"));
print(message1)


torrent_socket.send(message1)
while True:
	Response = torrent_socket.recv(2048)
	print(Response)
"""
#torrent_socket.close()
