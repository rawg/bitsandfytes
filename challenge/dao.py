# -*- coding: utf-8 -*-
"""


"""
import os
import random
import sqlite3


dbfile = os.environ["FLASK_DB_FILE"] if "FLASK_DB_FILE" in os.environ else "data/data.db"
namesfile = os.environ["FLASK_NAMES_FILE"] if "FLASK_NAMES_FILE" in os.environ else "data/names.txt"

conn = sqlite3.connect(dbfile, check_same_thread=False)
db = conn.cursor()
db.execute("""
    CREATE TABLE IF NOT EXISTS files (
        id integer primary key autoincrement,
        path text,
        name text,
        descr text,
        md5 text,
        dt_added datetime default current_timestamp
    );
    """)
db.execute("""
    CREATE TABLE IF NOT EXISTS runs (
        id integer primary key autoincrement,
        file_id text,
        user text,
        dt_added datetime default current_timestamp,
        pairs int,
        cats int,
        supercats int,
        merges int,
        success int default 0,
        message text
    );
    """)
db.execute("""
    CREATE TABLE IF NOT EXISTS navitems (
        item text primary key,
        enabled default 0
    );
    """)
conn.commit()

def navitems():
    db.execute("select item, enabled from navitems")
    ret = {}
    for r in db.fetchall():
        ret[r[0]] = bool(r[1])
    return ret

def set_nav(item, enabled):
    db.execute("insert or replace into navitems (item, enabled) values (?, ?)", (item, int(enabled)))
    conn.commit()

def put_run(file_id, username, pairs, cats, supercats, merges, success, message):
    db.execute("""insert into runs (file_id, user, pairs, cats, supercats, merges, success, message)
              values (?, ?, ?, ?, ?, ?, ?, ?)""", (file_id, username, pairs, cats, supercats, merges, int(success), message))
    conn.commit()

def files(keys=False):
    if keys:
        db.execute("select id, name, md5, descr from files order by dt_added asc")
        ret = {}
        for row in db.fetchall():
            ret.setdefault(row[1], {})
            ret[row[1]]["id"] = row[0]
            ret[row[1]]["name"] = row[1]
            ret[row[1]]["md5"] = row[2]
            ret[row[1]]["descr"] = row[3]

        return ret

    else:
        db.execute("select id, name, md5, descr from files order by dt_added asc")
        return db.fetchall()

def runs(success=True):
    db.execute("""select name as filename, user, runs.dt_added, pairs, cats, supercats, merges, message
        from runs
        inner join files on runs.file_id = files.id
        where runs.success = ?
        order by 1, 4, 5""", (int(success), ))

    ret = {}
    for row in db.fetchall():
        d = {}
        d["user"] = row[1]
        d["dt_added"] = row[2]
        d["pairs"] = row[3]
        d["cats"] = row[4]
        d["supercats"] = row[5]
        d["merges"] = row[6]
        d["message"] = row[7]
        ret.setdefault(row[0], [])
        ret[row[0]].append(d)
    return ret

def putfile(path, name, descr, checksum):
    db.execute("insert into files (id, path, name, descr, md5) values (null, ?, ?, ?, ?)", (path, name, descr, checksum))
    conn.commit()

def file_exists_hash(checksum):
    db.execute("select id from files where md5 = ?", (checksum, ))
    r = db.fetchone()
    return r is not None

def file_exists_name(filename):
    db.execute("select id from files where name = ?", (filename, ))
    r = db.fetchone()
    return r is not None

def file_by_id(idx):
    db.execute("select id, name, md5, path from files where id = ?", (idx, ))
    return db.fetchone()

def random_name():
    with open(namesfile) as f:
        lines = f.read().splitlines()
        return random.choice(lines)

    return "Uncertain Urn"
