import os
import zmq
import socket
import threading
import socketio
import logging
import argparse
import psutil
import sys
import signal
import time
from threading import Timer
from typing import Optional

fBlocks = {
    0x01: 'NetBlock',
    0x02: 'NetworkMaster',
    0x03: 'ConnectionMaster',
    0x05: 'Vehicle',
    0x06: 'Diagnosis',
    0x07: 'DebugMessages',
    0x0e: 'Tool',
    0x0f: 'EnhancedTestibility',
    0x10: 'Sources',
    0x21: '33',
    0x22: 'Amplifier',
    0x23: '35',
    0x24: 'AuxIn',
    0x26: 'MicrophoneInput',
    0x30: 'AudioTapePlayer',
    0x31: 'AudioDiskPlayer',
    0x34: 'DVDVideoPlayer',
    0x40: 'AmFmTuner',
    0x41: 'TMCTuner',
    0x42: 'TVTuner',
    0x43: 'DABTuner',
    0x44: 'SDARS',
    0x50: 'Telephone',
    0x51: 'GeneralPhoneBook',
    0x60: 'GraphicDisplay',
    0xf5: '245',
    0xf0: '240',
    0x71: 'Climate'
}
fkt_list = {
    'general': {
        0x000: 'FktIDs',
        0x001: 'Notification',
        0x002: 'NotificationCheck',
        0x010: 'Version',
        0x011: 'FBlockInfo',
        0x080: 'DynArrayIns',
        0x081: 'DynArrayDel',
        0x082: 'MapIns',
        0x083: 'MapDel',
        0x090: 'CreateArrayWindow',
        0x091: 'DestroyArrayWindow',
        0x092: 'MoveArrayWindow',
        0x093: 'SearchArrayWindow',
        0x094: 'LongArrayInfo',
        0x09a: 'ArrayWindowIns',
        0x09b: 'ArrayWindowDel',
        0x0a0: 'PowerDownDelay',
        0x0c0: 'HDCP_ReceiverConnectedIndication',
        0x0c1: 'HDCP_ReceiverDisconnectedIndication',
        0x0c2: 'HDCP_Control',
        0x0c4: 'HDCP_DecipherStatus',
        0x0c5: 'HDCP_Assign',
        0x100: 'SourceInfo',
        0x101: 'Allocate',
        0x102: 'DeAllocate',
        0x103: 'SourceActivity',
        0x104: 'SourceName',
        0x108: 'AllocateExt',
        0x110: 'SinkInfo',
        0x111: 'Connect',
        0x112: 'DisConnect',
        0x113: 'Mute',
        0x114: 'SinkName',
        0x115: 'ConnectTo',
        0x116: 'StreamDataInfo',
        0x117: 'SinkRouting',
        0x118: 'ConnectExt',
        0x120: 'DTCP_StartProcess',
        0x121: 'DTCP_Control',
        0x122: 'DTCP_Status',
        0x123: 'DTCP_CipherStatus',
        0x124: 'DTCP_Info',
        0x125: 'DTCP_ContentKeyProcess',
        0x126: 'DTCP_InfoExt',
        0x130: 'ScreenFormat',
        0x131: 'VideoFrequency',
        0x132: 'VideoNorm',
        0x133: 'VideoSignalFormat',
        0x135: 'VideoFormat',
        0x200: 'DeckStatus',
        0x201: 'TimePosition',
        0x202: 'TrackPosition',
        0x203: 'FramePosition',
        0x205: 'TitlePosition',
        0x206: 'ChapterPosition',
        0x207: 'DeckStatusExt',
        0x251: 'VideoInteraction',
        0x270: 'PlayerRegion',
        0x430: 'DeckEvent',
        0x431: 'MediaEvent',
        0x450: 'Random',
        0x451: 'Scan',
        0x452: 'Repeat',
        0x453: 'NextTrackToPlay',
        0x454: 'Deemphasis',
        0x455: 'SlowFwSpeed',
        0x456: 'SlowBwSpeed',
        0x457: 'FastFwSpeed',
        0x458: 'FastBwSpeed',
    },
    'amplifier': {
        0x000: 'FktIDs',
        0x001: 'Notification',
        0x002: 'NotificationCheck',
        0x010: 'Version',
        0x110: 'SinkInfo',
        0x111: 'Connect',
        0x112: 'DisConnect',
        0x113: 'Mute',
        0x114: 'SinkName',
        0x115: 'ConnectTo',
        0x116: 'SyncDataInfo',
        0x117: 'SinkRouting',
        0x200: 'Balance',
        0x201: 'Loudness',
        0x202: 'Bass',
        0x203: 'Treble',
        0x204: 'Fader',
        0x400: 'Volume',
        0x401: 'FadeInOut',
        0x402: 'Subwoofer',
        0x404: 'BassBoost',
        0x421: 'CompThreshold',
        0x422: 'LimThreshold',
        0x423: 'CompGain',
        0x424: 'AttackTime',
        0x425: 'ReleaseTime',
        0x426: 'CompressorSettings',
        0x427: 'LimiterSettings',
        0x430: 'Crossover',
        0x431: 'CrossoverSlope',
        0x440: 'DelayLine',
        0x441: 'SpeakerDelay',
        0x450: 'InputGainOffset',
        0x451: 'OutputGainOffset',
        0x452: 'OutputPhase',
        0x460: 'EqualizerOnOff',
        0x461: 'EqualizerSettings',
        0x462: 'GraphEqualizerOnOff',
        0x463: 'GraphEqualizer',
        0x464: 'GraphEqualizerLinear',
        0x465: 'MidTones',
        0x466: 'MuteParameters',
        0x467: 'MixerLevel',
        0x468: 'SoundSettingList',
        0x469: 'RecallSoundSetting',
        0x46a: 'SaveSoundSetting',
        0x46b: 'DynSoundControl',
        0x46c: 'CurrentSoundSetting',
        0x46d: 'SpeakerLevel',
    }
}

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RepeatTimer(Timer):
    def run(self):
        while not self.finished.wait(self.interval):
            self.function(*self.args, **self.kwargs)

