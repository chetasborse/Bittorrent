import random
from socket import *
import config
from Tracker import convert_to_peers
from subprocess import STDOUT, check_output
from Decode import decode
import threading
from Encode import encode
from Tracker import convert_to_http

#Connects to http trackers
def http_tracker_connect(tracker, httpreq, info_has_sha1):
	#global peer_list
	connect = True
	#print(httpreq)
	try:
		#data = subprocess.Popen(['wget', '-O', '-', httpreq], stdout=subprocess.PIPE).communicate()[0].strip()
		data = check_output(['wget', '-O', '-', httpreq], timeout=10)
	except Exception as e:
		print(f"\nUnable to connect to the tracker {tracker}\nReason: {e}\n")
		connect = False
	if connect and len(data) != 0:
		print(f"\n\nConnected to tracker {tracker}\n\n")
		t, pos = decode(data, 0)
		for key, val in t.items():
			if key == b'peers':
				peer_list1 = convert_to_peers(val)
				config.peer_list += peer_list1


#Connects to udp trackers	
def udp_tracker_connect(tracker, info_hash_sha1):
	#global peer_list, downloaded, uploaded, left, peer_id
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
		pe_id = bytes(config.peer_id, "utf-8")
		d = config.downloaded.to_bytes(8, "big")
		u = config.uploaded.to_bytes(8, "big")
		l = config.left.to_bytes(8, "big")
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
		config.peer_list += peer_list1
		#print(f"PeerList: {peer_list1}")
		print(f"\nConnected to tracker {tracker}\n")
	udp_socket.close()


def get_the_peers(info_has, peer_id, port, info_hash_sha1):
	tracker_thread_list = []
	tracker_pos = 0 #Tells the point index of tracker which was requested
	tracker_end = tracker_pos + 4 #Tells maximum how many trackers should be requested at a time
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
		tracker_pos += 1
		if tracker_pos == tracker_end:
			break	

	for t in tracker_thread_list:
		t.join(4)