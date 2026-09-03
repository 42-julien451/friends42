import requests
import time
import config

if __name__ == '__main__':
	while True:
		print(f'updating 42Paris campus...')
		try:
			print("Updating locations")
			req1 = requests.get(f'http://127.0.0.1:8080/locations/{config.update_key}')
			print(req1.status_code)
			print("Updating DEAD PC...")
			req2 = requests.get(f'http://127.0.0.1:8080/modules/{config.update_key}')
			print(req2.status_code)
		except requests.exceptions.RequestException as e:
			print(f'failed req:\n{e}')
		print('waiting 45s')
		time.sleep(45)
