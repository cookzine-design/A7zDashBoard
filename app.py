from flask import Flask, jsonify, render_template, request
from pathlib import Path
from werkzeug.utils import secure_filename
import os
import shutil
import subprocess
import time

import config

app = Flask(__name__)

def read_text(path, default=""):
    try:
        return Path(path).read_text().strip()
    except Exception:
        return default

def cpu_temp():
    candidates = []
    thermal = Path("/sys/class/thermal")
    if thermal.exists():
        for zone in sorted(thermal.glob("thermal_zone*")):
            temp_file = zone / "temp"
            type_file = zone / "type"
            try:
                raw = int(temp_file.read_text().strip())
                temp = raw / 1000 if abs(raw) > 1000 else float(raw)
                name = type_file.read_text().strip() if type_file.exists() else zone.name
                if -20 < temp < 120:
                    candidates.append({"name": name, "temp": round(temp, 1)})
            except Exception:
                pass
    if not candidates:
        return None, []
    # CPU 관련 thermal zone을 우선 선택
    preferred = [x for x in candidates if any(k in x["name"].lower()
                 for k in ("cpu", "soc", "thermal"))]
    selected = (preferred or candidates)[0]["temp"]
    return selected, candidates

def mem_info():
    data = {}
    for line in read_text("/proc/meminfo").splitlines():
        parts = line.split()
        if len(parts) >= 2:
            data[parts[0].rstrip(":")] = int(parts[1]) * 1024
    total = data.get("MemTotal", 0)
    available = data.get("MemAvailable", data.get("MemFree", 0))
    used = max(total - available, 0)
    pct = (used / total * 100) if total else 0
    return {
        "total": total,
        "available": available,
        "used": used,
        "percent": round(pct, 1)
    }

def loadavg():
    try:
        a, b, c = os.getloadavg()
        return [round(a, 2), round(b, 2), round(c, 2)]
    except Exception:
        return [0, 0, 0]

def cpu_usage():
    # /proc/stat 두 번 읽어 짧은 구간의 CPU 사용률 계산
    def sample():
        parts = read_text("/proc/stat").splitlines()
        for line in parts:
            if line.startswith("cpu "):
                nums = [int(x) for x in line.split()[1:]]
                idle = nums[3] + (nums[4] if len(nums) > 4 else 0)
                total = sum(nums)
                return total, idle
        return 0, 0
    a = sample()
    time.sleep(0.12)
    b = sample()
    dt = b[0] - a[0]
    di = b[1] - a[1]
    return round(max(0, min(100, (1 - di / dt) * 100)) if dt else 0, 1)

def disk_info():
    total, used, free = shutil.disk_usage("/")
    return {
        "total": total,
        "used": used,
        "free": free,
        "percent": round(used / total * 100, 1) if total else 0
    }

def directory_stats():
    def count(p):
        try:
            return sum(1 for x in p.iterdir() if x.is_file())
        except Exception:
            return 0
    return {
        "incoming": count(config.INCOMING_DIR),
        "output": count(config.OUTPUT_DIR),
        "error": count(config.ERROR_DIR),
    }

def activity():
    p = config.LOG_DIR / "activity.log"
    try:
        lines = p.read_text(errors="replace").splitlines()
        return lines[-config.MAX_ACTIVITY_LINES:][::-1]
    except Exception:
        return []

@app.get("/")
def index():
    return render_template("index.html")

@app.post("/api/upload")
def upload():
    files = request.files.getlist("files")
    if not files:
        return jsonify({"ok": False, "error": "No files selected"}), 400

    config.INCOMING_DIR.mkdir(parents=True, exist_ok=True)
    uploaded = []
    errors = []

    for f in files:
        if not f or not f.filename:
            continue

        filename = secure_filename(f.filename)
        if not filename:
            errors.append("Invalid filename")
            continue

        if config.WATCH_EXTENSIONS and Path(filename).suffix.lower() not in [
            x.lower() for x in config.WATCH_EXTENSIONS
        ]:
            errors.append(f"{filename}: unsupported extension")
            continue

        # Avoid overwriting an existing input file.
        target = config.INCOMING_DIR / filename
        if target.exists():
            stem, suffix = target.stem, target.suffix
            i = 1
            while target.exists():
                target = config.INCOMING_DIR / f"{stem}_{i}{suffix}"
                i += 1

        try:
            f.save(target)
            uploaded.append(target.name)
        except Exception as e:
            errors.append(f"{filename}: {e}")

    return jsonify({"ok": bool(uploaded), "uploaded": uploaded, "errors": errors}), 200 if uploaded else 400


@app.get("/api/status")
def status():
    temp, thermal_zones = cpu_temp()
    return jsonify({
        "cpu": cpu_usage(),
        "ram": mem_info(),
        "temperature": temp,
        "thermal_zones": thermal_zones,
        "load": loadavg(),
        "disk": disk_info(),
        "dirs": directory_stats(),
        "uptime": read_text("/proc/uptime").split()[0] if read_text("/proc/uptime") else "0",
        "activity": activity(),
        "time": time.strftime("%Y-%m-%d %H:%M:%S"),
    })

@app.post("/api/worker/restart")
def worker_restart():
    if request.remote_addr not in ("127.0.0.1", "::1") and request.headers.get("X-Dashboard-Action") != "cubie":
        return jsonify({"ok": False, "error": "action header required"}), 403
    try:
        subprocess.run(["sudo", "/bin/systemctl", "restart", "cubie-worker"],
                       check=True, timeout=15)
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@app.post("/api/system/reboot")
def reboot():
    if request.remote_addr not in ("127.0.0.1", "::1") and request.headers.get("X-Dashboard-Action") != "cubie":
        return jsonify({"ok": False, "error": "action header required"}), 403
    try:
        subprocess.Popen(["sudo", "/sbin/reboot"])
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

if __name__ == "__main__":
    app.run(host=config.HOST, port=config.PORT)
