import uuid
import threading
import logging
import urllib3
from locust import HttpUser, task, between
from locust.exception import StopUser

# 1) Silence the HTTPS warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 2) Configure logging format *before* any Locust setup runs
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)-5s %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger()

class WebsiteUser(HttpUser):
    wait_time = between(1, 2)

    # class‐level counter for assigning user numbers
    user_counter = 0
    counter_lock = threading.Lock()

    def on_start(self):
        with WebsiteUser.counter_lock:
            WebsiteUser.user_counter += 1
            self.user_num = WebsiteUser.user_counter

        # unique credentials per user
        self.email = f"user_{uuid.uuid4().hex[:8]}@test.com"
        self.password = "Password123!"

    @task
    def register_login_home_addinfo(self):
        # Step 1: register
        self.client.post(
            "/register",
            data={
                "email": self.email,
                "password": self.password,
                "confirm_password": self.password
            },
            verify=False
        )

        # Step 2: login
        resp = self.client.post(
            "/login",
            data={"email": self.email, "password": self.password},
            verify=False
        )

        # Steps 3 & 4 if login succeeded
        if resp.status_code == 200:
            self.client.get("/home", verify=False)
            self.client.post(
                "/add-info",
                data={
                    "fname": "Test", "mname": "User", "lname": "Locust",
                    "age": "30", "address": "123 Test St", "bday": "1995-01-01"
                },
                verify=False
            )

        # Log and stop this user
        logger.info(f"User {self.user_num} done queue")
        raise StopUser
