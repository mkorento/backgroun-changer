import subprocess
import os
from win32process import DETACHED_PROCESS

if __name__ == '__main__':
    current_dir = os.path.dirname(os.path.realpath(__file__))
    subprocess.Popen([current_dir + '\\client.exe'], creationflags=DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP, close_fds=True)
