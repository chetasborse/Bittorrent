import config
import os

def settings(choice):
    if choice == 1:
        config.max_peers = int(input("\tEnter maximum number of peers: "))
        print(f"\tMaximum number of peers set to {config.max_peers} successfully\n")
    elif choice == 2:
        config.upload_limit = int(input("\tEnter upload limit in kbps: "))
        print(f"\tUpload limit set to {config.upload_limit}\n")
    elif choice == 3:
        config.download_limit = int(input("\tEnter download limit in kbps: "))
        print(f"\tDownload limit set to {config.download_limit}\n")
    elif choice == 4:
        download_path = input("\tEnter download path: ")
        if not os.path.exists(download_path):
            print("\tNo such path exists. Default path set as download path\n")
        else:
            print(f"\tDownload path set to {download_path}\n")
            config.download_path = download_path
    else:
        return True
    return False
