import threading
from telnetlib import Telnet


class MuLineReader:
    def __init__(self, listener):
        self.listener = listener

    def connect(self, server, port):
        print("Connecting to MU: %s:%s" % (server, port))
        t = threading.Thread(target=self.__read_from_telnet, args=(server, port))
        t.start()

    def disconnect(self):
        # self.telnet.close()
        self.send_line("QUIT")

    def send_line(self, message):
        self.telnet.write(message.encode('utf-8') + b"\n")

    def __read_from_telnet(self, server, port):
        self.telnet = Telnet(server, port)
        self.listener.handle_connect(server, port)

        try:
            while True:
                line = self.telnet.read_until(b"\n")
                # There is an obvious bug for servers returning \n
                clean_line = line[:-2].decode('latin1')
                self.listener.handle_line(clean_line)
        except EOFError:
            self.listener.handle_disconnect(server, port)
