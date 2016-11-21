import threading
from queue import PriorityQueue
import sqlite3


class SqlParser(threading.Thread):
    def __init__(self, database_name, mu_listener):
        self.database_name = database_name
        self.mu_listener = mu_listener
        self.queue = PriorityQueue()
        self.sql_connection = None
        self.cursor = None
        super().__init__()
        self.setName("SQL Parser")
        self.start()

    def close(self):
        self.queue.put((1, None))

    def run(self):
        self.sql_connection = sqlite3.connect(self.database_name)
        self.cursor = self.sql_connection.cursor()
        while True:
            item = self.queue.get()
            command = item[1]
            if command is None:
                self.sql_connection.close()
                break
            args = item[2]
            command_function = getattr(self, command)
            command_function(*args)

    def query_for_pokemon_stats(self, callback_dbnum, partial_name):
        self.queue.put((0, "_fetch_stats", [callback_dbnum, partial_name]))

    def _fetch_stats(self, callback_dbnum, partial_name):
        fetched_pokemon = self._match_pokemon_name(partial_name)

        if len(fetched_pokemon) == 0:
            self.mu_listener.stats_not_found(callback_dbnum, partial_name)
        elif len(fetched_pokemon) > 1:
            names = [pokemon[1] for pokemon in fetched_pokemon]
            self.mu_listener.stats_ambiguous_name(callback_dbnum, partial_name, names)
        else:
            pokemon = fetched_pokemon[0]
            stat_query = '''SELECT s.identifier, ps.base_stat FROM pokemon_stats AS ps, stats AS s
               WHERE NOT s.is_battle_only AND ps.stat_id = s.id AND ps.pokemon_id = ? ORDER BY s.id'''
            self.cursor.execute(stat_query, (pokemon[0], ))
            stat_rows = self.cursor.fetchall()

            pokemon_name = pokemon[1]
            stats = [stat[1] for stat in stat_rows]
            self.mu_listener.stats_success(callback_dbnum, partial_name, pokemon_name, stats)

    def _match_pokemon_name(self, partial_name):
        like_name = "%%%s%%" % partial_name
        for name in (partial_name, like_name):
            self.cursor.execute("SELECT id, identifier FROM pokemon WHERE identifier LIKE ?", (name,))
            rows = self.cursor.fetchall()
            if len(rows) > 0:
                return rows
        return []

    def query_for_move(self, callback_dbnum, partial_name):
        self.queue.put((0, "_fetch_move", [callback_dbnum, partial_name]))

    def _fetch_move(self, callback_dbnum, partial_name):
        fetched_move = self._match_move_name(partial_name)

        if len(fetched_move) == 0:
            self.mu_listener.move_not_found(callback_dbnum, partial_name)
        elif len(fetched_move) > 1:
            names = [move[1] for move in fetched_move]
            self.mu_listener.move_ambiguous_name(callback_dbnum, partial_name, names)
        else:
            move_id = fetched_move[0][0]
            move_query = '''SELECT mn.name, t.identifier, mdc.identifier, m.power, m.pp, m.accuracy, m.priority
                    FROM languages AS l, move_names AS mn, moves AS m, move_damage_classes AS mdc, types AS t
                    WHERE l.identifier == "en"
                    AND m.id == ?
                    AND mn.move_id == m.id
                    AND mn.local_language_id == l.id
                    AND m.damage_class_id == mdc.id
                    AND t.id == m.type_id'''
            self.cursor.execute(move_query, (move_id,))
            move_row = self.cursor.fetchone()
            self.mu_listener.move_success(callback_dbnum, partial_name, move_row)

    def _match_move_name(self, partial_name):
        match_move_name_query = '''SELECT m.id, mn.name
                FROM languages AS l, move_names AS mn, moves AS m
                WHERE l.identifier == "en"
                AND mn.local_language_id == l.id
                AND mn.name LIKE ?
                AND mn.move_id == m.id'''

        like_name = "%%%s%%" % partial_name
        for match_style in (partial_name, like_name):
            self.cursor.execute(match_move_name_query, (match_style,))
            rows = self.cursor.fetchall()
            if len(rows) > 0:
                return rows
        return []
