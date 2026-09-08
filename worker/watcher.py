import time
from pathlib import Path
import subprocess
import shutil
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config

STATE = {}

def log(message):
    config.LOG_DIR.mkdir(parents=True, exist_ok=True)
    line = time.strftime("%Y-%m-%d %H:%M:%S") + " " + message
    with (config.LOG_DIR / "activity.log").open("a", encoding="utf-8") as f:
        f.write(line + "\n")
    print(line, flush=True)

def eligible(p):
    if not p.is_file() or p.name.startswith("."):
        return False
    if config.WATCH_EXTENSIONS:
        return p.suffix.lower() in [x.lower() for x in config.WATCH_EXTENSIONS]
    return True

def stable_file(p):
    try:
        s1 = p.stat().st_size
        time.sleep(0.4)
        s2 = p.stat().st_size
        return s1 == s2
    except FileNotFoundError:
        return False

def output_path(p):
    ext = config.OUTPUT_EXTENSION or p.suffix
    return config.OUTPUT_DIR / (p.stem + ext)

def process(p):
    out = output_path(p)
    tmp = out.with_name(out.name + ".partial")
    log(f"START {p.name}")
    try:
        cmd = [x.format(input=str(p), output=str(tmp)) for x in config.CONVERSION_COMMAND]
        subprocess.run(cmd, check=True, timeout=3600)
        tmp.replace(out)
        shutil.move(str(p), str(config.ARCHIVE_DIR / p.name))
        log(f"OK    {p.name} -> {out.name}")
    except Exception as e:
        try:
            if tmp.exists():
                tmp.unlink()
            shutil.move(str(p), str(config.ERROR_DIR / p.name))
        except Exception:
            pass
        log(f"FAIL  {p.name} : {e}")

def main():
    for d in (config.INCOMING_DIR, config.OUTPUT_DIR, config.ERROR_DIR, config.ARCHIVE_DIR, config.LOG_DIR):
        d.mkdir(parents=True, exist_ok=True)

    log("WATCHER STARTED")
    while True:
        try:
            for p in sorted(config.INCOMING_DIR.iterdir(), key=lambda x: x.stat().st_mtime):
                if not eligible(p):
                    continue
                if not stable_file(p):
                    continue
                key = str(p)
                stamp = p.stat().st_mtime_ns
                if STATE.get(key) == stamp:
                    continue
                STATE[key] = stamp
                process(p)
        except Exception as e:
            log(f"WATCH ERROR {e}")
        time.sleep(config.POLL_SECONDS)

if __name__ == "__main__":
    main()