class SocketMostClient(threading.Thread):
    def __init__(self):
        super().__init__()
        self.socketio = None
        self.registry = None
        self.listener = None
        self.commandStore = None
        self.server_check_interval = None

    def connect(self):
        self.server_check_interval = RepeatTimer(1, self.check_for_server)
        self.server_check_interval.start()
        
    def check_for_server(self):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.bind(('localhost', 8890))
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            self.socket.settimeout(1)  # Set a timeout for receiving messages
            self.socket.sendto(b'Server?', ('255.255.255.255', 5555))
            data, addr = self.socket.recvfrom(1024)
            addr = ['localhost', addr[1]] 
            self.connect_to_socket(f"ws://{addr[0]}:5556")
            self.server_check_interval.cancel()
            logger.debug(f"Server found: {addr[0]}:{addr[1]}")
        except socket.timeout:
            logger.debug("No server found within the timeout.")
 
    def connect_to_socket(self, uri):
        self.socketio = socketio.Client()

        def message_handler(msg):
            print('Received message: ', msg)
            self.on_message(msg)
        self.socketio.on('message', message_handler)

        @self.socketio.event
        def connect():
            time.sleep(0.50)
            logger.debug('Connected to MOSTPI!')
            self.socketio.emit('requestRegistry')

        @self.socketio.event
        def allocResults(data):
           self.on_alloc_results(data)

        @self.socketio.event
        def disconnect():
            self.on_disconnect()
        
        self.socketio.connect(uri)

    def on_message(self, message):
        if message["opType"] == 0x0f:
            try:
                parsed_error = self.error_parser.parse_error(message)
                logger.debug('error', parsed_error)
            except Exception as e:
                logger.debug('error', f'undefined error: {str(e)} {message}')
        else:
            if message["fktID"] == 2561:
                logger.debug("reg update")
                self.parse_registry(message)
            elif message["fktID"] == 0 and message["fBlockID"] > 1:
                self.parser.parse_message(message, message["fktID"])

        if self.commandStore is not None:
            cs = self.commandStore
            self.commandStore = None
            self.execute(*cs)

    def on_alloc_results(self, data):
        logger.debug('alloc results', data)

    def on_disconnect(self):
        self.socketio = None
        self.connect()

    def stop_listener(self):
        if self.listener is not None:
            # Terminate the server process
            self.listener.terminate()
            quit()

    def parse_registry(self, data):
        if  self.registry is None:
            self.registry = {}
        logger.debug("parsing registry")
        i = 0
        while i < len(data["data"]):
            temp_fblock_id = data["data"][i + 2]
            readable_name = fBlocks.get(temp_fblock_id, temp_fblock_id)
            
            if readable_name not in self.registry:
                self.registry[readable_name] = []

            self.registry[readable_name].append({
                'address': self.read_uint16_be(data["sourceAddrHigh"], data["sourceAddrLow"]),
                'instanceID': data["data"][i + 3],
                'fBlockID': temp_fblock_id
            })

            i += 4

    def read_uint16_be(self, high, low):
        return (high << 8) | low
    
    def read_uint8_be(self, value, offset):
        return (value >> 8*offset) & 0xFF

    def execute(self, command, args):
        self.server_check_interval.join()
        if command == 'setAmplifierSink':
            logger.debug(f"Executing: {command}")
            if self.registry is None:
                logger.debug("Getting registry")
                self.socketio.emit('requestRegistry')
            else:
                amplifier = self.registry.get('Amplifier', None)
                if amplifier is not None:
                    logger.debug("Switch amplifier stream")
                    amplifier = amplifier[0]
                    data = {
                        'sourceAddrHigh': self.read_uint8_be(amplifier["address"], 1),
                        'sourceAddrLow': self.read_uint8_be(amplifier["address"], 0),
                        'fBlockID': amplifier["fBlockID"],
                        'instanceID': amplifier["instanceID"],
                        'sinkNr': int(args[0])
                    }
                    self.socketio.emit('stream', data)
                else:
                    logger.debug("Amplifier not found in registry")
