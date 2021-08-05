#!/usr/bin/env python3

# =============================================================================
# Created at Hochschule Esslingen - University of Applied Sciences
# Department: Anwendungszentrum KEIM
# Author: Andreas Rößler
# Contact: emanuel.reichsoellner@hs-esslingen.de
# Date: February 2021
# License: MIT License
# =============================================================================
# This Script provides a WebServer to run the Simulation on a remote machine
# =============================================================================

from queue import Queue
import time
import threading
from http.server import ThreadingHTTPServer

from datetime import datetime
from Web.handler import HandlerFactory


class WebServer:
    def __init__(self):
        super(WebServer, self).__init__()
        self.sumo_data = {"time": datetime.now().strftime("%H:%M:%S")}

        self.dynamic = {}
        self.queue = Queue(maxsize=1)

        self.worker = threading.Thread(target=self.runInThread)
        self.worker.setDaemon(True)
        self.worker.start()

    def alive(self):
        return self.worker.is_alive()

    def shutdown(self):
        self.httpd.shutdown()
        self.httpd.server_close()
        print("WebServer shutdown done")

    def runInThread(self):
        cache = {}
        # get the handler CLASS!
        Handler = HandlerFactory(cache, self.dynamic, self.queue)
        try:
            time.sleep(0.5)
            server_address = ("", 8080)
            Handler.fillCache()
            # Handler.fillDynamic("/sumo", self.get_sumo)
            # Handler.fillCommand("run", self.run_sumo)
            # Handler.fillCommand("stop", self.stop_sumo)
            self.httpd = ThreadingHTTPServer(server_address, Handler)
            print("WebServer starting")
            self.httpd.serve_forever()
            print("WebServer returned")
        except Exception as e:
            print("Error in WebServer", e)

    def unload(self):
        threading.Thread(target=self.shutdown, daemon=True).start()
