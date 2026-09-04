from globals import *
from functools import wraps
from db import Db, Psql
import config
from flask import request, redirect, make_response, g
import json
import hashlib
import hmac
import time
import secrets
import datetime
import arrow
import zlib


def proxy_images(url: str, light=False):
    if not url:
        return "/static/img/unknown.jpg"
    if light:
        return url.replace('https://cdn.intra.42.fr/users/', 'https://friends.42paris.fr/proxy/resize/70/')
    if 'small' in url or 'medium' in url:
        return url.replace('https://cdn.intra.42.fr/users/', 'https://friends.42paris.fr/proxy/')
    return url.replace('https://cdn.intra.42.fr/users/', 'https://friends.42paris.fr/proxy/resize/512/')


def auth_required(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        token = request.cookies.get('token')
        db = Db("database.db")
        userid = db.get_user_by_bookie(token)

        if userid == 0:
            db.close()
            resp = make_response(redirect("/redirect_42", 307))
            resp.set_cookie("previous", str(request.url_rule), secure=True, max_age=None, httponly=True)
            return resp
        if db.is_banned(userid['userid']):
            return f"You are banned from this website.", 403
        details = db.get_user_by_id(userid['userid'])
        is_admin = db.is_admin(userid['userid'])
        theme = db.get_theme(userid['userid'])
        msg_unread = db.number_of_unread_msg(userid['userid'])
        db.close()
        userid['admin'] = is_admin
        userid['username'] = details['name']
        userid['theme'] = theme
        g.user = userid
        g.msg_count = msg_unread
        kwargs["userid"] = userid
        return function(*args, **kwargs)

    return wrapper


def gen_session():
    return secrets.token_urlsafe(30)


def create_hooks(app):
    @app.before_request
    def hook_session():
        if 'session' not in request.cookies:
            g.session = gen_session()
            g.set_session_cookie = True
        else:
            g.session = request.cookies['session']

    @app.after_request
    def after_request(response):
        if 'set_session_cookie' in g:
            response.set_cookie('session', g.session, None)
        return response


def create_csrf():
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    random = secrets.token_urlsafe(20)
    msg = timestamp + "," + random + ""
    signature = hmac.new(
        (config.csrf + g.session).encode('ascii'),
        msg=msg.encode('ascii'),
        digestmod=hashlib.sha256)
    return msg + ":" + signature.hexdigest()


def verify_csrf(csrf: str):
    if ':' not in csrf and ',' not in csrf:
        return False
    msg = csrf.split(':')[0]
    signature = csrf.split(':')[1]
    try:
        date = time.strptime(csrf.split(',')[0], '%Y-%m-%d-%H-%M-%S')
    except ValueError:
        return False
    if (time.time() - time.mktime(date)) > 1500:
        return False
    digest = hmac.new((config.secret + g.session).encode('ascii'), msg=msg.encode('ascii'),
                      digestmod=hashlib.sha256).hexdigest()
    return hmac.compare_digest(digest, signature)


def get_position(name):
    ret = r.get("USER>" + str(name))
    return ret.decode('utf-8') if ret is not None else None


def standard_cluster(pos):
    if pos and 'paul' in pos:
        pos = pos.replace('A', '')
        pos = pos.replace('B', '')
    return pos

def create_users(db, profiles):
    for elem in profiles:
        db.create_user(elem)
        if elem["location"]:
            db.delete_issues(elem['location'])
            old_location = r.get('PERM>' + str(elem['username']))
            if not old_location or old_location.decode("utf-8") != elem['location']:
                notif_friends = db.get_notifications_friends(elem['id'])
            r.set('USER>' + str(elem["id"]), elem["location"], ex=200)
            r.set('USER>' + str(elem['username']), elem["location"], ex=200)
            r.set('PERM>' + str(elem['username']), elem["location"])
    db.commit()


def get_last_pos(username):
    x = r.get('PERM>' + username)
    if not x:
        return 'Unknown'
    return x.decode('utf-8')


def get_cached_locations():
    locations = r.get("locations/1") or '[]'
    if locations[0] == 91 or locations[0] == '[':
        cache_tab = json.loads(locations)
    else:
        cache_tab = json.loads(zlib.decompress(locations).decode('utf-8'))
    return cache_tab


def get_last_update(campus=1):
    last_update = r.get("location_last_update/" + str(campus))
    success = r.get("location_success/" + str(campus))
    if last_update:
        return arrow.get(last_update.decode("utf-8")), success.decode("utf-8") == '1'
    return None, False

def is_shadow_banned(user: int, offender: int, c_db=None):
    db = c_db
    if c_db is None:
        db = Db("database.db")
    ret = db.is_shadow_banned(user, offender)
    if c_db is None:
        db.close()
    return ret

psql = Psql()
def locs():
    data = psql.get_crs()
    users = []
    for d in data:
        u = ratatouille.getUserByIDOrUsername(d[0])
        u["location"] = d[1].replace(".paris.42.school", "")
        users.append(u)
        time.sleep(0.2)
    with Db("database.db") as db:
        create_users(db, users)
    alluser_json = [a for a in users]
    r.set("locations/" + str(1), zlib.compress(json.dumps(alluser_json).encode('utf-8')))
    r.set("location_last_update/" + str(1), arrow.now().__str__())
    r.set("location_success/" + str(1), '1')
    return users, 200

def date_fmt_locale(date: str, fmt="DD/MM/YYYY HH:mm:ss"):
    if date is None:
        return arrow.now().to('local').format(fmt, locale='fr')
    if type(date) is not str:
        return '?'
    return arrow.get(date).to('local').format(fmt, locale='fr')


def date_relative(date, granularity=None):
    if granularity:
        return arrow.get(date).humanize(locale='fr', granularity=granularity)
    return arrow.get(date).humanize(locale='fr')


def find_keyword_project(keyword: str, group: False) -> list:
    db = Db("database.db")
    if group:
        projects = db.search_project_solo(keyword, False)
    else:
        projects = db.search_project(keyword)
    db.close()
    return projects
