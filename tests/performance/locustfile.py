import random
import string
import time
import logging
from locust import HttpUser, task, between, events

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EtcdApiUser(HttpUser):
    wait_time = between(0.1, 0.5)
    
    def on_start(self):
        """Initialize user with some random prefix for keys to avoid collision if needed"""
        self.key_prefix = "perf_test_"
        self.keys_created = []

    def generate_random_string(self, length=10):
        return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

    @task(3)
    def put_key(self):
        key = f"{self.key_prefix}{self.generate_random_string()}"
        value = self.generate_random_string(100) # 100 bytes value
        
        start_time = time.time()
        with self.client.post("/kv", json={"key": key, "value": value}, catch_response=True) as response:
            if response.status_code == 200:
                response.success()
                self.keys_created.append(key)
            else:
                response.failure(f"Failed to put key: {response.text}")
                logger.error(f"PUT /kv failed: {response.text}")

    @task(10)
    def get_key(self):
        if not self.keys_created:
            return
            
        key = random.choice(self.keys_created)
        encoded_key = key # In real app we might need url encoding but client does it
        
        with self.client.get(f"/kv/{encoded_key}", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 404:
                # 404 is acceptable if key was deleted, but we track created keys.
                # However, other users might delete it.
                response.success() 
            else:
                response.failure(f"Failed to get key: {response.text}")
                logger.error(f"GET /kv/{key} failed: {response.text}")

    @task(1)
    def delete_key(self):
        if not self.keys_created:
            return
            
        key = random.choice(self.keys_created)
        self.keys_created.remove(key)
        
        with self.client.delete(f"/kv/{key}", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 404:
                response.success()
            else:
                response.failure(f"Failed to delete key: {response.text}")
                logger.error(f"DELETE /kv/{key} failed: {response.text}")

