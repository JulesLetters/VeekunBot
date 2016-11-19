import re
import threading
from queue import PriorityQueue

from mu_line_reader import MuLineReader


class MuParser:
    def __init__(self, sql_listener):
        self.line_reader = MuLineReader(self)
        self.sql = sql_listener
        self.queue = PriorityQueue()
        self.connected = False

    def connect(self, server, port):
        self.line_reader.connect(server, port)

    def disconnect(self):
        self.line_reader.disconnect()

    def do_raw_send(self, line):
        self.queue.put((0, line))

    def do_stats_not_found(self, callback_dbnum, partial_name):
        line = "@nspemit %s=No match found for '%s'" % (callback_dbnum, partial_name)
        self.queue.put((0, line))

    def do_stats_ambiguous_name(self, callback_dbnum, partial_name, names):
        string_names = '|'.join(names)
        line = "@nspemit %s=Multiple matches found for '%s':%%r[iter(%s, %%b%%b%%i0, |, %%r)]" % (callback_dbnum, partial_name, string_names)
        self.queue.put((0, line))

    def do_stats_success(self, callback_dbnum, partial_name, pokemon_name, stats):
        string_stats = ' '.join(str(i) for i in stats)
        line = "@nspemit %s=Stats for '%s': %s" % (callback_dbnum, pokemon_name, string_stats)
        self.queue.put((0, line))

    def __write_loop(self):
        while self.connected:
            line = self.queue.get()[1]
            if line is None:
                break
            self.line_reader.send_line(line)

        while not self.queue.empty():
            self.queue.get()

    def handle_connect(self, server, port):
        print("Connected to MU: %s:%s" % (server, port))
        self.connected = True
        t = threading.Thread(target=self.__write_loop)
        t.start()

    def handle_disconnect(self, server, port):
        self.connected = False
        self.queue.put((1, None))
        print("Disconnected from MU: %s:%s" % (server, port))

    def handle_line(self, line):
        print("MU: %s" % line)
        command_form = '\{ "command": "stats", "callback": (#\d+), "input": "([-\w\d ]+)" \}'
        command_match = re.match(command_form, line)
        if command_match:
            callback_dbnum = command_match.group(1)
            partial_pokemon_name = command_match.group(2)
            print("Running stat query on '%s' for '%s'" % (partial_pokemon_name, callback_dbnum))
            self.sql.query_for_pokemon_stats(callback_dbnum, partial_pokemon_name)
            return