class ZMQServer:
    def __init__(self, pid_file_path="server.pid"):
        self.pid_file_path = pid_file_path
        self.smc = None
        self.running = True
        signal.signal(signal.SIGINT, self.kill_server)
        signal.signal(signal.SIGTERM, self.kill_server)

    def kill_server(self, *args, **kwargs):
        self.stop_server()
        self.quit()
    
    def routines(self, routine, args):
        if routine == 'startup':
            logger.debug("Background Server started up.")
        elif routine == 'stop':
            logger.debug("Stopping background server")
            self.stop_server()
        else:
            self.smc.execute(routine, args)

    def server(self, message=None):
        context = zmq.Context()
        socket = context.socket(zmq.REP)
        socket.bind("tcp://127.0.0.1:5570")
        self.smc = SocketMostClient()
        self.smc.connect()

        if message is not None:
            self.routines(message["routine"], message["args"])

        # RabbitMQ loop
        while self.running:
            message = socket.recv_json()
            logger.debug(f"Received request: {message}")

            # Simulate some work
            self.routines(message["routine"], message["args"])

            # Send a response
            socket.send_json({"state":"success"})
        
        quit()

    def write_pid_file(self):
        with open(self.pid_file_path, 'w') as f:
            f.write(str(os.getpid()))

    def read_pid_file(self):
        try:
            with open(self.pid_file_path, 'r') as f:
                return int(f.read().strip())
        except FileNotFoundError:
            return None
        
    def delete_pid_file(self):
        try:
            os.remove(self.pid_file_path)
        except:
            logger.debug("PID not existing anymore.")
            pass

    def is_process_alive(self, pid):
        if pid is None:
            return False
        elif psutil.pid_exists(pid):
            return os.path.basename(__file__) in " ".join(psutil.Process(pid).cmdline())
        else:
            logger.debug("Process not existing anymore.")
            return False
        
    def sendToServer(self, message):
        context = zmq.Context()
        socket = context.socket(zmq.REQ)
        socket.connect("tcp://127.0.0.1:5570")

        # Send a message to the server
        socket.send_json(message)

        # # Receive the response
        response = socket.recv()
        logger.debug(f"Received response: {response}")

    def execute(self, routine, args):
        # Check if the server is already running by reading the PID file
        if not self.is_process_alive(self.read_pid_file()) and routine in ["startup", "stop"]:
            # Write the PID to the file
            self.write_pid_file()
            # Spawn the server process
            self.server({"routine":routine, "args":args})
            # Send message to started server    
        else:
            logger.debug(f"Send to server: {routine}, arguments: {args}")
            self.sendToServer({"routine":routine, "args":args})

    def stop_server(self, *args, **kwargs):
        if self.smc is not None:
            # Terminate the server process
            self.smc.stop_listener()
        # Remove the PID file after the server process has terminated
        self.delete_pid_file()
        self.running = False

def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('command', nargs='?', help='Command to execute against the SocketMostClient')
    parser.add_argument('nargs', nargs='*')
    parser.add_argument('--log-level', default='INFO', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                        help='Set the logging level (default: INFO)')
    parser.add_argument('--start', action=argparse.BooleanOptionalAction, default=False, help='Trigger a client background start')
    parser.add_argument('--stop', action=argparse.BooleanOptionalAction, default=False, help='Trigger a client background stop')
    args = parser.parse_args()

    logger.setLevel(args.log_level)
    
    zmq_server = ZMQServer()
    if args.stop:
        zmq_server.execute('stop', None)
    elif args.start:
        zmq_server.execute('startup', None)
    else:
        zmq_server.execute(args.command, args.nargs)


if __name__ == "__main__":
    main()