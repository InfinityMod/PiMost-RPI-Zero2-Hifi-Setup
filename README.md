# PiMost-RPI-Zero2-Hifi-Setup
This repository includes all configuration and startup files to set up a Raspberry Pi zero2 with a Jack2 server that bridges music from the OTG USB port to the PiMost adapter and finally into the MOST25 bus. This configuration also includes the setup for Camilladsp. Jack-Matchmaker is utilized for an automatic sink and source connection in jack.

What you need to do to get everything running:
1. Install Raspbian on your SD card for the RPI
2. Install on the live system Jack2, Camilladsp, Jack-;atchmaker and Node17
3. Install on the live system CamillaGUI to /home/pi/dev/camillagui
4. Clone the SocketMost repository (best to /home/pi/SocketMost)
5. Clone this repository to /home/pi/config
6. Execute setup.sh:
```
chmod +x /home/pi/config/setup.sh
/home/pi/config/setup.sh
```
7. Reboot the system and see if everything works out.
8. Possibly, you need to adapt the device labels for the Requires and After configuration in jackd.service.
Also, see if you installed all paths as applied in the jack/systemd/startJackd.sh file, which is the main file used to start the music pipeline.

I will also upload a clean, minimal-usage RPI image that already includes the setup as soon as possible.

Please see [https://techblogio.com/blog/bmw-digital-audio-streaming](https://techblogio.com/blog/bmw-digital-audio-streaming) for further documentation.