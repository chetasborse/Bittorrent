from Tracker import *

peer_id = make_peer_id()
has = "9D4A9495BE35D97B13E60D143F37CC38378D8233"
info_hash = bytes.fromhex(has)
print(info_hash)
info_has = escape(info_hash)
tracker = "http://t.nyaatracker.com:80/announce" 
url = convert_to_http(tracker, info_has, peer_id, 0, 0, 0, 6889)
print(url)
