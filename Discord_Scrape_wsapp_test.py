import requests
import json
import websocket
import threading
import time


class CDiscord_Scrape:

    def retrieve_messages(self, channelid):
        headers = {
            'authorization': self.token
        }
        r = requests.get(f'https://discord.com/api/v9/channels/{channelid}/messages', headers = headers)
        j = json.loads(r.text)
        return j

    def retrieve_guild(self, guild_id):
        headers = {
            'authorization': self.token
        }
        r = requests.get(f'https://discord.com/api/v9/guilds/{guild_id}', headers = headers)
        j = json.loads(r.text)
        return j


    def on_data(self, wsapp, rec_data, wsapp_opcode, contflag):
        self.event = json.loads(rec_data)
        print(f"opcode: {wsapp_opcode}  contflag: {contflag}, rec_data: {json.dumps(self.event)[:200]}")

        if wsapp_opcode ==  websocket.ABNF.OPCODE_TEXT:

            # This doesn't work for PingPongEnabled.
            # For HearbeatEnabled, a fault injection sequence of commands to the Discord server need to be developed for verification
            if self.event['op'] == 0 and self.event['t'] == "READY":
                if self.invalid_session:
                    resumeJSON = {
                        "op": 6,
                        "d": {
                            "token"     : self.token,
                            "session_id": self.session_id,
                            "seq"       : self.last_sequence_nr
                        }
                    }
                    #time.sleep(1)
                    wsapp.send(json.dumps(resumeJSON))
                    print(f"Sent resume: {json.dumps(resumeJSON)}")
                else:
                    self.session_id = self.event['d']['session_id']

            elif self.event['op'] == 0 and self.event['t'] == "RESUME":     # Correct? Fault injection needed to test resume feature.
                self.invalid_session = False
                print("Session Resumed!")

            elif self.event['op'] == 0 and "author" in self.event['d']:
                guild_id  = self.event['d']['guild_id']
                guildJSON = self.retrieve_guild(guild_id)
                print(f"{guildJSON['name']}.{self.event['d']['author']['username']}: {self.event['d']['content']}")

            elif self.event['op'] == 10 and "heartbeat_interval" in self.event['d']:
                self.heartbeat_interval = self.event['d']['heartbeat_interval'] / 1000
                print(f"heartbeat_interval received: {self.heartbeat_interval}s")

            elif self.event['op'] == 11:
                self.heartbeat_current_time_sec = time.time()
                heartbeat_delta_time_sec = self.heartbeat_current_time_sec - self.heartbeat_prev_time_sec
                print(f"GMT: {time.asctime(time.gmtime())}  heartbeat_delta_sec: {heartbeat_delta_time_sec:.1f}s  Got a Heartbeat back from server!")
                self.heartbeat_prev_time_sec = self.heartbeat_current_time_sec


            elif self.event['op'] == 9:     # Invalid Session received from Discord Server. Close run_forever() and try to resume
                                            # For HearbeatEnabled, a fault injection sequence of commands to the Discord server need to be developed so op==9 message is sent back from the server.
                self.invalid_session = True
                self.last_sequence_nr = self.sequence_nr
                print(f"op:{self.event['op']}")
                wsapp.close()

        self.sequence_nr = self.event['s']
                

    def on_error(self, wsapp, error):
        print(error)

    def on_close(self, wsapp, close_status_code, close_msg):
        print("### closed ###")

    def on_ping(self, wsapp, message):
        print("Got a ping! A pong reply has already been automatically sent.")

    def on_pong(self, wsapp, message):
        self.pong_current_time_sec = time.time()
        pong_delta_time_sec = self.pong_current_time_sec - self.pong_prev_time_sec
        print(f"GMT: {time.asctime(time.gmtime())}  pong_delta_sec: {pong_delta_time_sec:.1f}s  Got a pong! No need to respond")
        self.pong_prev_time_sec = self.pong_current_time_sec

    def on_open(self, wsapp):

        heartbeatJSON = {
            "op": 1,
            "d": "null"
        }

        if self.HeartbeatEnable:
            print('Heartbeat begin')
            def Heartbeat(*args):
               while True:
                    time.sleep(self.heartbeat_interval)
                    #time.sleep(2)   # Test purpose
                    wsapp.send(json.dumps(heartbeatJSON))
                    print("Heartbeat sent")
                
            thread_Heartbeat = threading.Thread(target=Heartbeat)
            thread_Heartbeat.start()
        
        if self.token:
            connectJSON = {
                'op': 2,
                "d": {
                    "token": self.token,
                    "properties": {
                        "$os": "windows",
                        "$browser": "chrome",
                        "$device": 'pc'
                    }
                }
            }
            wsapp.send(json.dumps(connectJSON))


    def Run(self, token=None, PingPongEnable=True, HeartbeatEnable=None):
        # First get the heartbeat_interval from the server with WebSock (for WebSocketApp run_forever() call)
        ws = websocket.WebSocket()
        ws.connect('wss://gateway.discord.gg/?v=9&encoding=json')
        ws.send(json.dumps({"op":1,"d":"null"}))
        time.sleep(1)
        response = ws.recv()
        if response:
            j = json.loads(response)
            self.heartbeat_interval = j['d']['heartbeat_interval'] / 1000
        else:
            print("No heartbeat_interval was received. Stop execution")
            exit()
        ws.close()

        self.token = token
        self.HeartbeatEnable = HeartbeatEnable
        self.PingPongEnable = PingPongEnable
        self.invalid_session = False

        self.pong_prev_time_sec = time.time()
        self.heartbeat_prev_time_sec = time.time()

        websocket.enableTrace(False)
        
        wsapp = websocket.WebSocketApp('wss://gateway.discord.gg/?v=10&encoding=json',
                                        on_error=self.on_error, 
                                        on_close=self.on_close)
        
        wsapp.on_data=self.on_data
        wsapp.on_open = self.on_open
        if PingPongEnable:
            wsapp.on_ping = self.on_ping
            wsapp.on_pong = self.on_pong
            while True:
                #wsapp_stopped = wsapp.run_forever(ping_interval=self.heartbeat_interval, ping_timeout=10, ping_payload=json.dumps({"op":1,"d":"null"}))
                wsapp_stopped = wsapp.run_forever(ping_interval=self.heartbeat_interval, ping_timeout=10)
                print("wsapp stopped!")
        else:
            while True:
                wsapp_stopped = wsapp.run_forever() 
                print("wsapp stopped!")



