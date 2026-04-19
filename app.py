# -*- coding: utf-8 -*-
"""
CTKM Training - PNJ Store 1305
Flask app with auth + role-based access for CTKM training pages.
"""

import os
import sqlite3
from functools import wraps

from flask import (
    Flask, g, redirect, render_template, request, session, url_for, send_file,
    abort,
)
from werkzeug.security import check_password_hash

# ---------------------------------------------------------------------------
# App config
# ---------------------------------------------------------------------------
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "pnj-ctkm-training-1305-secret")
app.config["JSON_AS_ASCII"] = False

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "phieu_ck.db")
PORT = 5051

# ---------------------------------------------------------------------------
# CTKM registry — moi CTKM la 1 dict
# allowed_roles: list role duoc xem. ["*"] = tat ca.
# ---------------------------------------------------------------------------
CTKM_LIST = [
    {
        "slug": "sn-38-nam-pnj",
        "title": "SINH NHẬT PNJ 38 NĂM",
        "subtitle": "Vững Niềm Tin, Sáng Giá Trị",
        "desc": "Combo ưu đãi lên đến 38 triệu. 7 chương trình: Top Doanh thu, Combo giảm giá, Đón Sinh nhật, Birthday Pass, Bình giữ nhiệt, Hóa đơn kế tiếp, Sản phẩm chọn lọc.",
        "date_range": "10/04 - 03/05/2026",
        "status": "active",
        "channel": "Offline + Online",
        "icon": "38",
        "color": "#A08030",
        "accent": "#C8A850",
        "allowed_roles": ["*"],
    },
]

# ---------------------------------------------------------------------------
# Database helpers (pattern tu phieu-ck-app)
# ---------------------------------------------------------------------------

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA journal_mode=WAL")
    return g.db


@app.teardown_appcontext
def close_db(exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()


# ---------------------------------------------------------------------------
# Auth helpers
# ---------------------------------------------------------------------------

def get_current_user():
    if "user_id" not in session:
        return None
    db = get_db()
    user = db.execute("SELECT * FROM users WHERE id = ?", (session["user_id"],)).fetchone()
    return user


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session and session.get("role") != "guest":
            return redirect(url_for("login", next=request.path))
        return f(*args, **kwargs)
    return decorated


def get_visible_ctkm(role):
    if role == "admin":
        return CTKM_LIST
    return [c for c in CTKM_LIST if "*" in c["allowed_roles"] or role in c["allowed_roles"]]


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/ctkm/login", methods=["GET", "POST"])
def login():
    if "user_id" in session or session.get("role") == "guest":
        return redirect(url_for("ctkm_index"))

    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        db = get_db()
        user = db.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["role"] = user["role"]
            next_url = request.args.get("next") or url_for("ctkm_index")
            return redirect(next_url)
        error = "Sai tai khoan hoac mat khau"

    return render_template("login.html", error=error)


@app.route("/ctkm/guest")
def guest_login():
    session.clear()
    session["username"] = "Khách"
    session["role"] = "guest"
    return redirect(url_for("ctkm_index"))


@app.route("/ctkm/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/ctkm/")
@login_required
def ctkm_index():
    role = session.get("role", "guest")
    user = get_current_user() if "user_id" in session else None
    user_info = {
        "username": session.get("username", "Khách"),
        "role": role,
    }
    ctkm_visible = get_visible_ctkm(role)
    return render_template("ctkm_list.html", user=user_info, ctkm_list=ctkm_visible)


@app.route("/ctkm/<slug>/")
@login_required
def ctkm_detail(slug):
    role = session.get("role", "guest")
    ctkm = next((c for c in CTKM_LIST if c["slug"] == slug), None)
    if not ctkm:
        abort(404)
    if role != "admin" and "*" not in ctkm["allowed_roles"] and role not in ctkm["allowed_roles"]:
        abort(403)
    file_path = os.path.join(app.static_folder, "ctkm", slug, "index.html")
    if not os.path.isfile(file_path):
        abort(404)
    return send_file(file_path)


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT, debug=True)
