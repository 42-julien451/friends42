import redis
import config
try:
    import RatatouilleClient
    ratatouille = RatatouilleClient.RatatouilleClient(config.ratatouille_client, config.ratatouille_secret, realm="next");
except ImportError:
    ratatouille = None;
from api42 import Api


r = redis.Redis(host=config.redis_host, port=config.redis_port, db=0)
api = Api()
