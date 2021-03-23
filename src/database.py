from cuttlepool import CuttlePool

import sqlite3


class SQLitePool(CuttlePool):
    def normalize_resource(self, resource):
        resource.row_factory = None
    
    def ping(self, resource):
        try:
            rv = resource.execute('SELECT 1').fetchall()
            return (1,) in rv
        except sqlite3.Error:
            return False

pool = SQLitePool(
    factory=sqlite3.connect,
    database='database.db',
    capacity=25
)

def migrate():
    with pool.get_resource() as con:
        cursor = con.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS challenges (
                id INTEGER PRIMARY KEY,
                name TEXT UNIQUE,
                value INTEGER,
                category TEXT,
                CREATED_AT DATETIME
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS hINTEGERs (
                id INTEGER PRIMARY KEY,
                content TEXT
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS teams (
                id INTEGER PRIMARY KEY,
                name TEXT UNIQUE
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS challenges (
                id INTEGER PRIMARY KEY,
                name TEXT UNIQUE,
                value INTEGER,
                CREATED_AT DATETIME
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS submissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                challenge_id INTEGER,
                team_id INTEGER,
                SUBMITTED_ON DATETIME,
                UNIQUE(challenge_id, team_id)
            )
        """)

        con.commit()

def add_challenge(id, name, value, category):
    with pool.get_resource() as con:
        cursor = con.cursor()

        try:
            cursor.execute('''
                INSERT INTO challenges VALUES (?, ?, ?, ?, 0)
            ''', (id, name, value, category))

            con.commit()    
            return True

        except Exception as e:
            ''' Challenge existed '''
            return False

def update_challenge(id, name, value, category):
    with pool.get_resource() as con:
        cursor = con.cursor()

        try:
            cursor.execute('''
                UPDATE challenges SET name = ?, value = ?, category = ?, CREATED_AT = 0 where id = ?
            ''', (name, value, category, id))

            con.commit()    
            return True

        except Exception as e:
            ''' Failed update challenge '''
            return False

def get_challenge_by_id(challenge_id):
    with pool.get_resource() as con:
        cursor = con.cursor()
        cursor.execute('''
            SELECT * FROM challenges where id=?
        ''', (challenge_id, ))

        return cursor.fetchall() 

def get_challenge():
    with pool.get_resource() as con:
        cursor = con.cursor()
        cursor.execute('''
            SELECT id, name FROM challenges
        ''')

        return cursor.fetchall()

def add_team(team_id, team_name):
    with pool.get_resource() as con:
        cursor = con.cursor()

        try:
            cursor.execute('''
                INSERT INTO teams VALUES (?, ?)
            ''', (team_id, team_name))

            con.commit()

        except Exception:
            ''' Team existed'''
            pass

def get_team_name(team_id):
    with pool.get_resource() as con:
        cursor = con.cursor()
        cursor.execute('''
            SELECT name from teams where id=?
        ''', (team_id, ))

        return cursor.fetchall()[0]

def add_submission(challenge_id, team_id, timestamp):
    with pool.get_resource() as con:
        cursor = con.cursor()

        try:
            cursor.execute('''
                INSERT INTO submissions VALUES (NULL, ?, ?, ?)
            ''', (team_id, challenge_id, timestamp))

            con.commit()
            return True

        except Exception as e:
            ''' Submission existed'''
            return False

def get_challenge_solve(challenge_id):
    with pool.get_resource() as con:
        cursor = con.cursor()
        cursor.execute('''
            SELECT teams.name FROM submissions INNER JOIN submissions.team_id=teams.id
        ''')

        return cursor.fetchall()[0]