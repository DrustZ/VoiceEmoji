import os
import json
import signal
import base64
import logging
import subprocess

import tornado.web
import tornado.ioloop
import tornado.options
import tornado.websocket
import tornado.autoreload
from tornado import gen
import time 
from datetime import datetime

from TextProcessor import TextProcessor
from EmojiPredictor import EmojiPredictor
from CHNTextProcessor import CHNTextProcessor
from Recognizer import GoogleSpeechRecognizer


#this is the backend server
#for both running the front static web interface
#and the voice data processing

root = os.path.dirname(__file__)

speechRecognizer = GoogleSpeechRecognizer()
ep = EmojiPredictor()
textProcessor = TextProcessor(ep)
CHNtextProcessor = CHNTextProcessor(ep)

'''
Handler for chatting related websocket
'''
class SocketHandler(tornado.websocket.WebSocketHandler):
    waiters = set()

    def check_origin(self, origin):
        return True

    def open(self):
        self.useradded = False
        self.uname = ""
        SocketHandler.waiters.add(self)

    def on_close(self):
        SocketHandler.waiters.remove(self)
        msg = {"type":"user left", "username":self.uname, "numUsers":len(SocketHandler.waiters)}
        SocketHandler.send_updates(tornado.escape.json_encode(msg))

    @classmethod
    def send_updates(cls, msg, exclude=None):
        # print("sending message to %d waiters" % len(cls.waiters))
        for waiter in cls.waiters:
            if waiter.uname == exclude:
                continue
            try:
                waiter.write_message(msg)
            except:
                print("Error sending message")

    def on_message(self, message):
        parsed = tornado.escape.json_decode(message)
        #user joined
        if parsed["type"] == "add user" and not self.useradded:
            self.uname = parsed["uname"]
            self.adduser = True
            msg = {"type":"login", "numUsers":len(SocketHandler.waiters)}
            self.write_message(msg)
            msg = {"type":"user joined", "username":self.uname, "numUsers":len(SocketHandler.waiters)}
            SocketHandler.send_updates(tornado.escape.json_encode(msg), self.uname)
        #user typing
        if parsed["type"] == "typing":
            msg = {"type":"typing", "username":self.uname}
            SocketHandler.send_updates(tornado.escape.json_encode(msg), self.uname)
        #on stop typing
        if parsed["type"] == "stop typing":
            msg = {"type":"stop typing", "username":self.uname}
            SocketHandler.send_updates(tornado.escape.json_encode(msg), self.uname)
        #on new message
        if parsed["type"] == "new message":
            msg = {"type":"new message", "username":self.uname, "message":parsed["message"]}
            SocketHandler.send_updates(tornado.escape.json_encode(msg), self.uname)


#handler for voice process
class DataHandler(tornado.web.RequestHandler):
    def prepare(self):
        if self.request.headers.get("Content-Type", "").startswith("application/json"):
            self.json_args = tornado.escape.json_decode(self.request.body)
        else:
            self.json_args = None

    def set_default_headers(self):
        # print ("setting headers!!!")
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Headers", "Origin, X-Requested-With, Content-Type, Accept")
        self.set_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
        self.set_header('Content-Type', 'application/json; charset=UTF-8')

    def get(self):
        self.write("Hello, world")

    @gen.coroutine
    def post(self):
        if self.json_args != None:
            remote_ip = self.request.headers.get("X-Real-IP") or \
            self.request.headers.get("X-Forwarded-For") or \
            self.request.remote_ip

            request_time = millis = int(round(time.time() * 1000))
            if not os.path.exists('audios'):
                os.makedirs('audios')
            logstr = ""
            if "message" in self.json_args:
                fname = "audios/"+time.strftime("%m%d-%H_%M_%S")
                with open("%s.wav" % fname, "wb") as fh:
                    fh.write(base64.decodebytes(self.json_args["message"].encode("utf-8")))
                subprocess.call(['ffmpeg', '-i', "%s.wav"%fname, '-c:a', 'flac',
                   '-vn','-ac', '1', '-ar', '16k', '%s.flac'%fname])
                self.set_status(201)
                speechRecognizer.language_code = self.json_args["language"]
                content = speechRecognizer.recognize("%s.flac"%fname)
                print("[recognized]: "+str(content))
                os.remove('%s.flac'%fname)
                os.remove('%s.wav'%fname)
                if self.json_args["language"] == 'en-US':
                    res = textProcessor.processText(self.json_args["premessage"], content)
                else:
                    res = CHNtextProcessor.processText(self.json_args["premessage"], content)
                print(res)
                request_time = int(round(time.time() * 1000))-request_time
                print("[Time] %d" % request_time)
                with open("log.txt", "a", encoding="utf-8") as myfile:
                    myfile.write("%s\t%s\t%d\t%s\n" % 
                    (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), remote_ip, request_time, str(res)))
                self.write(json.dumps(res))
            elif "contents" in self.json_args:
                content = self.json_args["contents"]
                print ('[msg] %s' % content)
                if CHNtextProcessor.isCHN(content):
                    res = CHNtextProcessor.processText('', self.json_args["contents"])
                else:
                    res = textProcessor.processText('', self.json_args["contents"])
                with open("log.txt", "a", encoding="utf-8") as myfile:
                    myfile.write(str(res)+"\n")
                print(res)
                self.set_status(201)
                self.write(json.dumps(res))
                

class MyApplication(tornado.web.Application):
    is_closing = False

    def signal_handler(self, signum, frame):
        logging.info('exiting...')
        self.is_closing = True

    def try_exit(self):
        if self.is_closing:
            # clean up here
            tornado.ioloop.IOLoop.instance().stop()
            logging.info('exit success')


def make_app():
    #cn.html for Chinese web interface, index.html for English
    return MyApplication([
        (r"/()", tornado.web.StaticFileHandler, {"path": root, "default_filename": "index.html"}),
        (r"/(.*\.html)", tornado.web.StaticFileHandler, {"path": root}),
        (r"/(.*\.png)", tornado.web.StaticFileHandler,{"path": root }),
        (r"/(.*\.jpg)", tornado.web.StaticFileHandler,{"path": root }),
        (r"/(.*\.mp3)", tornado.web.StaticFileHandler,{"path": root }),
        (r"/(.*\.js)", tornado.web.StaticFileHandler,{"path": root }),
        (r"/(.*\.css)", tornado.web.StaticFileHandler,{"path": root }),
        (r"/(.*\.json)", tornado.web.StaticFileHandler,{"path": root }),
        (r"/ws", SocketHandler),
        (r"/messages", DataHandler),
    ], debug=True)

if __name__ == "__main__":
    app = make_app()
    # app.listen(8080)
    # you need to generate your own crt for https options
    # as voice process need to pass through https cert
    # your can use free services such as Let's Encrypt
    http_server = tornado.httpserver.HTTPServer(app, ssl_options={
        "certfile": "certs/server.crt",
        "keyfile": "certs/server.key",
    })
    http_server.listen(443)
    #http_server.listen(8080)
    print ("listen...")

    tornado.autoreload.start()
    for dir, _, files in os.walk('.'):
        for f in files:
            if (not f.startswith('.')) and (not f.endswith("txt")):
                tornado.autoreload.watch(dir + '/' + f) 

    tornado.ioloop.PeriodicCallback(app.try_exit, 200).start()
    tornado.ioloop.IOLoop.current().start()

# python -W ignore server.py