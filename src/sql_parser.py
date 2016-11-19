import threading
import sqlite3


class SqlParser:
    def __init__(self, database_name, mu_listener):
        self.database_name = database_name
        self.mu_listener = mu_listener

    def close(self):
        # self.sql_connection.close()
        pass

    def query_for_pokemon_stats(self, callback_dbnum, partial_name):
        t = threading.Thread(target=self.__fetch_stats, args=(callback_dbnum, partial_name))
        t.start()

    def __fetch_stats(self, callback_dbnum, partial_name):
        sql_connection = sqlite3.connect(self.database_name)
        cursor = sql_connection.cursor()
        fetched_pokemon = self.__fetch_pokemon(cursor, partial_name)

        if len(fetched_pokemon) == 0:
            self.mu_listener.stats_not_found(callback_dbnum, partial_name)
        elif len(fetched_pokemon) > 1:
            names = [pokemon[1] for pokemon in fetched_pokemon]
            self.mu_listener.stats_ambiguous_name(callback_dbnum, partial_name, names)
        else:
            pokemon = fetched_pokemon[0]
            stat_query = '''SELECT s.identifier, ps.base_stat FROM pokemon_stats AS ps, stats AS s
               WHERE NOT s.is_battle_only AND ps.stat_id = s.id AND ps.pokemon_id = ? ORDER BY s.id'''
            cursor.execute(stat_query, (pokemon[0], ))
            stat_rows = cursor.fetchall()

            pokemon_name = pokemon[1]
            stats = [stat[1] for stat in stat_rows]
            self.mu_listener.stats_success(callback_dbnum, partial_name, pokemon_name, stats)

        sql_connection.close()

    def __fetch_pokemon(self, cursor, partial_name):
        like_name = "%%%s%%" % partial_name
        for name in (partial_name, like_name):
            cursor.execute("SELECT id, identifier FROM pokemon WHERE identifier LIKE ?", (name,))
            rows = cursor.fetchall()
            if len(rows) > 0:
                return rows
        return []
