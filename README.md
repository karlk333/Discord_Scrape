# Discord_Scrape_wsapp_test


This is a script to test out WebSocketApp to work with Discord servers.
Using a class including WebSocketApp instead of WebSocket for long lived websocket connection
Inspired by CodeDict at YouTube: https://www.youtube.com/watch?v=dR9n1zmw-Go
dc = CDiscord_Scrape()

Retrieve you Discord authorization token if you want to scrape text messages from the Discord forums in which you have membership.
How to do this you can find in the CodeDict Youtube strip
If you don't assign any token, you can anyway test the heartbeat / ping/pong protocol wihtout it as shown in the script test drivers below
token = 'insert_autorization_code_here' 



Script test drivers. Pick the one you need for testing.

Heartbeat version seems to work now.

PingPong version:
  Discord server always responds with op==9 after three pongs. 
  Restart of run_forever() doesn't kill ping thread, instead a new thread is started for every restart.
  Resume does not work either.
  Actually there is no documentation on a Ping feature in the Gateway documentation of the Discord development, see https://discord.com/developers/docs/topics/gateway.
