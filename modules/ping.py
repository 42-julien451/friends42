import module
from icmplib import multiping, resolve

MODULE_NAME = 'Ping'
DNS_NAME = 'DNS'


def main(computers):
	print("Running module ping")
	host = []
	ips = []
	for computer in computers:
		try:
			ip = resolve(computer + ".paris.42.school", '4')
			if len(ip) != 1:
				module.insert(DNS_NAME, computer, f'Invalid A records {ip}', module.States.DEAD,
				              '<i class="fa-solid fa-circle-question text-danger"></i>')
				continue
			host.append(computer)
			ips.append(ip[0])
			module.insert(DNS_NAME, computer, f'{ip[0]}', module.States.INFO)
		except Exception as e:
			module.insert(DNS_NAME, computer, e.__str__(), module.States.DEAD)

	ret = multiping(ips, count=1, interval=0, timeout=1, privileged=False, concurrent_tasks=200)
	for computer in ret:
		hostname = host[ips.index(computer.address)]
		if computer.is_alive:
			if computer.avg_rtt > 100:
				module.insert(MODULE_NAME, hostname, f"{computer.avg_rtt}ms", module.States.WARNING,
				              '<i class="fa-solid fa-person-cane text-info"></i>')
			else:
				module.insert(MODULE_NAME, hostname, f"{computer.avg_rtt}ms", module.States.OK)
		else:
			module.insert(MODULE_NAME, hostname, f"Can't ping", module.States.DEAD)

# main('bess-f1r1s1')
