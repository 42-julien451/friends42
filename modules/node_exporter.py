import module
import requests
import config
from icmplib import multiping, resolve
from prometheus_client.parser import text_string_to_metric_families
from requests.auth import HTTPBasicAuth
import concurrent.futures as futures
import urllib3


def worker(computer, basic):
	issues = []
	try:
		metrics = requests.get(f'http://{computer}.paris.42.school:9100/metrics', verify=False, timeout=1)
	except:
		print('node_exporter fail')
		return []
	if metrics.status_code != 200:
		print('node_exporter fail')
		return []
	metrics = metrics.text

	for family in text_string_to_metric_families(metrics):
		for sample in family.samples:
			# print("Name: {0} Labels: {1} Value: {2}".format(*sample))
			if sample[0] == 'node_hwmon_temp_celsius' and sample[2] >= 88:
				issues.append(
					module.Issue("Temperature", computer, f"{sample[1]['chip']} -> {sample[2]}", module.States.WARNING,
					             '<i class="fa-solid fa-temperature-three-quarters text-warning"></i>'))
				break
			elif sample[0] == 'node_network_info' and sample[1]['operstate'] == 'up' and sample[1]['device'].startswith(
					"enp"):
				if sample[1]['duplex'] != 'full':
					issues.append(
						module.Issue("Ethernet", computer, f"{sample[1]['duplex']} duplex", module.States.WARNING,
						             '<i class="fa-solid fa-ethernet text-warning"></i>'))
				issues.append(module.Issue("MAC", computer, f"{sample[1]['address']}", module.States.INFO))
				break
			elif sample[0] == 'node_network_carrier_down_changes_total' and sample[1]['device'].startswith('enp') and \
					sample[2] > 5:
				issues.append(module.Issue("Flapping", computer, f"{sample[2]} flaps", module.States.WARNING,
				                           '<i class="fa-solid fa-ethernet text-danger"></i>'))
				break
			elif sample[0] == 'node_network_speed_bytes' and sample[1]['device'].startswith('enp') and sample[
				2] < 1.25e7:
				issues.append(module.Issue("Speed", computer, f"{sample[2] / 125000}mbps", module.States.WARNING,
				                           '<i class="fa-solid fa-ethernet text-danger"></i>'))
				break

	return issues


def main(computers):
	print("Running module node_exporter")
	urllib3.disable_warnings(category=urllib3.exceptions.InsecureRequestWarning)
	executor = futures.ThreadPoolExecutor(max_workers=20)
	basic = HTTPBasicAuth(config.node_user, config.node_pwd)
	issues = []
	res = [executor.submit(worker, computer, basic) for computer in computers]
	executor.shutdown()
	for result in res:
		issues += result.result()
	module.remove_latest('Temperature', '%')
	module.remove_latest('Ethernet', '%')
	module.remove_latest('Flapping', '%')
	module.mass_insert(issues)


# disque, erreurs réseaux, temperature, mac address, disque full ?, cpu 100%, carrier_up_changes_total?

print("OK!")
