import time
import schedule
import daemon
from daemon import pidfile



class Daemon:
    LOCK_FILE = '/tmp/ps_daemon.pid'
    def __init__(self):
        pass

    def start_bg(self):
        print("Starting in background")
        file = pidfile.TimeoutPIDLockFile(self.LOCK_FILE)
        with daemon.DaemonContext(pidfile=file):
            print("Started")
            self.start()
        print("After context")
        pid = get_daemon_pid(self.LOCK_FILE)
        if pid is not None:
            print(f"Daemon PID: {pid}")
        else:
            print("Daemon is not running.")

    def start(self):
        print(f"PS Daemon Scheduling tasks")
        schedule.every(5).minutes.do(self._rewrite_bm25_database)

        print("Starting loop")
        while True:
            schedule.run_pending()
            time.sleep(1)

    def _rewrite_bm25_database(self):
        from python_search.search_ui.bm25_search import Bm25Search
        Bm25Search().build_bm25()
        print("Bm25 database rewritten")


def get_daemon_pid(pid_file):
    try:
        with open(pid_file, 'r') as file:
            pid = int(file.read().strip())
            return pid
    except FileNotFoundError:
        return None  # PID file doesn't exist, daemon might not be running


def main():
    import fire
    fire.Fire(Daemon)


if __name__ == "__main__":
    main()
