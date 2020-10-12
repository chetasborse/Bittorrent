import random
import urllib

#function to convert hash to escaped
def escape(has):
	has_hex = has.hex()
	i = 0
	escaped_seq = ''
	while i < 40:
		part = has_hex[i: i + 2].lower()
		if part == '2d' or part == '2e' or part == '5f' or part == '7e' or (part >= '30' and part <= '39') or (part >= '41' and part <= '5a') or (part >= '61' and part <= '7a'):
			escaped_seq += chr(int(part, 16))
		else:
			escaped_seq += '%' + part.lower()
		i += 2
	return escaped_seq

#Creates client id based on Azureus-style
def make_peer_id():
	code = 'CS'
	version = '0001'
	random_num = ''
	for i in range(12):
		random_num += str(random.randint(0, 9))
	peer_id = '-' + code + version + '-' + random_num
	return peer_id
	
def convert_to_http(tracker, has, peer_id, uploaded, downloaded, left, port):
	#tracker="http://91.217.91.21:3218/scrape"
	http_req = ''
	#has_escape = escape(has)
	#print(has_escape)
	#has_escape = bytes.fromhex(has)
	http_req = tracker + "?" + "info_hash=" + has + "&peer_id=" + peer_id + "&uploaded=" + str(uploaded) + "&downloaded=" + str(downloaded) + "&left=" + str(left) + "&port=" + str(port) + "&compact=1"
	return http_req
	
def convert_to_peers(data):
	if type(data) == list:
		peerlist = []
		for indi in data:
			for key, val in indi.items():
				if key == b'ip':
					ip1 = val.decode('ascii')
				if key == b'port':
					port = str(val)
			dic = {
				"ip": ip1,
				"port": port
			}
			peerlist.append(dic)
		return peerlist			

	else:
		heci = data.hex()
		#print(heci)
		n = len(heci)
		peerlist = []
		i = 0
		while i < n:
			j = 0
			ip = ''
			port = 0
			while j < 8:
				num = heci[i : i + 2]
				num1 = str(int(num, 16))
				ip += num1 + "."
				j += 2
				i += 2
			ip = ip[0: len(ip) - 1]
			num = heci[i : i + 4]
			port = str(int(num, 16))
			i += 4
			dic = {
				"ip": ip,
				"port": port
			}
			peerlist.append(dic)
		return peerlist
	
	
	
