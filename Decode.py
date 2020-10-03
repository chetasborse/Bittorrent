from collections import OrderedDict

#remember to pass 0 in while calling function

def decode(data, pos):
	lit = data[pos: pos + 1]
	if lit == b'i':
		pos += 1
		found = data.index(b'e', pos)
		result = data[pos: found]
		pos = found + 1
		return int(result), pos
	elif lit == b'd':
		pos += 1
		dic = OrderedDict()
		while data[pos: pos + 1] != b'e':
			key, pos = decode(data, pos)
			value, pos = decode(data, pos)
			dic[key] = value
		pos += 1
		return dic, pos
	elif lit == b'l':
		pos += 1
		lis = []
		while data[pos: pos + 1] != b'e':
			ite, pos = decode(data, pos)
			lis.append(ite)
		pos += 1
		return lis, pos
	elif lit == b'0' or lit == b'1' or lit == b'2' or lit == b'3' or lit == b'4' or lit == b'5' or lit == b'6' or lit == b'7' or lit == b'8' or lit == b'9':
		found = data.index(b':', pos)
		length = int(data[pos: found])
		pos = found + 1
		strin = data[pos: pos + length]
		pos += length
		return strin, pos
	elif lit == b'e':
		return data, pos

                  