# This is a script to test out WebSocketApp to work with Discord servers.
# Using a class including WebSocketApp instead of WebSocket for long lived websocket connection
# Inspired by CodeDict at YouTube: https://www.youtube.com/watch?v=dR9n1zmw-Go
dc = CDiscord_Scrape()

# Retrieve you Discord authorization token if you want to scrape text messages from the Discord forums in which you have membership.
# How to do this you can find in the CodeDict Youtube strip
# If you don't assign any token, you can anyway test the heartbeat / ping/pong protocol wihtout it as shown in the script test drivers below
token = 'insert_autorization_code_here' 



# Script test drivers. Pick the one you need for testing.
# Heartbeat version seems to work now
# PingPong version. Discord server always responds with op==9 after three pongs. 
#   Restart of run_forever() doesn't kill ping thread, instead a new thread is started for every restart.
#   Resume does not work either.
#   Actually there is no documentation on a Ping feature in the Gateway documentation of the Discord development, see https://discord.com/developers/docs/topics/gateway

dc.Run(token, PingPongEnable=False, HeartbeatEnable=True)
#dc.Run(PingPongEnable=False, HeartbeatEnable=True)
#dc.Run(token, PingPongEnable=True, HeartbeatEnable=False)
#dc.Run(PingPongEnable=True, HeartbeatEnable=False)
