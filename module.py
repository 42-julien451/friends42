import functools
from db import Db
from dataclasses import dataclass
import importlib
import maps.maps

campus_map = maps.maps.map_paris.map


class States:
	INFO = -1
	OK = 0
	WARNING = 1
	DEAD = 2


@dataclass
class Issue:
	module: str
	computer: str
	text: str = ""
	severity: int = 0
	icon_html: str = ""
	data: str = None


def insert(module: str, computer: str, text="", severity=0, icon_html='', data=None):
	with Db("database.db") as db:
		db.insert_issue(module, fix_computer_name(computer), text, severity, icon_html, data)
	return True


def mass_insert(data: list[Issue]):
	with Db("database.db") as db:
		for issue in data:
			db.insert_issue(issue.module, fix_computer_name(issue.computer), issue.text, issue.severity,
			                issue.icon_html, issue.data,
			                commit=False)
			db.commit()


def remove_latest(module: str, computer: str):
	with Db("database.db") as db:
		db.remove_latest(module, computer)
	return True


def get_module_logs(module: str, computer: str):
	with Db("database.db") as db:
		return db.get_mod_issues_specific(module, computer)


def get_module_py(name):
	try:
		fn = importlib.import_module('modules.' + name, package=None)
		return fn
	except:
		return False

def call_func(module, name, *args, **kwargs):
	mod = get_module_py(module)
	if not mod or not hasattr(mod, name):
		return False
	fn = getattr(mod, name)
	return fn(*args, **kwargs)


@functools.cache
def list_computers() -> list[str]:
	possible = []
	for cluster in campus_map['allowed']:
		for line in campus_map[cluster]:
			for dump in line:
				if len(dump) > 2:
					possible.append(dump)
	return possible


@functools.cache
def fix_computer_name(old: str) -> str:
	possibles: list[str] = list_computers()
	for possible in possibles:
		if possible.lower() == old.lower():
			return possible
	return old
