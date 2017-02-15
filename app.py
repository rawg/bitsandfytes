# -*- coding: utf-8 -*-


import sqlite3
import hashlib
import os
import os.path
import tempfile

from challenge.validate import validate
from challenge import dao

from flask import (Flask, render_template, send_from_directory, request,
                   redirect, url_for, flash, session, send_from_directory,
                   make_response)
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "cURYjtPpVO6LzUO/mMndtw=="
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

ulpath = os.environ["FLASK_UL_PATH"] if "FLASK_UL_PATH" in os.environ else "data/sources/"
tmppath = os.environ["FLASK_TEMP_PATH"] if "FLASK_TEMP_PATH" in os.environ else "data/tmp/"


def md5(full_path):
    return hashlib.md5(open(full_path, 'rb').read()).hexdigest()

@app.route('/')
def index():
    runs = dao.runs()
    files = dao.files(keys=True)
    return render_template("index.html", runs=runs, files=files, navs=dao.navitems())

@app.route("/shame")
def shame():
    runs = dao.runs(success=False)
    files = dao.files(keys=True)
    return render_template("shame.html", runs=runs, files=files, navs=dao.navitems())

@app.route("/score", methods=["GET"])
def get_score():
    if "username" in request.cookies:
        username = request.cookies["username"]
    else:
        username = ""

    username_anon = dao.random_name()

    files = dao.files()
    return render_template("score.html", files=files, username=username, username_anon=username_anon, navs=dao.navitems())

@app.route("/score", methods=["POST"])
def post_score():
    ifile = request.files["file"]
    ntf = tempfile.NamedTemporaryFile(dir=ulpath, delete=True)
    fn = ntf.name
    ntf.close()
    ifile.save(fn)

    src = dao.file_by_id(request.form["source"])
    r = validate(src[3], fn)
    un = request.form["username"]
    if not un:
        un = request.form["username_anon"]
        if not un:
            un = dao.random_name()

    dao.put_run(src[0], un, r["pairs"], r["cats"], r["supercats"], r["merges"],
                r["success"], r["message"])

    if not r["success"]:
        flash(r["message"], "error")
    else:
        msg = "Removed %i pairs and %i categories. " % (r["pairs"], r["cats"])
        msg += "%i super categories detected" % r["supercats"]
        if int(r["merges"]) > 0:
            msg += " after at least %i merges." % r["merges"]
        else:
            msg += "."

        flash(msg, "success")

    response = make_response(redirect(url_for("get_score")))
    response.set_cookie("username", un)
    return response

@app.route("/sources", methods=["GET"])
def get_sources():
    return render_template("sources.html", navs=dao.navitems())

@app.route("/sources", methods=["POST"])
def post_source():
    f = request.files["file"]
    ntf = tempfile.NamedTemporaryFile(dir=ulpath, delete=True)
    fn = ntf.name
    ntf.close()

    f.save(fn)
    checksum = md5(fn)
    eh = dao.file_exists_hash(checksum)
    en = dao.file_exists_name(f.filename)

    if not eh and not en:
        dao.putfile(fn, f.filename, request.form["descr"], checksum)
    else:
        flash("This file has already been uploaded", "error")

    return redirect(url_for("get_sources"))

@app.route("/sources/<path:source>")
def get_source(source):
    f = dao.file_by_id(source)
    base = os.path.basename(f[3])
    return send_from_directory(ulpath, base, as_attachment=True, attachment_filename=f[1])

@app.route('/<path:filename>')
def all_static(filename):
    return send_from_directory("static", filename)

@app.route("/nav/<item>/<enabled>")
def nav_item(item, enabled):
    dao.set_nav(str(item), int(enabled))
    return redirect(url_for("index"))
