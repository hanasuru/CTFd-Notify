from cuttlepool import CuttlePool

import sqlite3
import mysql.connector
import os


class SQLitePool(CuttlePool):
    def normalize_resource(self, resource):
        resource.row_factory = None
    
    def ping(self, resource):
        try:
            rv = resource.execute('SELECT 1').fetchall()
            return (1,) in rv
        except sqlite3.Error:
            return False

class MySQLPool():
    def get_resource(self):
        dbconfig = {
            "database": os.getenv('DB_NAME'),
            "user": os.getenv('DB_USER'),
            "password": os.getenv('DB_PASSWORD')
        }
        cnx = mysql.connector.connect(**dbconfig)
        return cnx

driver = os.getenv('DB_DRIVER')
if driver == 'mysql':
    pool = MySQLPool()
elif driver == 'sqlite':
    pool = SQLitePool(
        factory=sqlite3.connect,
        database='database.db',
        capacity=25
    )
else:
    pool = MySQLPool()

def migrate():
    if driver == 'sqlite':
        # Not implemented
        pass
    else:
        migrate_mysql()

def migrate_mysql():
    con = pool.get_resource()
    cursor = con.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS challenges (
            id INTEGER PRIMARY KEY,
            name VARCHAR(255) UNIQUE,
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
            name VARCHAR(255) UNIQUE
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS challenges (
            id INTEGER PRIMARY KEY,
            name VARCHAR(255) UNIQUE,
            value INTEGER,
            CREATED_AT DATETIME
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS submissions (
            id INTEGER PRIMARY KEY AUTO_INCREMENT,
            challenge_id INTEGER,
            team_id INTEGER,
            SUBMITTED_ON DATETIME,
            UNIQUE(challenge_id, team_id)
        )
    """)

    con.commit()

def add_challenge(id, name, value, category):
    con = pool.get_resource()
    cursor = con.cursor()

    try:
        cursor.execute('''
            INSERT INTO challenges VALUES (%s, %s, %s, %s, 0)
        ''', (id, name, value, category))

        con.commit()    
        return True

    except Exception as e:
        ''' Challenge existed '''
        return False

def update_challenge(id, name, value, category):
    con = pool.get_resource()
    cursor = con.cursor()

    try:
        cursor.execute('''
            UPDATE challenges SET name = %s, value = %s, category = %s, CREATED_AT = 0 where id = %s
        ''', (name, value, category, id))

        con.commit()    
        return True

    except Exception as e:
        ''' Failed update challenge '''
        return False

def get_challenge_by_id(challenge_id):
    con = pool.get_resource()
    cursor = con.cursor()
    cursor.execute('''
        SELECT * FROM challenges where id=%s
    ''', (challenge_id, ))

    return cursor.fetchall() 

def get_challenge():
    con = pool.get_resource()
    cursor = con.cursor()
    cursor.execute('''
        SELECT id, name FROM challenges
    ''')

    return cursor.fetchall()

def add_team(team_id, team_name):
    con = pool.get_resource()
    cursor = con.cursor()

    try:
        cursor.execute('''
            INSERT INTO teams VALUES (%s, %s)
        ''', (team_id, team_name))

        con.commit()

    except Exception:
        ''' Team existed'''
        pass

def get_team_name(team_id):
    con = pool.get_resource()
    cursor = con.cursor()
    cursor.execute('''
        SELECT name from teams where id=%s
    ''', (team_id, ))

    return cursor.fetchall()[0]

def add_submission(challenge_id, team_id, timestamp):
    con = pool.get_resource()
    cursor = con.cursor()

    try:
        cursor.execute('''
            INSERT INTO submissions VALUES (NULL, %s, %s, %s)
        ''', (team_id, challenge_id, timestamp))

        con.commit()
        return True

    except Exception as e:
        ''' Submission existed'''
        return False

def get_challenge_solve(challenge_id):
    con = pool.get_resource()
    cursor = con.cursor()
    cursor.execute('''
        SELECT teams.name FROM submissions INNER JOIN submissions.team_id=teams.id
    ''')

    return cursor.fetchall()[0]