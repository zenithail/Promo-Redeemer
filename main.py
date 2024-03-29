import os
import tls_client
import httpx
import threading
import random
import time
import json
import sys
import colorama
import termcolor
import pystyle
from pystyle import Center, Colorate, Colors
from colorama import Fore, init
from itertools import cycle
from typing import Optional, Any
from base64 import b64encode as enc
from timeit import default_timer as timer
from datetime import timedelta


init()
thread_lock = threading.Lock()
activated_accounts = 0

open("config.json", "r") as config:
    config = json.load(config)

webhook = config["webhook"]

class Console:

    @staticmethod
    def _time():
        return time.strftime("%H:%M:%S", time.gmtime())

    @staticmethod
    def clear():
        os.system("cls" if os.name == "nt" else "clear")

    @staticmethod
    def sprint(content: str, status: bool = True) -> None:
        thread_lock.acquire()
        sys.stdout.write(
            f"[{Fore.LIGHTBLUE_EX}{Console()._time()}{Fore.RESET}] {Fore.GREEN if status else Fore.RED}{content}"
            + "\n"
            + Fore.RESET
        )
        thread_lock.release()

    @staticmethod
    def update_title() -> None:
        start = timer()

        while True:
            thread_lock.acquire()
            end = timer()
            elapsed_time = timedelta(seconds=end - start)
            os.system(
                f"title SKX Redeemer │ Activated Accounts: {activated_accounts} │ Elapsed: {elapsed_time}"
            )
            thread_lock.release()

def discord_send(url):
    global message_ids
    payload = {
        "content": f'```[SKX-Redeemer] : Claimed: {claimed} | Failed: {failed} | Processed: {processed}```'
    }
    headers = {
        "Content-Type": "application/json"
    }

    if message_ids:
        latest_message_id = message_ids[-1]
        response = requests.patch(f"{url}/messages/{latest_message_id}", data=json.dumps(payload), headers=headers)
        if response.status_code == 200:
            return
        else:
            return
    else:
        response = requests.post(url, data=json.dumps(payload), headers=headers)
        if response.status_code == 200:
            message_id = response.json().get("id")
            message_ids.append(message_id)
            return
        else:
            return

nameconf = config["name"]
line1conf = config["line_1"]
cityconf = config["city"]
stateconf = config["state"]
postalconf = config["postalcode"]
countryconf = config["country"]


class Others:

    @staticmethod
    def getClientData():
        with open("config.json", "r") as config:
            config = json.load(config)

        build_num = config["build_num"]
        return build_num


    @staticmethod
    def remove_content(filename: str, delete_line: str) -> None:
        thread_lock.acquire()
        with open(filename, "r+") as io:
            content = io.readlines()
            io.seek(0)
            for line in content:
                if not (delete_line in line):
                    io.write(line)
            io.truncate()
        thread_lock.release()

TS = tls_client.Session(
    ja3_string="771,4865-4866-4867-49195-49199-49196-49200-52393-52392-49171-49172-156-157-47-53,0-23-65281-10-11-35-16-5-13-18-51-45-43-27-17513,29-23-24,0",

    h2_settings={

        "HEADER_TABLE_SIZE": 65536,

        "MAX_CONCURRENT_STREAMS": 1000,

        "INITIAL_WINDOW_SIZE": 6291456,

        "MAX_HEADER_LIST_SIZE": 262144

    },

    h2_settings_order=[

        "HEADER_TABLE_SIZE",

        "MAX_CONCURRENT_STREAMS",

        "INITIAL_WINDOW_SIZE",

        "MAX_HEADER_LIST_SIZE"

    ],

    supported_signature_algorithms=[

        "ECDSAWithP256AndSHA256",

        "PSSWithSHA256",

        "PKCS1WithSHA256",

        "ECDSAWithP384AndSHA384",

        "PSSWithSHA384",

        "PKCS1WithSHA384",

        "PSSWithSHA512",

        "PKCS1WithSHA512",

    ],

    supported_versions=["GREASE", "1.3", "1.2"],

    key_share_curves=["GREASE", "X25519"],

    cert_compression_algo="brotli",

    pseudo_header_order=[

        ":method",

        ":authority",

        ":scheme",

        ":path"

    ],

    connection_flow=15663105,

    header_order=[

        "accept",

        "user-agent",

        "accept-encoding",

        "accept-language"

    ]
)    

