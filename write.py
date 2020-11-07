import config
import time
import os

def write_to_file(lock):
    f = ''
    is_file = config.is_file
    if not config.is_file: #This part creates a folder if the torrent is multi file
        config.f = open("temporary", "wb+")
    else:
        f_name = config.download_path + "/" + config.file_name
        f = open(f_name, "wb+")
    while True:
        if len(config.write_buffer) != 0:
            lock.acquire()
            item = config.write_buffer.pop(0)
            lock.release()
            offset = item["index"] * config.single_piece_len
            if is_file:
                f.seek(offset, 0)
                f.write(item["piece"])
            else:
                config.f.seek(offset, 0)
                config.f.write(item["piece"])
            config.pieces_written += 1
            config.downloaded += config.single_piece_len
        else:
            time.sleep(1)
            if config.pieces_written == config.total_pieces and is_file:
                f.close()
                break
            elif config.pieces_written == config.total_pieces and not is_file:
                break


def write_to_multifile():
    while True:
        if config.pieces_written == config.total_pieces:
            # temp_file = open("temporary", "wb+")
            offset = 0
            config.f.seek(0)
            for i in config.folder_dets:
                paths = config.download_path +"/" + config.file_name + i["path"]
                print(f"\nRead start")
                # temp_file.seek(offset, 0)
                data = config.f.read(i["length"]) 
                config.f.seek = 0
                try:
                    os.mkdir(paths)
                except:
                    pass
                f_name = paths + '/' + i["file_name"]
                f = open(f_name, "wb+")
                f.write(data)
                f.close()
            config.f.close()
            break
            if os.path.exists("temporary"):
                os.remove("temporary")
        else:
            time.sleep(2)
    
        