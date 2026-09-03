from routes.helpers import *
from flask import Blueprint, render_template
import maps.maps as maps
import os
import importlib


app = Blueprint('locations', __name__, template_folder='templates')

def run_module(module):
	try:
		fn = importlib.import_module(module, package=None).main
		map = maps.available.map
		clusters = maps.available.map['allowed']
		computers = []
		for cluster in clusters:
			for line in map[cluster]:
				for computer in line:
					if len(computer) <= 3:
						continue
					computers.append(computer)
		try:
			print(f'Running {module}')
			fn(computers)
		except Exception as e:
			print('Computer error', e)
	except Exception as e:
		print('Module Error ', e)

@app.route('/modules/<token>')
def update_modules(token):
	if token != config.update_key:
		return 'Bad token', 400
	for folder in os.listdir('./modules/'):
		if '.py' in folder and '__' not in folder and 'module.py' not in folder:
			print("Running DEAD PC modules")
			run_module('modules.' + folder.replace('.py', ''))
	return 'OK', 200

@app.route('/modules/<token>/<module>')
def update_module(token, module):
	if token != config.update_key:
		return 'Bad token', 400
	run_module('modules.' + module)
	return 'OK', 200

@app.route('/locations/<token>')
def update_locs(token):
	if token != config.update_key:
		return 'Bad token', 400
	print("Running locations updates")
	locs()
	return 'OK', 200


@app.route('/locations/<token>/dbg')
def update_locs_dbg(token):
	if token != config.update_key:
		return 'Bad token', 400
	return locs()


@app.route('/goto/<pos>')
@auth_required
def goto_route(pos, userid):
	with Db("database.db") as db:
		campus_id = db.get_user_by_id(userid['userid'])['campus']
	if campus_id not in maps.available:
		return render_template('campus_refresh.html', campus_id=campus_id)
	data = maps.available[campus_id].exrypz(pos)
	if data and 'etage' in data and 'made' not in data['etage'].lower():
		data['etage'] = data['etage'].rstrip('A')
		data['etage'] = data['etage'].rstrip('B')
	if not data or 'etage' not in data or data['etage'] not in maps.available[campus_id].map['allowed']:
		return f"{pos} not found !!!", 404
	return make_response(redirect(f"/?cluster={data['etage']}&p={pos}", 307))


@app.route('/update_campus_id/')
@auth_required
def update_campus_id(userid):
	if r.get("campus_refreshed/" + str(userid['userid'])):
		return "Already refreshed, please wait 60s", 400
	ret_status, ret_data = api.get_unknown_user(userid['username'])
	if ret_status != 200:
		return "L'intra n'est pas disponible pour le moment, réessayez plus tard", 500
	r.set("campus_refreshed/" + str(userid['userid']), '1', ex=60)
	with Db("database.db") as db:
		db.create_user(ret_data, 1)
	return redirect('/', 307)