class Redeemer:
    def __init__(
        self,
        vcc: str,
        token: str,
        link: str,
        build_num: int,
        proxy: Optional[Any] = None,
    ) -> None:
        self.card_number, self.expiry, self.ccv = vcc.split(":")
        self.link = link
        self.token = token
        self.proxy = proxy
        self.build_num = build_num
        self.client = httpx.Client(proxies=proxy, timeout=90)
        self.stripe_client = httpx.Client(proxies=proxy, timeout=90)

        if "promos.discord.gg/" in self.link:
            self.link = f'https://discord.com/billing/promotions/{self.link.split("promos.discord.gg/")[1]}'

        if ":" in self.token:
            self.token = token.split(":")[2]
            self.full_token = token
        else:
            self.token = token

    def __tasks__(self) -> Any:
        if not self.__session__():
            print(f"{Fore.RED} [-] Could not create a session", False)
            return

        if not self.__stripe():
            print(f"{Fore.RED} [-] Could not get stripe cookies", False)
            return

        if not self.__stripe_tokens():
            print(f"{Fore.RED} [-] Could not get confirm token", False)
            return

        if not self.setup_intents():
            print(f"{Fore.RED} [-] Could not setup intents [Client Secret]", False)
            return

        if not self.validate_billing():
            print(f"{Fore.RED} [-] Could not validate billing [Billing Token]", False)
            return

        if not self.__stripe_confirm():
            print(f"Could confirm stripe [Payment Id]", False)
            return

        if not self.add_payment():
            print(f"{Fore.RED} [-] Could not add vcc, error message: {self.error}", False)
            return

        redeem = self.redeem()

        if not redeem:
            print(f"{Fore.RED} [-] Could not redeem nitro, error: {self.error}", False)
            if "This payment method cannot be used" in self.error:
                Others().remove_content("vccs.txt", self.card_number)

            elif "Already purchased" in self.error:
                Others().remove_content("tokens.txt", self.token)

                thread_lock.acquire()

                with open("success.txt", "a") as success:
                    if hasattr(self, "full_token"):
                        success.write(self.full_token + "\n")
                    else:
                        success.write(self.token + "\n")

                thread_lock.release()

            elif "This gift has been redeemed already" in self.error:
                Others().remove_content("promos.txt", self.link)

            return

        elif redeem == "auth":
            return redeem

        else:
            print(f"{Fore.GREEN} [+] Successfully redeemed {self.token}", True)
            Others().remove_content("tokens.txt", self.token)
            Others().remove_content(
                "promos.txt", self.link.split("/promotions/")[1]
            )
            discord_send(webhook)

            thread_lock.acquire()

            with open("success.txt", "a") as success:
                if hasattr(self, "full_token"):
                    success.write(self.full_token + "\n")
                else:
                    success.write(self.token + "\n")

            global activated_accounts
            activated_accounts += 1

            thread_lock.release()

    def __session__(self) -> bool:
        self.client.headers.update(
            {
                "Accept": "*/*",
                "Accept-Language": "en-US,en;q=0.9",
                "Connection": "keep-alive",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Sec-Fetch-User": "?1",
                "Upgrade-Insecure-Requests": "1",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.5112.39 Safari/537.36",
                "sec-ch-ua": '".Not/A)Brand";v="99", "Google Chrome";v="103", "Chromium";v="103"',
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": '"Windows"',
            }
        )

        get_site = TS.get(self.link)

        if not (get_site.status_code in [200, 201, 204]):
            return False

        self.stripe_key = get_site.text.split("STRIPE_KEY: '")[1].split("',")[0]

        self.__dcfduid = (
            get_site.headers["set-cookie"].split("__dcfduid=")[1].split(";")[0]
        )
        self.__sdcfduid = (
            get_site.headers["set-cookie"].split("__sdcfduid=")[1].split(";")[0]
        )

        self.client.cookies.update(
            {
                "__dcfduid": self.__dcfduid,
                "__sdcfduid": self.__sdcfduid,
                "locale": "en-US",
            }
        )

        self.super_properties = enc(
            json.dumps(
                {
                    "os": "Windows",
                    "browser": "Chrome",
                    "device": "",
                    "system_locale": "en-US",
                    "browser_user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.5112.39 Safari/537.36",
                    "browser_version": "104.0.5112.39",
                    "os_version": "10",
                    "referrer": "",
                    "referring_domain": "",
                    "referrer_current": "",
                    "referring_domain_current": "",
                    "release_channel": "stable",
                    "client_build_number": self.build_num,
                    "client_event_source": None,
                },
                separators=(",", ":"),
            ).encode()
        ).decode("utf-8")

        self.client.headers.update(
            {
                "X-Context-Properties": "eyJsb2NhdGlvbiI6IlJlZ2lzdGVyIn0=",
                "X-Debug-Options": "bugReporterEnabled",
                "X-Discord-Locale": "en-US",
                "X-Super-Properties": self.super_properties,
            }
        )

        self.client.headers.update({"Host": "discord.com", "Referer": self.link})

        self.fingerprint = self.client.get("https://discord.com/api/v9/experiments")

        if not (self.fingerprint.status_code in [200, 201, 204]):
            return False

        self.fingerprint = self.fingerprint.json()["fingerprint"]

        self.client.headers["Origin"] = "https://discord.com"

        if not (get_site.status_code in [200, 201, 204]):
            return False

        self.client.headers.update(
            {"X-Fingerprint": self.fingerprint, "Authorization": self.token}
        )

        return True

    def __stripe(self) -> bool:
        self.stripe_client.headers.update(
            {
                "accept": "application/json",
                "accept-language": "en-CA,en;q=0.9",
                "content-type": "application/x-www-form-urlencoded",
                "dnt": "1",
                "origin": "https://m.stripe.network",
                "referer": "https://m.stripe.network/",
                "sec-ch-ua": '".Not/A)Brand";v="99", "Google Chrome";v="103", "Chromium";v="103"',
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": '"Windows"',
                "sec-fetch-dest": "empty",
                "sec-fetch-mode": "cors",
                "sec-fetch-site": "cross-site",
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.5112.39 Safari/537.36",
            }
        )

        response = self.stripe_client.post(
            "https://m.stripe.com/6",
            data="JTdCJTIydjIlMjIlM0EyJTJDJTIyaWQlMjIlM0ElMjIwYWQ5NTYwYzZkYjIxZDRhZTU3ZGM5NmQ0ZThlZGY3OCUyMiUyQyUyMnQlMjIlM0EyNC45JTJDJTIydGFnJTIyJTNBJTIyNC41LjQyJTIyJTJDJTIyc3JjJTIyJTNBJTIyanMlMjIlMkMlMjJhJTIyJTNBJTdCJTIyYSUyMiUzQSU3QiUyMnYlMjIlM0ElMjJmYWxzZSUyMiUyQyUyMnQlMjIlM0EwLjIlN0QlMkMlMjJiJTIyJTNBJTdCJTIydiUyMiUzQSUyMnRydWUlMjIlMkMlMjJ0JTIyJTNBMCU3RCUyQyUyMmMlMjIlM0ElN0IlMjJ2JTIyJTNBJTIyZW4tQ0ElMjIlMkMlMjJ0JTIyJTNBMCU3RCUyQyUyMmQlMjIlM0ElN0IlMjJ2JTIyJTNBJTIyV2luMzIlMjIlMkMlMjJ0JTIyJTNBMCU3RCUyQyUyMmUlMjIlM0ElN0IlMjJ2JTIyJTNBJTIyUERGJTIwVmlld2VyJTJDaW50ZXJuYWwtcGRmLXZpZXdlciUyQ2FwcGxpY2F0aW9uJTJGcGRmJTJDcGRmJTJCJTJCdGV4dCUyRnBkZiUyQ3BkZiUyQyUyMENocm9tZSUyMFBERiUyMFZpZXdlciUyQ2ludGVybmFsLXBkZi12aWV3ZXIlMkNhcHBsaWNhdGlvbiUyRnBkZiUyQ3BkZiUyQiUyQnRleHQlMkZwZGYlMkNwZGYlMkMlMjBDaHJvbWl1bSUyMFBERiUyMFZpZXdlciUyQ2ludGVybmFsLXBkZi12aWV3ZXIlMkNhcHBsaWNhdGlvbiUyRnBkZiUyQ3BkZiUyQiUyQnRleHQlMkZwZGYlMkNwZGYlMkMlMjBNaWNyb3NvZnQlMjBFZGdlJTIwUERGJTIwVmlld2VyJTJDaW50ZXJuYWwtcGRmLXZpZXdlciUyQ2FwcGxpY2F0aW9uJTJGcGRmJTJDcGRmJTJCJTJCdGV4dCUyRnBkZiUyQ3BkZiUyQyUyMFdlYktpdCUyMGJ1aWx0LWluJTIwUERGJTJDaW50ZXJuYWwtcGRmLXZpZXdlciUyQ2FwcGxpY2F0aW9uJTJGcGRmJTJDcGRmJTJCJTJCdGV4dCUyRnBkZiUyQ3BkZiUyMiUyQyUyMnQlMjIlM0EwLjElN0QlMkMlMjJmJTIyJTNBJTdCJTIydiUyMiUzQSUyMjE5MjB3XzEwNDBoXzI0ZF8xciUyMiUyQyUyMnQlMjIlM0EwJTdEJTJDJTIyZyUyMiUzQSU3QiUyMnYlMjIlM0ElMjItNCUyMiUyQyUyMnQlMjIlM0EwJTdEJTJDJTIyaCUyMiUzQSU3QiUyMnYlMjIlM0ElMjJmYWxzZSUyMiUyQyUyMnQlMjIlM0EwJTdEJTJDJTIyaSUyMiUzQSU3QiUyMnYlMjIlM0ElMjJzZXNzaW9uU3RvcmFnZS1kaXNhYmxlZCUyQyUyMGxvY2FsU3RvcmFnZS1kaXNhYmxlZCUyMiUyQyUyMnQlMjIlM0EwLjElN0QlMkMlMjJqJTIyJTNBJTdCJTIydiUyMiUzQSUyMjAxMDAxMDAxMDExMTExMTExMDAxMTExMDExMTExMTExMDExMTAwMTAxMTAxMTExMTAxMTExMTElMjIlMkMlMjJ0JTIyJTNBOS4yJTJDJTIyYXQlMjIlM0EwLjIlN0QlMkMlMjJrJTIyJTNBJTdCJTIydiUyMiUzQSUyMiUyMiUyQyUyMnQlMjIlM0EwJTdEJTJDJTIybCUyMiUzQSU3QiUyMnYlMjIlM0ElMjJNb3ppbGxhJTJGNS4wJTIwKFdpbmRvd3MlMjBOVCUyMDEwLjAlM0IlMjBXT1c2NCklMjBBcHBsZVdlYktpdCUyRjUzNy4zNiUyMChLSFRNTCUyQyUyMGxpa2UlMjBHZWNrbyklMjBDaHJvbWUlMkYxMDMuMC4wLjAlMjBTYWZhcmklMkY1MzcuMzYlMjIlMkMlMjJ0JTIyJTNBMCU3RCUyQyUyMm0lMjIlM0ElN0IlMjJ2JTIyJTNBJTIyJTIyJTJDJTIydCUyMiUzQTAlN0QlMkMlMjJuJTIyJTNBJTdCJTIydiUyMiUzQSUyMmZhbHNlJTIyJTJDJTIydCUyMiUzQTIxLjUlMkMlMjJhdCUyMiUzQTAuMiU3RCUyQyUyMm8lMjIlM0ElN0IlMjJ2JTIyJTNBJTIyMTZlNzljMzY0YjkwNDM0NGU1ODFmNjlhMTI4ZTNkYTglMjIlMkMlMjJ0JTIyJTNBNi4xJTdEJTdEJTJDJTIyYiUyMiUzQSU3QiUyMmElMjIlM0ElMjJodHRwcyUzQSUyRiUyRkdTN2hxbmtaQlJwUF83V245LUNHRmh6cTRrcjJYM0pDNEEzazZCREJ2cEUuZzJ1OS1ocVp2R0lxWUpjUGxQZndKQWYtdjNSZ3lLX3gxTnBwekFsQTEyTSUyRkJRZE55enBMVTRuTTZZS3p6bmFQMVhDRDFXMERKMXozVHBudHoyWnBJcXMlMkYwc0x5MVBQSUkyaG0zT0RIaUxadUtjNlJkeWNMRTFWcm1yeW50c1hYdDdvJTJGb1dwRTZfai1tS0tFS25CWEVpbVVZMDJRTVlfTklJanRPblZHbHUwblFmVSUyMiUyQyUyMmIlMjIlM0ElMjJodHRwcyUzQSUyRiUyRkdTN2hxbmtaQlJwUF83V245LUNHRmh6cTRrcjJYM0pDNEEzazZCREJ2cEUuZzJ1OS1ocVp2R0lxWUpjUGxQZndKQWYtdjNSZ3lLX3gxTnBwekFsQTEyTSUyRkJRZE55enBMVTRuTTZZS3p6bmFQMVhDRDFXMERKMXozVHBudHoyWnBJcXMlMkYwc0x5MVBQSUkyaG0zT0RIaUxadUtjNlJkeWNMRTFWcm1yeW50c1hYdDdvJTJGb1dwRTZfai1tS0tFS25CWEVpbVVZMDJRTVlfTklJanRPblZHbHUwblFmVSUyMiUyQyUyMmMlMjIlM0ElMjJfSWwxX2c2VDlzcjVXcS10eUhkZUwxZWVFdHo3TzdJRE8xZ3JDLU5aY1VrJTIyJTJDJTIyZCUyMiUzQSUyMjBiOTYwMGE5LTkyNjctNGViNi05NGNhLTM1MzNhMDE4NGExMTQxMDc3NiUyMiUyQyUyMmUlMjIlM0ElMjJmOGFkN2Y2Ny1lMWFmLTQxZTctYjlmMy1kNzRjZGRlMGI1NGQzZThiODAlMjIlMkMlMjJmJTIyJTNBZmFsc2UlMkMlMjJnJTIyJTNBdHJ1ZSUyQyUyMmglMjIlM0F0cnVlJTJDJTIyaSUyMiUzQSU1QiUyMmxvY2F0aW9uJTIyJTVEJTJDJTIyaiUyMiUzQSU1QiU1RCUyQyUyMm4lMjIlM0EyNjcuNSUyQyUyMnUlMjIlM0ElMjJkaXNjb3JkLmNvbSUyMiUyQyUyMnYlMjIlM0ElMjJkaXNjb3JkLmNvbSUyMiU3RCUyQyUyMmglMjIlM0ElMjI5NjI5ZjFjZWM1NGY1YjhmM2IxYSUyMiU3RA==",
        )

        if not (response.status_code in [200, 201, 204]):
            return False

        self.muid, self.guid, self.sid = (
            response.json()["muid"],
            response.json()["guid"],
            response.json()["sid"],
        )

        self.client.cookies.update(
            {"__stripe_mid": self.muid, "__stripe_sid": self.sid}
        )

        return True

    def __stripe_tokens(self) -> bool:
        self.stripe_client.headers["Authorization"] = "Bearer " + self.stripe_key
        data = f"card[number]={self.card_number}&card[cvc]={self.ccv}&card[exp_month]={self.expiry[:2]}&card[exp_year]={self.expiry[-2:]}&guid={self.guid}&muid={self.muid}&sid={self.sid}&payment_user_agent=stripe.js%2Ff0346bf10%3B+stripe-js-v3%2Ff0346bf10&time_on_page={random.randint(60000, 120000)}&key={self.stripe_key}&pasted_fields=number%2Cexp%2Ccvc"

        response = self.stripe_client.post(
            "https://api.stripe.com/v1/tokens", data=data
        )

        if response.status_code == 200:
            self.confirm_token = response.json()["id"]
            return True
        else:
            return False

    def setup_intents(self) -> bool:
        response = self.client.post(
            "https://discord.com/api/v9/users/@me/billing/stripe/setup-intents"
        )

        if response.status_code == 200:
            self.client_secret = response.json()["client_secret"]
            return True
        else:
            return False

    def validate_billing(
        self,
        name: str = nameconf,
        line_1: str = line1conf,
        line_2: str = "",
        city: str = cityconf,
        state: str = stateconf,
        postal_code: str = postalconf,
        country: str = countryconf,
        email: str = "mrzevs291@gmail.com",
    ) -> bool:
        self.name = name
        self.line_1 = line_1
        self.line_2 = line_2
        self.city = city
        self.state = state
        self.postal_code = postal_code
        self.country = country
        self.email = email

        response = self.client.post(
            "https://discord.com/api/v9/users/@me/billing/payment-sources/validate-billing-address",
            json={
                "billing_address": {
                    "name": name,
                    "line_1": line_1,
                    "line_2": line_2,
                    "city": city,
                    "state": state,
                    "postal_code": postal_code,
                    "country": country,
                    "email": email,
                }
            },
        )

        if response.status_code == 200:
            self.billing_token = response.json()["token"]
            return True
        else:
            return False

    def parse_data(self, content: str) -> str:
        return content.replace(" ", "+")

    def __stripe_confirm(self) -> bool:
        self.depracted_client_secret = str(self.client_secret).split("_secret_")[0]
        data = f"""payment_method_data[type]=card&payment_method_data[card][token]={self.confirm_token}&payment_method_data[billing_details][address][line1]={self.parse_data(self.line_1)}&payment_method_data[billing_details][address][line2]={(self.parse_data(self.line_2) if self.line_2 != "" else self.line_2)}&payment_method_data[billing_details][address][city]={self.city}&payment_method_data[billing_details][address][state]={self.state}&payment_method_data[billing_details][address][postal_code]={self.postal_code}&payment_method_data[billing_details][address][country]={self.country}&payment_method_data[billing_details][name]={self.parse_data(self.name)}&payment_method_data[guid]={self.guid}&payment_method_data[muid]={self.muid}&payment_method_data[sid]={self.sid}&payment_method_data[payment_user_agent]=stripe.js%2Ff0346bf10%3B+stripe-js-v3%2Ff0346bf10&payment_method_data[time_on_page]={random.randint(210000, 450000)}&expected_payment_method_type=card&use_stripe_sdk=true&key={self.stripe_key}&client_secret={self.client_secret}"""

        response = self.stripe_client.post(
            f"https://api.stripe.com/v1/setup_intents/{self.depracted_client_secret}/confirm",
            data=data,
        )

        if response.status_code == 200:
            self.payment_id = response.json()["payment_method"]
            return True
        else:
            return False

    def add_payment(self) -> bool:
        payload = {
            "payment_gateway": 1,
            "token": self.payment_id,
            "billing_address": {
                "name": self.name,
                "line_1": self.line_1,
                "line_2": self.line_2,
                "city": self.city,
                "state": self.state,
                "postal_code": self.postal_code,
                "country": self.country,
                "email": self.email,
            },
            "billing_address_token": self.billing_token,
        }

        response = self.client.post(
            "https://discord.com/api/v9/users/@me/billing/payment-sources", json=payload
        )

        if response.status_code == 200:
            self.payment_source_id = response.json()["id"]
            return True
        else:
            self.error = response.json()["errors"]["_errors"][0]["message"]
            return False

    def redeem(self) -> bool:
        response = TS.post(
            f'https://discord.com/api/v9/entitlements/gift-codes/{self.link.split("https://discord.com/billing/promotions/")[1]}/redeem',
            json={"channel_id": None, "payment_source_id": self.payment_source_id},
        )

        if response.status_code == 200:
            return True

        elif response.json()["message"] == "Authentication required":
            self.stripe_payment_id = response.json()["payment_id"]
            return "auth"

        else:
            self.error = response.json()["message"]
            return False


