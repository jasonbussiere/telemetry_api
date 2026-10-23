import argparse
import random
import socket
from platform import platform

import psutil
import requests
import time



class T850Agent:

    def __init__(self, agent_id, base_url="http://127.0.0.1:5000/api"):
        self.db_id = None
        self.agent_id = agent_id
        self.base_url = base_url
        self.hostname = f"T850-{self.agent_id}"
        self.token=self.authenticate()

    def authenticate(self):
        """Authenticate with API to get a JWT token"""
        print(f'Logging in to API')
        url = f"{self.base_url}/login"
        res = requests.post(url, json={
            "hostname": self.hostname,
            "password": 'agent-secure-password-!'
        })

        if res.status_code == 200:
            return res.json().get('access_token')
        else:
            print(f"[{time.strftime('%X')}] Login failed!: {res.status_code} {res.text} ")
            return None

    def get_headers(self):
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }

    def send_telemetry(self):
        #CREATE (POST)
        url = f"{self.base_url}/metrics"
        payload = self.get_sensor_data()


        try:
            response = requests.post(url, json=payload, headers=self.get_headers())

            if response.status_code == 422:
                print("VALIDATION FAILED!")
                print(response.json())


            if response.status_code in [200, 201]:
                response_data = response.json()
                if "agent_id" in response_data:
                    self.db_id = response_data["agent_id"]
                print(f"[Agent {self.agent_id}] Telemetry sent to successfully")
            else:
                print(f"[Agent {self.agent_id}] Telemetry rejected: {response.status_code} {response.text} ")
        except Exception as e:
            print(f"Connection: {e}")

    def update_status(self, new_status):
        url = f"{self.base_url}/hosts/{self.db_id}"
        payload = {"status": new_status}
        response = requests.put(url, json=payload, headers=self.get_headers())
        if response.status_code == 200:
            print(f"[Agent {self.agent_id}] Updated status to {new_status}")

    def terminator(self):

        if not hasattr(self, "db_id") or not self.db_id:
            print(f"Skipping terminator: no database ID recorded")
            return

        url = f"{self.base_url}/hosts/{self.db_id}"

        response = requests.delete(url, headers=self.get_headers())
        if response.status_code == 200:
            print(f"[Agent {self.agent_id}] Agent terminated. The future is saved!")
        else:
            print(f"Terminator failed: {response.status_code} {response.text} ")

    def get_sensor_data(self):
        cpu = psutil.cpu_percent(interval=None)
        ram = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        return {
            "hostname": self.hostname,
            "os_info": platform(),
            "status": "active",

            "cpu_percent": cpu,
            "ram_percent": ram.percent,
            "total_ram_gb": round(ram.total / (1024 ** 3), 2),
            "disk_percent": disk.percent,
            "total_disk_gb": round(disk.total / (1024 ** 3), 2),

        }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument( "--id", type=int, help="Agent ID", required=True)
    args = parser.parse_args()

    agent = T850Agent(agent_id=args.id)
    print(f"[Agent {args.id}] Deployed and Active")

    cycle = 1

    try:
        while True:
            agent.send_telemetry()

            if cycle % 10==0:
                new_status = random.choice(["combat mode", "scanning"])
                agent.update_status(new_status)

            cycle += 1
            time.sleep(3)
    except KeyboardInterrupt:
        print(f"[Agent {args.id}] Abort detected. Self-terminating...")
        agent.terminator()

    except Exception as e:
        print(f"[Agent {args.id}] Error: {e}")
        agent.terminator()

if __name__ == "__main__":
    main()