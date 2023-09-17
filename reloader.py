import subprocess
import time
from typing import Callable, Dict, Iterable, Optional
import os
import sys
import threading

_STAT_IGNORE_SCAN = tuple({
    sys.base_exec_prefix, 
    sys.base_prefix, 
    sys.prefix, 
    sys.exec_prefix, 
    os.path.realpath(sys.base_exec_prefix),
    os.path.realpath(sys.base_prefix)
})

_IGNORE_COMMON_DIR = {
    "__pycache__",
    ".git",
    ".hg",
    ".tox",
    ".nox",
    ".pytest_cache",
    ".mypy_cache",
}

class ReloaderLoop:
    def __enter__(self) -> "ReloaderLoop":
        self.mtims: Dict[str, float] = {}
        self.__run_step()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass
    
    def __run_step(self) -> None: 
        for name in self.__find_stat_paths():
            mtime = os.stat(name).st_mtime
            old_time = self.mtims.get(name)
            if not old_time:
                self.mtims[name] = mtime
                continue
            if mtime > old_time:
                self.__trigger_reload(name)

    def __trigger_reload(self, filename: str) -> None:
        filename = os.path.abspath(filename)
        print(f"* Detected change in {filename}, reloading")
        sys.exit(3)

    def __find_stat_paths(self) -> Iterable[str]:
        paths = set()
        for path in sys.path:
            path = os.path.abspath(path)
            if os.path.isfile(path):
                paths.add(path)
                continue
            for root, dirs, files in os.walk(path):
                if root.startswith(_STAT_IGNORE_SCAN) or os.path.basename(root) in _IGNORE_COMMON_DIR:
                    dirs.clear()
                    continue
                for name in files:
                    if name.endswith((".py", ".pyc")):
                        paths.add(os.path.join(root, name))
        return paths

    def run(self) -> None:
        while True:
            self.__run_step()
            time.sleep(1)
    
    def restart_with_reloader(self) -> Optional[int]:
        while True:
            print(f"* Restarting server")
            args = [sys.executable, *sys.orig_argv[1:]]
            new_environ = os.environ.copy()
            new_environ["RUN_MAIN"] = "true"
            exit_code = subprocess.call(args, env=new_environ, close_fds=False)
            if exit_code != 3:
                return exit_code

    
def run_with_reloader(main_func: Callable):
    reloader = ReloaderLoop()

    if os.environ.get("RUN_MAIN") == "true":
        t = threading.Thread(target=main_func)
        t.daemon = True

        with reloader:
            t.start()
            reloader.run()  
    else:
        sys.exit(reloader.restart_with_reloader())