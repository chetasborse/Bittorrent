from collections import OrderedDict
#To print metainfo file

def print_torr(torrent):
    for key, value in torrent.items():
        if type(value) == OrderedDict:
            print(f"key: {key}")
            print("OrderedDict2")
            for key1, value1 in value.items():
                print(f"{key1}: {value1}")
                #if key1 == b'files':
                #	print(f"{key1}=>{value1}\n")
                #elif key1 == b'pieces':
                #	print(f"{key1}=>\n\t{value1}")
                #else:
                #	print(f"{key1}")
        else:
            print(f"{key}=>{value}\n")
