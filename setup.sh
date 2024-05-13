# Startup scripts
ln -s /home/pi/socketmost/*.service /etc/systemd/system/
ln -s /home/pi/jack/systemd/*.service /etc/systemd/system/
# Alsa
mv /etc/.asoundrc /etc/.asoundrc_old
ln -s /home/pi/alsa/.asoundrc /etc/asoundrc
ln -s /home/pi/alsa/g_audio.conf /etc/modprobe.d/g_audio.conf
#Systemd
systemctl daemon-reload
systemctl enable jackd
systemctl enable socketmost
systemctl enable socketmost_commander
systemctl start jackd
systemctl start socketmost
systemctl start socketmost_commander