import requests
import time
import config

campuses = config.campuses_to_update

if __name__ == '__main__':
	while True:
		for campus in campuses:
			print(f'updating 42Paris campus...')
			try:
				print("Updating locations")
				req = requests.get(f'http://127.0.0.1:8080/locations/{config.update_key}')
				print("Updating DEAD PC...")
				req = requests.get(f'http://127.0.0.1:8080/modules/{config.update_key}')
				print(req.status_code)
			except requests.exceptions.RequestException:
				print('failed req')
			time.sleep(5)
		print('waiting 45s')
		time.sleep(45)
