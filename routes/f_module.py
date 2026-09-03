import module
from globals import *
from routes.helpers import *
from flask import Blueprint, render_template
import json
import os

app = Blueprint('modules', __name__, template_folder='templates')


def severity(issue):
	if issue == -1:
		return '<div class="text-primary"><i class="fa-solid fa-circle-right"></i>'
	elif issue == 1:
		return '<div class="text-warning"><i class="fa-solid fa-circle-exclamation"></i>'
	elif issue == 2:
		return '<div class="text-danger"><i class="fa-solid fa-circle-xmark"></i>'
	return '<div class="text-success"><i class="fa-solid fa-circle-check"></i>'


@app.route('/summary/<pc>', methods=['GET'])
@auth_required
def module_page(pc, userid):
	render_list = []
	for folder in os.listdir('./modules/'):
		if '.py' in folder and '__' not in folder and 'module.py' not in folder:
			module_name = folder.replace('.py', '')
			ret = module.call_func(module_name, 'html', pc)
			if ret is False:
				print(f'Module {module_name} not found or has no html()')
				continue
			render_list.append(ret)
	with Db() as db:
		summary = db.get_mod_issues(pc)
	return render_template("issues.html", render_list=render_list, computer=pc, summary=summary, severity=severity)
