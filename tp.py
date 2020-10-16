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
#path = "/home/chetas/Desktop/t1.torrent"
path = "/home/chetas/Desktop/vidmate_201912_archive.torrent"
#path = "/home/chetas/Desktop/amusementsinmath16713gut_archive.torrent"

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
# Declaration ends here


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
#Printing part ends here

