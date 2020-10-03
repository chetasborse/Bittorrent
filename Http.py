import random

#function to convert hash to escaped
def escape(has):
	has_hex = has.hex()
	i = 0
	escaped_seq = ''
	while i < 20:
		part = has_hex[i: i + 2].lower()
		if part == '2d' or part == '2e' or part == '5f' or part == '7e' or (part >= '30' and part <= '39') or (part >= '41' and part <= '5a') or (part >= '61' and part <= '7a'):
			escaped_seq += str(int(part, 16))
		else:
			escaped_seq += '%' + part.upper()
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
	http_req = ''
	has_escape = escape(has)
	http_req = tracker + "?" + "info_hash=" + has_escape + "&peer_id=" + peer_id + "&uploaded=" + str(uploaded) + "&downloaded=" + str(downloaded) + "&left=" + str(left) + "&port=6889&compact=0"
	return http_req
	
	
