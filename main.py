from multiprocessing import Process
from services.cleanup import run as cleanup_run

def start_cleanup():
    cleanup_run()

if __name__ == "__main__":
    p = Process(target=start_cleanup)
    p.start()
