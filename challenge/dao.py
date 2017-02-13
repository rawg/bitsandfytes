# -*- coding: utf-8 -*-
"""


"""
import sqlite3
import os


dbfile = os.environ["FLASK_DB_FILE"] if "FLASK_DB_FILE" in os.environ else "data.db"

conn = sqlite3.connect(dbfile)
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
        merged int,
        success int default 0
    );
    """)
conn.commit()

def put_run(file_id, username, pairs, cats, merged, success):
    db.execute("""insert into runs (file_id, user, pairs, cats, merged, success)
              values (?, ?, ?, ?, ?, ?)""", (file_id, username, pairs, cats, merged, int(success)))
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

def runs():
    db.execute("""select name as filename, user, runs.dt_added, pairs, cats, merged
    from runs
    inner join files on runs.file_id = files.id
    where runs.success = 1
    order by 1, 4, 5""")
    ret = {}
    for row in db.fetchall():
        d = {}
        d["user"] = row[1]
        d["dt_added"] = row[2]
        d["pairs"] = row[3]
        d["cats"] = row[4]
        d["merged"] = row[5]
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
