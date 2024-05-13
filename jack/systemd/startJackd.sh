#!/bin/bash
export DISPLAY=:0
export "receiveSamplingRate=44100"
export "sndDevice=snd_44k_16"

is_jackd_running() {
   touch /tmp/log/nohup-jack.out
   jack_wait -w -t 60
}

is_alsa_running() {
   touch /tmp/log/nohup-usb2audio.out
   touch /tmp/log/nohup-usb2audio-err.out
   observe_startup "$!" '1.000000' "poll timed out" /tmp/log/{nohup-usb2audio.out,nohup-usb2audio-err.out}
}
 
is_camilladsp_running() {
   touch /tmp/log/nohup-camilladsp.out
   (ps aux | grep -q '[c]amilladsp') && ! (cat /tmp/log/nohup-camilladsp.out | grep -q 'ClientError(FAILURE | SERVER_FAILED)')
}

function wait_file_changed {
   tail -fn0 --silent $@ | head -n1
}

function observe_startup {
  local pid="$1"
  local word_true="$2"
  local word_false="$3"
  local match=''
  while kill -0 $pid 2> /dev/null; do
      match=$(cat ${@:4} | grep --line-buffered -o -e "$word_false" -e "$word_true")
      if [ "$match" = "$word_true" ]; then
         return 0
      elif [ "$match" = "$word_false" ]; then
         return 1
      else
         sleep 0.01
      fi
  done
  return 1
}

mkdir -p /tmp/log
rm /tmp/log/nohup-*.out || true	 

case "$1" in 
start)
    { JACK_NO_AUDIO_RESERVATION=1 nohup stdbuf -oL jackd -R -P 94 -n default -d alsa -p 512 -P plug:pcm.snd_44k_16 -r 44100 -O &> /tmp/log/nohup-jack.out 2> /tmp/log/nohup-jack-err.out </dev/null &  
      while ! is_jackd_running; do	
         sleep 0
      done
      nohup jack-matchmaker -p /home/pi/config/jack/matchmaker/patterns.cfg &>/dev/null &
    } && {
      echo "Spawn Zita"
      modprobe -r g_audio 
      systemctl restart systemd-modules-load.service
      nohup stdbuf -oL jack_load usb2audio zalsa_in -i "-d snd_card_usb -r 44100 -p 512 -n 4 -Q 96 -S" &> /tmp/log/nohup-usb2audio.out 2> /tmp/log/nohup-usb2audio-err.out </dev/null
      echo "Camilladsp"
      nohup /root/.cargo/bin/camilladsp -s /home/pi/config/camilladsp/statefile.yml -o /tmp/log/camilladsp.log -p 1234 /home/pi/config/camilladsp/configs/MOSTPI.yml > /tmp/log/nohup-camilladsp.out 2> /tmp/log/nohup-camilladsp-err.out &
    } && {
      echo "CamillaGui, Jacktrip, gaudio_ctl"
      nohup /home/pi/dev/camillagui/.venv/bin/python /home/pi/dev/camillagui/main.py &>/dev/null &
      nohup jacktrip -S &>/dev/null &
      nohup /home/pi/dev/gaudio_ctl/target/release/gaudio_ctl -g UAC2Gadget -c "Capture Rate" -d 60 -y "/home/pi/config/socketmost/.venv/bin/python3 /home/pi/config/socketmost/socketmost_commander.py setAmplifierSink 2" &>/dev/null &
    }
   ;;
stop)
   ps -ef | grep 'jackd' | grep -v grep | awk '{print $2}' | xargs -r kill -9
   ps -ef | grep 'qjackctl' | grep -v grep | awk '{print $2}' | xargs -r kill -9
   ps -ef | grep 'jack-matchmaker' | grep -v grep | awk '{print $2}' | xargs -r kill -9
   ps -ef | grep 'camillagui' | grep -v grep | awk '{print $2}' | xargs -r kill -9
   ps -ef | grep 'camilladsp' | grep -v grep | awk '{print $2}' | xargs -r kill -9
   ps -ef | grep 'jacktrip' | grep -v grep | awk '{print $2}' | xargs -r kill -9
   ps -ef | grep 'zita-a2j' | grep -v grep | awk '{print $2}' | xargs -r kill -9
   ps -ef | grep 'gaudio_ctl' | grep -v grep | awk '{print $2}' | xargs -r kill -9
   ;;
restart)
   $0 stop
   $0 start
   ;;
status)
   if [ -e /var/run/hit.pid ]; then
      echo hit.sh is running, pid=`cat /var/run/hit.pid`
   else
      echo hit.sh is NOT running
      exit 1
   fi
   ;;
*)
   echo "Usage: $0 {start|stop|status|restart}"
esac

exit 0 

