sudo apt update
for i in 1 2 3 4 5; do echo 0 | sudo tee /sys/devices/system/cpu/cpu$i/online ; done
sudo apt full-upgrade -y
sudo reboot
ls
unzip cubie-server-dashboard.zip
sudo apt install unzip
unzip cubie-server-dashboard.zip
ls
cd cubie-server-dashboard
chmod +x install.sh
sudo ./install.sh
unzip cubie-server-dashboard.zip
chmod +x install.sh
sudo ./install.sh
sudo poweroff
