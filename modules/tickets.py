import json
import module
from flask import render_template_string


def main(computers):
	return False


def html(pc):
	logs = module.get_module_logs('Tickets', pc)
	for log in logs:
		if log['data'][0] == '{':
			log['data'] = json.loads(log['data'])
	return render_template_string("""
	<table>
		<thead>
			<tr>
				<th>Issue</th>
				<th>Ticket</th>
			</tr>
		</thead>
		<tbody>
			{% for log in logs %}
				<tr>
					<td>{{log.text}}</td>
					<td>{{log.data.link}}</td>
				</tr>
			{% endfor %}
		</tbody>
	</table>
	""", pc=pc, logs=logs)
