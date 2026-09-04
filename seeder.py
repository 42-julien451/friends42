import json
import random
import redis
import zlib
import arrow
import sqlite3
from datetime import datetime, timedelta

r = redis.Redis(host="127.0.0.1", port=6379, db=0)

first_names = [
    "Lucas", "Emma", "Hugo", "Lea", "Nathan",
    "Chloe", "Louis", "Manon", "Arthur", "Camille"
]

last_names = [
    "Martin", "Bernard", "Thomas", "Robert", "Richard",
    "Petit", "Durand", "Leroy", "Moreau", "Simon"
]

floors = ["f0", "f1", "f1b", "f2", "f4", "f6"]

def random_date(start_year=2013, end_year=2025):
    start = datetime(start_year, 1, 1)
    end = datetime(end_year, 12, 31)

    delta = end - start
    random_seconds = random.randint(0, int(delta.total_seconds()))

    return start + timedelta(seconds=random_seconds)

def random_location():
    floor = random.choice(floors)
    row = random.randint(1, 13)
    seat = random.randint(1, 23)

    return f"{floor}r{row}s{seat}"

def generate_users(number):
    users = []

    for _ in range(number):
        first_name = random.choice(first_names)
        last_name = random.choice(last_names)

        username = (
            first_name[0].lower()
            + last_name.lower()
            + str(random.randint(1, 999))
        )

        start_at = random_date()

        end_at = start_at + timedelta(
            days=random.randint(1, 30),
        )

        user = {
            "access_status": "Active",
            "account_type": "42v2",
            "username": username,
            "first_name": first_name,
            "last_name": last_name,
            "id": str(random.randint(1000, 20999)),
            "location": random_location(),
            "profile_picture_url": "https://cdn.intra.42.fr/users/82f7920b4257569e28a0825392d6e598/moulinette.jpg",
            "status": "learner.student",
            "program_session_participations": [
                {
                    "campus_id": "paris",
                    "end_at": end_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "id": "290983",
                    "program": {
                        "id": "c-piscine",
                        "name": "C Piscine"
                    },
                    "start_at": start_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
                },
            ],
        }

        users.append(user)

    return users

def find_piscine_date(cursus):
    for c in cursus:
        if "c-piscine" in c["program"]["id"] or "piscine-c-decloisonnee" in c["program"]["id"]:
            start = datetime.fromisoformat(c['start_at'].replace("Z", "+00:00"))
            end = datetime.fromisoformat(c['end_at'].replace("Z", "+00:00"))
            month = start + (end - start) / 2
            return month.strftime("%B"), month.strftime("%Y")
    return "Error date", 42

def create_user(user_data: dict):
    con = sqlite3.connect("database.db")
    cur = con.cursor()
    def god(db, field, userid: int):
        """get old data"""
        return f"(SELECT {field} FROM {db} WHERE id = '{userid}')"

    active = "CURRENT_TIMESTAMP" if user_data["location"] else god('USERS', 'active', user_data["id"])
    pass
    if user_data["status"] == 'staff.campus':
        month, year = "January", 4242
    else:
        month, year = find_piscine_date(user_data['program_session_participations'])
    cur.execute(
        'INSERT OR REPLACE INTO USERS(id, name, image, pool, active) '
        f"VALUES(?, ?, ?, ?, {active})",
        [user_data["id"], user_data["username"], user_data["profile_picture_url"],
         f"{month} {year}"])
    con.commit()
    con.close()

def create_users(profiles):
    for elem in profiles:
        create_user(elem)
        if elem["location"]:
            r.set('USER>' + str(elem["id"]), elem["location"], ex=200)
            r.set('USER>' + str(elem['username']), elem["location"], ex=200)
            r.set('PERM>' + str(elem['username']), elem["location"])

NUMBER_OF_USERS = 100

data = generate_users(NUMBER_OF_USERS)
create_users(data)

alluser_json = [a for a in data]
r.set("locations/" + str(1), zlib.compress(json.dumps(data).encode('utf-8')))
r.set("location_last_update/" + str(1), arrow.now().__str__())
r.set("location_success/" + str(1), '1')