class Authentication(Redeemer):
    def __init__(
        self,
        vcc: str,
        token: str,
        link: str,
        build_num: int = Others().getClientData(),
        proxy: Optional[Any] = None,
    ) -> None:
        super().__init__(vcc, token, link, build_num, proxy)

        try:
            if self.__tasks__() == "auth":
                if not self.discord_payment_intents():
                    print(f"{Fore.RED} [-] Could not setup discord payment intents", False)
                    return

                time.sleep(0.2)

                if not self.stripe_payment_intents():
                    print(
                        f"{Fore.RED} [-] Could not setup stripe payment intents [1]", False
                    )
                    return

                time.sleep(0.2)

                if not self.stripe_payment_intents_2():
                    print(
                        f"{Fore.RED} [-] Could not setup stripe payment intents [2]", False
                    )
                    return

                time.sleep(0.2)

                if not self.stripe_fingerprint():
                    print(f"{Fore.RED} [-] Could not send fingerprint to stripe", False)
                    return

                time.sleep(0.2)

                if not self.authenticate():
                    print(f"{Fore.RED} [-] Could not authenticate vcc", False)
                    return

                time.sleep(0.2)

                if not self.billing():
                    print(f"{Fore.RED} [-] Could not send fingerprint to stripe", False)
                    return

                time.sleep(0.2)

                redeem = self.redeem()
                if not redeem:
                    print(
                        f"{Fore.RED} [-] Could not redeem nitro, error: {self.error}", False
                    )
                    if "This payment method cannot be used" in self.error:
                        Others().remove_content("vccs.txt", self.card_number)
                    return

                elif redeem == "auth":
                    print(f"{Fore.RED} [-] Could not authenticate vcc", False)
                    return

                else:
                    print(f"{Fore.GREEN} [+] Sucessfully Redeemed {self.token}", True)
                    Others().remove_content("tokens.txt", self.token)
                    Others().remove_content(
                        "promos.txt", self.link.split("/promotions/")[1]
                    )

                    thread_lock.acquire()

                    with open("success.txt", "a") as success:
                        if hasattr(self, "full_token"):
                            success.write(self.full_token + "\n")
                        else:
                            success.write(self.token + "\n")

                    global activated_accounts
                    activated_accounts += 1
                    thread_lock.release()

            else:
                return
        except Exception as err:
            print(f"{Fore.RED} [-] An error occured: {err}", False)

    def discord_payment_intents(self) -> bool:
        response = TS.get(
            f"https://discord.com/api/v9/users/@me/billing/stripe/payment-intents/payments/{self.stripe_payment_id}"
        )

        if response.status_code == 200:
            self.stripe_payment_intent_client_secret = response.json()[
                "stripe_payment_intent_client_secret"
            ]
            self.depracted_stripe_payment_intent_client_secret = str(
                response.json()["stripe_payment_intent_client_secret"]
            ).split("_secret_")[0]
            self.stripe_payment_intent_payment_method_id = response.json()[
                "stripe_payment_intent_payment_method_id"
            ]
            return True
        else:
            return False

    def stripe_payment_intents(self) -> bool:
        response = self.stripe_client.get(
            f"https://api.stripe.com/v1/payment_intents/{self.depracted_stripe_payment_intent_client_secret}?key={self.stripe_key}&is_stripe_sdk=false&client_secret={self.stripe_payment_intent_client_secret}"
        )

        if response.status_code == 200:
            return True
        else:
            return False

    def stripe_payment_intents_2(self) -> bool:
        data = {
            "expected_payment_method_type": "card",
            "use_stripe_sdk": "true",
            "key": self.stripe_key,
            "client_secret": self.stripe_payment_intent_client_secret,
        }

        response = self.stripe_client.post(
            f"https://api.stripe.com/v1/payment_intents/{self.depracted_stripe_payment_intent_client_secret}/confirm",
            data=data,
        )

        if response.status_code == 200:
            self.server_transaction_id = response.json()["next_action"][
                "use_stripe_sdk"
            ]["server_transaction_id"]
            self.three_d_secure_2_source = response.json()["next_action"][
                "use_stripe_sdk"
            ]["three_d_secure_2_source"]
            self.merchant = response.json()["next_action"]["use_stripe_sdk"]["merchant"]
            self.three_ds_method_url = response.json()["next_action"]["use_stripe_sdk"][
                "three_ds_method_url"
            ]
            return True
        else:
            return False

    def stripe_fingerprint(self) -> bool:
        self.threeDSMethodNotificationURL = f"https://hooks.stripe.com/3d_secure_2/fingerprint/{self.merchant}/{self.three_d_secure_2_source}"
        data = {
            "threeDSMethodData": enc(
                json.dumps(
                    {"threeDSServerTransID": self.server_transaction_id},
                    separators=(",", ":"),
                ).encode()
            ).decode("utf-8")
        }

        response = self.stripe_client.post(self.threeDSMethodNotificationURL, data=data)

        if response.status_code == 200:
            return True
        else:
            return False

    def authenticate(self) -> bool:
        data = f"""source={self.three_d_secure_2_source}&browser=%7B%22fingerprintAttempted%22%3Atrue%2C%22fingerprintData%22%3A%22{enc(json.dumps({"threeDSServerTransID": self.server_transaction_id},separators=(",", ":")).encode()).decode('utf-8')}%22%2C%22challengeWindowSize%22%3Anull%2C%22threeDSCompInd%22%3A%22Y%22%2C%22browserJavaEnabled%22%3Afalse%2C%22browserJavascriptEnabled%22%3Atrue%2C%22browserLanguage%22%3A%22en-US%22%2C%22browserColorDepth%22%3A%2224%22%2C%22browserScreenHeight%22%3A%221080%22%2C%22browserScreenWidth%22%3A%221920%22%2C%22browserTZ%22%3A%22240%22%2C%22browserUserAgent%22%3A%22Mozilla%2F5.0+(Windows+NT+10.0%3B+Win64%3B+x64)+AppleWebKit%2F537.36+(KHTML%2C+like+Gecko)+Chrome%2F104.0.5112.39+Safari%2F537.36%22%7D&one_click_authn_device_support[hosted]=false&one_click_authn_device_support[same_origin_frame]=false&one_click_authn_device_support[spc_eligible]=true&one_click_authn_device_support[webauthn_eligible]=true&one_click_authn_device_support[publickey_credentials_get_allowed]=true&key={self.stripe_key}"""

        response = self.stripe_client.post(
            "https://api.stripe.com/v1/3ds2/authenticate", data=data
        )

        if response.status_code == 200:
            return True
        else:
            return False

    def billing(self) -> bool:
        response = TS.get(
            f"https://discord.com/api/v9/users/@me/billing/payments/{self.stripe_payment_id}"
        )

        if response.status_code == 200:
            return True
        else:
            return False



