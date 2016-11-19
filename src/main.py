# Connects a MU bot to an SQL DB.

from mu_parser import MuParser
from sql_parser import SqlParser


def parse_address(address, default_port):
    split_address = address.split(":", 1)
    server = split_address[0]
    if len(split_address) == 2:
        try:
            port = int(split_address[1])
        except ValueError:
            print("Error for %s: Erroneous port." % address)
            return {}
    else:
        port = default_port

    return {'server': server, 'port': port}


class Communicator:
    def __init__(self, database_name, mu):
        self.mu_parser = MuParser(self)
        self.mu_parser.connect(mu['server'], mu['port'])
        self.sql_parser = SqlParser(database_name, self)

    def stop(self):
        self.mu_parser.disconnect()
        self.sql_parser.close()

    def raw_send_to_mu(self, line):
        self.mu_parser.do_raw_send(line)

    def query_for_pokemon_stats(self, callback_dbnum, partial_name):
        self.sql_parser.query_for_pokemon_stats(callback_dbnum, partial_name)

    def stats_not_found(self, callback_dbnum, partial_name):
        self.mu_parser.do_stats_not_found(callback_dbnum, partial_name)

    def stats_ambiguous_name(self, callback_dbnum, partial_name, names):
        self.mu_parser.do_stats_ambiguous_name(callback_dbnum, partial_name, names)

    def stats_success(self, callback_dbnum, partial_name, pokemon_name, stats):
        self.mu_parser.do_stats_success(callback_dbnum, partial_name, pokemon_name, stats)


def main():
    import sys
    if len(sys.argv) != 3:
        print("Usage: veebot <MU server[:port]> <database name>")
        sys.exit(1)

    mu = parse_address(sys.argv[1], 4201)
    database_name = sys.argv[2]

    communicator = Communicator(database_name, mu)

    try:
        while True:
            keyboard = input()
            if keyboard.startswith("m"):
                communicator.raw_send_to_mu(keyboard[1:])
            elif keyboard.startswith("q"):
                break
    except KeyboardInterrupt:
        pass

    communicator.stop()

if __name__ == "__main__":
    main()
