from collections import OrderedDict

def encode(data):
	if type(data) == str:
		value = str(len(data)) + ':' + data
		return str.encode(value)
	elif type(data) == int:
		value = 'i' + str(data) + 'e'
		return str.encode(value)
	elif type(data) == dict or type(data) == OrderedDict:
		value = bytearray('d', 'utf-8')
		for key, val in data.items():
			key1 = encode(key)
			val1 = encode(val)
			value += key1
			value += val1
		value += b'e'
		return value
	elif type(data) == bytes:
		value = bytearray()
		value += str.encode(str(len(data)))
		value += b':'
		value += data
		return value
	elif type(data) == list:
		value = bytearray('l', 'utf-8')
		for item in data:
			value += encode(item)
		value += b'e'
		return value
	else:
		return
			
