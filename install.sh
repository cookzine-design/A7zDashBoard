#!/bin/bash
set -euo pipefail

APP=/opt/cubie-dashboard
DATA=/srv/cubie

if [ "$EUID" -ne 0 ]; then
  echo "Please run: sudo ./install.sh"
  exit 1
fi

echo "[1/7] Installing system packages..."
apt-get update
apt-get install -y python3 python3-venv python3-pip sudo

echo "[2/7] Creating cubie service user..."
if ! id cubie >/dev/null 2>&1; then
  useradd --system --home "$APP" --shell /usr/sbin/nologin cubie
fi

echo "[3/7] Installing application..."
mkdir -p "$APP" "$DATA"/{incoming,output,error,archive,logs}
cp -a app.py config.py requirements.txt templates static worker "$APP"/
chown -R cubie:cubie "$APP" "$DATA"
chmod 755 "$APP" "$DATA"

echo "[4/7] Creating Python virtual environment..."
python3 -m venv "$APP/.venv"
"$APP/.venv/bin/pip" install --upgrade pip
"$APP/.venv/bin/pip" install -r "$APP/requirements.txt"
chown -R cubie:cubie "$APP/.venv"

echo "[5/7] Installing systemd units..."
cp systemd/cubie-dashboard.service /etc/systemd/system/
cp systemd/cubie-worker.service /etc/systemd/system/

echo "[6/7] Installing restricted sudo rules..."
cat >/etc/sudoers.d/cubie-dashboard <<'EOF'
cubie ALL=(root) NOPASSWD: /bin/systemctl restart cubie-worker
cubie ALL=(root) NOPASSWD: /sbin/reboot
EOF
chmod 440 /etc/sudoers.d/cubie-dashboard
visudo -cf /etc/sudoers.d/cubie-dashboard

echo "[7/7] Starting services..."
systemctl daemon-reload
systemctl enable --now cubie-worker
systemctl enable --now cubie-dashboard

echo
echo "=========================================="
echo " Cubie Server Dashboard installed"
echo "=========================================="
echo
echo "Dashboard: http://$(hostname -I | awk '{print $1}'):8080"
echo "Input:     $DATA/incoming"
echo "Output:    $DATA/output"
echo "Error:     $DATA/error"
echo
echo "Status:"
systemctl --no-pager --full status cubie-dashboard || true
systemctl --no-pager --full status cubie-worker || true
