import config
import time

def write_to_file(lock):
    f = open(config.file_name, "wb+")
    is_file = config.is_file
    while True:
        if len(config.write_buffer) != 0:
            lock.acquire()
            item = config.write_buffer.pop(0)
            lock.release()
            temp_list = config.index_pieces_acq[0 : item["index"]]
            coun = temp_list.count(1)
            total_offset = coun * config.single_piece_len
            f.seek(total_offset, 0)
            rem_piece = f.read()
            f.seek(total_offset, 0)
            f.write(item["piece"])
            f.write(rem_piece)
        else:
            time.sleep(1)