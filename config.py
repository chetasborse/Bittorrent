#Config file where all the global variables are stored
from Tracker import make_peer_id

tracker = ""
download_path = ''
folder_dets = [] #Details of folder if the torrent is multi file
hash_code_list = []
uploaded = 0
downloaded = 0
left = 0
peer_id = make_peer_id()
port = 6889
info_hash = ''
is_file = True
single_piece_len = 0
peer_list = []
available_peers = []
global_tracker_list = []
tracker_list = []
peers_available = []
total_pieces = 0
index_pieces_acquired = []
file_name = ""
pieces_acquisition = 0 #Pieces acquired at any given instant of time
pieces_written = 0
index_pieces_acq = []
top4_peer_list = [] #Contains top 4 peers at any random time
request_queue = []
peer_no = 0
sizes = 16384 #Block size in which the pieces need to be requested
last_piece_len = 0
top4_peer_list = []
request_queue = []
write_buffer = []
file_name = ''
f = ''
single_f = ''
file_size = 0