if __name__ == "__main__":
    Console().clear()


    colorama.deinit()
    os.system("title SKX Redeemer | t.me/skxuhq")
    os.system('cls' if os.name == 'nt' else 'clear')
    w = (
    Center.XCenter(
                f"""  


    ____           __                             
   / __ \___  ____/ /__  ___  ____ ___  ___  _____
  / /_/ / _ \/ __  / _ \/ _ \/ __ `__ \/ _ \/ ___/
 / _, _/  __/ /_/ /  __/  __/ / / / / /  __/ /    
/_/ |_|\___/\__,_/\___/\___/_/ /_/ /_/\___/_/     
                                                                             

          -> t.me/skxuhq                                   
          -> Nitro Promotion Redeemer

 """)

            )
    print(Colorate.Horizontal(Colors.rainbow, w))
        colorama.init(autoreset=True)
    threads = int(input(f"{Fore.BLUE}[+] Enter number of threads: "))
    proxies = cycle(open("proxies.txt", "r").read().splitlines())
    vccs = open("vccs.txt", "r").read().splitlines()
    tokens = open("tokens.txt", "r").read().splitlines()
    promolinks = open("promos.txt", "r").read().splitlines()
    use_on_cc = config["use_on_vcc"]
    thread_count = threads
    build_num = Others().getClientData()

    duplicate_vccs = []

    for vcc in vccs:
        for _ in range(use_on_cc):
            duplicate_vccs.append(vcc)
    Redeemer()

proxied = config["proxied"]

while len(vccs) and len(tokens) and len(promolinks) > 0:
        try:
            local_threads = []
            for x in range(thread_count):
                try:
                    if proxied:
                        next_proxy = "http://" + next(proxies)
                        proxy = {"http://": next_proxy, "https://": next_proxy}
                    else:
                        next_proxy = None
                        proxy = None

                token = tokens[0]
                vcc = duplicate_vccs[0]
                link = promolinks[0]

                start_thread = threading.Thread(
                    target=Authentication,
                    args=(
                        vcc,
                        token,
                        link,
                        build_num,
                        proxy,
                    ),
                )
                local_threads.append(start_thread)
                start_thread.start()

                tokens.pop(0)
                promolinks.pop(0)
                duplicate_vccs.pop(0)

                if not (vcc in duplicate_vccs):
                    Others().remove_content("vccs.txt", vcc)

            for thread in local_threads:
                thread.join()

        except IndexError:
            break
        except:
            pass


        print(f"{Fore.RED} [-] Ran out of materials, Threads may have not finished yet", False)
