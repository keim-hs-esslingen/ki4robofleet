#!/usr/bin/env python3

# =============================================================================
# Created at Hochschule Esslingen - University of Applied Sciences
# Department: Anwendungszentrum KEIM
# Author: Andreas Rößler
# Contact: emanuel.reichsoellner@hs-esslingen.de
# Date: February 2021
# License: MIT License
# =============================================================================
# Handler for the WebServer
# Check the Simulation-Status on: http://localhost:8080/index.html
# =============================================================================

from queue import Queue
from Web.updater import onChange
from datetime import datetime
from http.server import BaseHTTPRequestHandler
import os
import json


def readFile(filePath):
    f = open(filePath, "rb")
    content = f.read()
    f.close()
    return content


def contentType(ext):
    if ext == ".ico":
        return "image/x-icon"
    if ext == ".js":
        return "text/javascript"
    if ext == ".css":
        return "text/css"
    if ext == ".json":
        return "application/json"
    if ext == ".png":
        return "image/png"
    if ext == ".jpg":
        return "image/jpg"
    if ext == ".wav":
        return "audio/wav"
    return "text/html"


def HandlerFactory(cache: dict, dynamic: dict, cmdqueue: Queue):
    class Handler(BaseHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super(Handler, self).__init__(*args, **kwargs)

        def log_message(self, format, *args):
            pass

        def updateCache(filePath):
            nonlocal cache
            public_dir = os.path.join(os.path.dirname(__file__), "public")
            public_len = len(public_dir)
            urlPath = filePath[public_len:]
            cache[urlPath]["content"] = readFile(filePath)
            print("updated cache", filePath)
            onChange(filePath, Handler.updateCache)

        def fillCache():
            nonlocal cache
            cache = {}
            public_dir = os.path.join(os.path.dirname(__file__), "public")
            public_len = len(public_dir)
            print("cache", public_dir)
            for (dirpath, dirnames, filenames) in os.walk(public_dir):
                for f in filenames:
                    fileName, fileExtension = os.path.splitext(f)
                    print("Adding", f, fileName, fileExtension)
                    filePath = os.path.join(dirpath, f)
                    onChange(filePath, Handler.updateCache)
                    urlPath = filePath[public_len:]
                    cache[urlPath] = {
                        "content_type": contentType(fileExtension),
                        "content": readFile(filePath),
                    }
                    print("added", urlPath)

        def _set_headers(self, type):
            self.send_response(200)
            self.send_header("Content-type", type)
            self.end_headers()

        def _html(message):
            content = f"<html><body><h4>{message}</h4></body></html>"
            return content.encode("utf8")

        def do_GET(self):
            nonlocal cache, dynamic

            if self.path in dynamic:
                o = dynamic[self.path]
                jsonData = json.dumps(o)
                self._set_headers("application/json")
                self.wfile.write(jsonData.encode("utf8"))
                return
            if self.path in cache:
                co = cache[self.path]
                self._set_headers(co["content_type"])
                self.wfile.write(co["content"])
            else:
                self._set_headers("text/html")
                self.wfile.write(
                    Handler._html("This ({}) is not found.".format(self.path))
                )

        def do_HEAD(self):
            self._set_headers("text/html")

        def do_POST(self):
            nonlocal cmdqueue
            content_len = int(self.headers.get("Content-Length"))
            post_body = self.rfile.read(content_len)
            try:
                data = json.loads(post_body)
                o = {"path": self.path, "data": data}
                cmdqueue.put(o)
            except Exception as e:
                o = {"server error": str(e), "body": post_body}
            jsonData = json.dumps(o)
            self._set_headers("application/json")
            self.wfile.write(jsonData.encode("utf8"))

    return Handler
