from collections import OrderedDict
from Decode import decode
from Http import convert_to_http, make_peer_id

#path = "/home/chetas/Desktop/abcd.png.torrent"
path = "/home/chetas/Desktop/ubuntu-20.04.1-desktop-amd64.iso.torrent"

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

"""
#To print metainfo file
for key, value in torrent.items():
	if type(value) == OrderedDict:
		print("OrderedDict2")
		for key1, value1 in value.items():
			print(f"{key1}=> {value1}")
	else:
		print(f"{key}=> {value}\n")
"""
		
		
for key, value in torrent.items():
	if type(value) == OrderedDict:
		for key1, value1 in value.items():
			if key1 == b'pieces':
				i = 0
				n = len(value1)
				while i < n:
					hashval = value1[i: i + 20]
					i += 20
					hash_code_list.append(hashval)
			elif key1 == b'length':
				left = int(value1)
				#print(left)
	else:
		if key == b'announce':
			tracker = str(value)
			n = len(tracker)
			tracker = tracker[2:n - 1]
		


#print(f"\nTracker: {tracker}\n")
#print("Hash Values:")
#print(f"Length = {left}")
#for has in hash_code_list:
#	print(has)

for has in hash_code_list:
	httpreq = convert_to_http(tracker, has, peer_id, uploaded, downloaded, left, port)
	print(httpreq)

