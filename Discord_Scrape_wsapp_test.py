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


    def on_message(self, wsapp, message):
        self.event = json.loads(message)

        if "heartbeat_interval" in self.event['d']:
            self.heartbeat_interval = self.event['d']['heartbeat_interval'] / 1000
            print(f"heartbeat_interval received: {self.heartbeat_interval}s")

        if "author" in self.event['d']:
            guild_id  = self.event['d']['guild_id']
            guildJSON = self.retrieve_guild(guild_id)
            print(f"{guildJSON['name']}.{self.event['d']['author']['username']}: {self.event['d']['content']}")
            op_code = self.event['op']
            if op_code == 11:
                print('Heartbeat received')


    def on_error(self, wsapp, error):
        print(error)

    def on_close(self, wsapp, close_status_code, close_msg):
        print("### closed ###")

    def on_ping(self, wsapp, message):
        print("Got a ping! A pong reply has already been automatically sent.")

    def on_pong(self, wsapp, message):
        print("Got a pong! No need to respond")

    def on_open(self, wsapp):
        self.heartbeat_interval = 40    # Initial hearbeat_interval, will be overwritten/assigned in on_message() once ['d']['hearbeat_interval'] is received
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
            payload = {
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
            wsapp.send(json.dumps(payload))


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

        websocket.enableTrace(False)
        
        wsapp = websocket.WebSocketApp('wss://gateway.discord.gg/?v=9&encoding=json',
                                        on_message=self.on_message, 
                                        on_error=self.on_error, 
                                        on_close=self.on_close)
        
        wsapp.on_open = self.on_open
        if PingPongEnable:
            wsapp.on_ping = self.on_ping
            wsapp.on_pong = self.on_pong
            wsapp.run_forever(ping_interval=self.heartbeat_interval, ping_timeout=10, ping_payload=json.dumps({"op":1,"d":"null"})) 
        else:
            wsapp.run_forever() 


# This is a script to test out WebSocketApp to work with Discord servers.
# Using a class including WebSocketApp instead of WebSocket for long lived websocket connection
# Inspired by CodeDict at YouTube: https://www.youtube.com/watch?v=dR9n1zmw-Go
dc = CDiscord_Scrape()

# Retrieve you Discord authorization token if you want to scrape text messages from the Discord forums in which you have membership.
# How to do this you can find in the CodeDict Youtube strip
# If you don't assign any token, you can anyway test the heartbeat / ping/pong protocol wihtout it as shown in the script test drivers below
#token = 'insert_autorization_code_here_and_remove_#' 

# Script test drivers. Pick the one you need for testing.
# Heartbeat version still throws back warning message: argument of type 'NoneType' is not iterable
# PingPong version works without any warning messages.
#dc.Run(token, PingPongEnable=False, HeartbeatEnable=True)
#dc.Run(PingPongEnable=False, HeartbeatEnable=True)
#dc.Run(token, PingPongEnable=True, HeartbeatEnable=False)
dc.Run(PingPongEnable=True, HeartbeatEnable=False)
