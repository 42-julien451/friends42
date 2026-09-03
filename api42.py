import time
from typing import Optional
import requests
import config
import globals


class Api:
	key: str = ""
	secret: str = ""
	rate_limit_sec = 0
	rate_limit_last_time: float = time.time()
	token: str = ""
	expire_at: int = 0

	def __init__(self):
		self.rate_limit_last_time = time.time()
		self.rate_limit_last_time_hours = time.time()

	def get_access_token(self, token: str, state: str, domain: str) -> str:
		self.add_rate()
		r = None
		try:
			r = requests.post(
				"https://auth.42paris.fr/realms/next/protocol/openid-connect/token",
				data={
					"grant_type": "authorization_code",
					"client_id": config.ratatouille_client,
					"client_secret": config.ratatouille_secret,
					"code": token,
					"redirect_uri": config.redirect_url.replace('{current_domain}', domain),
				},
			)
		except Exception as e:
			return ""
		if r.status_code != 200:
			return ""
		return r.json()["access_token"]

	def get_token_info(self, token: str):
		self.add_rate()
		try:
			user_info = requests.get(f"https://auth.42paris.fr/realms/next/protocol/openid-connect/userinfo", headers={
				"Authorization": "Bearer " + token
			})
		except Exception as e:
			return None
		if user_info.status_code != 200:
			return None
		return user_info.json()

	def get_user_id_by_token(self, token: str, state: str, domain: str):
		final_token = self.get_access_token(token, state, domain)
		if final_token == "":
			return 0
		user_info = self.get_token_info(final_token)
		if not user_info:
			return 0
		if user_info["account_type"] == "42v2":
			return int(user_info["42v2_id"])
		elif user_info["account_type"] == "42next" and user_info["id"]:
			return int(user_info["id"])
		elif user_info["account_type"] == "42next" and user_info["42v2_id"]:
			return int(user_info["42v2_id"])

	def add_rate(self):
		if self.rate_limit_last_time == time.time() and self.rate_limit_sec == 2:
			time.sleep(1)
			self.rate_limit_sec = 0
		if self.rate_limit_last_time != time.time():
			self.rate_limit_sec = 0
			self.rate_limit_last_time = time.time()
		self.rate_limit_sec += 1

	def get(self, url: str, params: Optional[list] = None) -> tuple[dict, int, dict]:
		if params is None:
			params = []
		if self.expire_at < time.time():
			if not self.get_token():
				return {"error": "Rate limit"}, 429, {}
		self.add_rate()
		req_url = self.intra
		if "v2/" != url[:3]:
			req_url += '/v2'
		req_url += f"{url}?{'&'.join([item for item in params])}"
		r = None
		try:
			r = requests.get(req_url, headers={
				"Authorization": f"Bearer {self.token}"
			})
		except Exception as e:
			return {"error": e.__str__()}, 0, {}
		if r and r.status_code == 200:
			return r.json(), r.status_code, dict(r.headers)
		else:
			return {"error": r.text}, r.status_code, dict(r.headers)


	def get_unknown_user(self, user_name: str):
		data = globals.ratatouille(user_name)
		if data == 200:
			return 200, data
		return 500, data
