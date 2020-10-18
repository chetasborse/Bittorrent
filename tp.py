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
#path = "./torrent_files/111803045.torrent"
#path = "/home/chetas/Desktop/111803045.torrent"
path = "/home/chetas/Desktop/bencoding.py.torrent"

# ____________________Part 1: Reading the torrent file____________________
f = open(path, "rb")
metainfo = f.read()
torrent, pos = decode(metainfo, 0)
# ____________________Part 1 ends here____________________

# Declaring global variables
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
peers_available = []
total_pieces = 0
index_pieces_acquired = []
file_name = ""
# Declaration ends here

folder = False
files = []
#To print metainfo file
for key, value in torrent.items():
	if type(value) == OrderedDict:
		print(f"key: {key}")
		print("OrderedDict2")
		for key1, value1 in value.items():
			print(f"{key1}: {value1}")
			if key1 == b'files':
				folder = True
				files = value1
			#if key1 == b'files':
			#	print(f"{key1}=>{value1}\n")
			#elif key1 == b'pieces':
			#	print(f"{key1}=>\n\t{value1}")
			#else:
			#	print(f"{key1}")
	else:
		print(f"{key}=>{value}\n")
#Printing part ends here

for file_namess in files:
	for key, val in file_namess.items():
		print(f"{key}: {val}")
		
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
					hash_code_list.append(hashval)
					index_pieces_acquired.append({"info_hash": hashval, "acquired": False})
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
			elif key1 == b'name':
				file_name = value1.decode("utf-8")
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
		if key == b'announce':
			tracker = value.decode("utf-8")

total_pieces = int(left / single_piece_len) + 1
last_piece_length = left - (total_pieces - 1) * single_piece_len
print(f"Size: {left}, len: {single_piece_len}\ntot: {total_pieces}")
