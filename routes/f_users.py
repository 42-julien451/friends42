from globals import *
from routes.helpers import *
from flask import Blueprint, make_response

app = Blueprint('users', __name__, template_folder='templates')

#TODO: Stocker dans la DB si v2v3/next (isnext)
@app.route('/getuser/<username>')
@auth_required
def getuser(username, userid):
	with Db() as db:
		user = db.get_user_profile(username, api)
		if user is None:
			return '', 404
		is_friend = db.is_friend(userid['userid'], user['id'])
		user['is_friend'] = is_friend
		user["position"] = get_position(user['name'])
		user["image"] = proxy_images(user["image"])
	return dict(user)


@app.route('/settings/profile', methods=['POST'])
@auth_required
def settings_profile(userid):
	info = request.json
	if info is None:
		return 400
	db = Db("database.db")
	if db.is_banned(userid['userid']):
		return 'banned', 403
	success = db.set_profile(userid['userid'], dict(info))
	db.close()
	if not success:
		return '', 400
	return redirect('/settings/', 307)
