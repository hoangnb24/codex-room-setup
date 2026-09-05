"""Exercise the installed CLI and daemon without using operator state."""
import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import sys
import tempfile
import time


cli = str(Path(sys.argv[1]).absolute())
with tempfile.TemporaryDirectory(prefix="paseo-daemon-smoke-") as temporary:
    home = Path(temporary)
    env = {key: value for key, value in os.environ.items()
           if not key.startswith(("PASEO_", "CODEX_"))}
    env.update(HOME=str(home), PASEO_HOME=str(home / ".paseo"),
               XDG_CONFIG_HOME=str(home / ".config"))
    subprocess.run([cli, "--help"], env=env, check=True,
                   stdout=subprocess.DEVNULL, timeout=30)
    with socket.socket() as reservation:
        reservation.bind(("127.0.0.1", 0))
        address = "127.0.0.1:" + str(reservation.getsockname()[1])
    with (home / "daemon.log").open("w+") as log:
        process = subprocess.Popen(
            [cli, "daemon", "start", "--foreground", "--listen", address,
             "--home", str(home / ".paseo"), "--no-relay", "--no-web-ui"],
            env=env, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        try:
            deadline = time.monotonic() + 60
            while time.monotonic() < deadline:
                if process.poll() is not None:
                    raise RuntimeError("daemon exited before becoming ready")
                try:
                    result = subprocess.run(
                        [cli, "provider", "ls", "--host", address, "--json"],
                        env=env, capture_output=True, text=True, timeout=5)
                    if result.returncode == 0:
                        json.loads(result.stdout)
                        print("PASEO_DAEMON_SMOKE_OK real_cli_and_provider_rpc")
                        break
                except subprocess.TimeoutExpired:
                    pass
                time.sleep(0.5)
            else:
                raise RuntimeError("daemon did not answer provider RPC within 60 seconds")
        except Exception:
            log.flush()
            log.seek(0)
            print(log.read(), file=sys.stderr)
            raise
        finally:
            try:
                os.killpg(process.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait(timeout=5)
