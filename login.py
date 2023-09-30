import os
from dotenv import load_dotenv
import requests

load_dotenv()

def get_access_token():
    url = os.getenv("FISKIL_API_URL")
    payload = {
        "client_id": os.getenv("FISKIL_CLIENT_ID"),
        "client_secret": os.getenv("FISKIL_CLIENT_SECRET"),
    }
    headers = {
        "content-type": "application/json",
        "cache-control": "no-cache"
    }
    response = requests.post(url, json=payload, headers=headers)
    return response.json().get("access_token")

def fetch_usage(access_token):
    end_user_id = os.getenv("END_USER_ID")
    usage_url = f"https://prod.fiskil.com/v1/energy/usage?cursor=None&end_user_id={end_user_id}"
    # usage_url = f"https://prod.fiskil.com/v1/energy/usage?cursor={cursor}&end_user_id={end_user_id}"
    headers = {
        "authorization": f"Bearer {access_token}",
        "content-type": "application/json",
        "cache-control": "no-cache"
    }
    response = requests.get(usage_url, headers=headers)
    response_data = response.json()
    return response_data


def fetch_and_save_plan_info(access_token):
    end_user_id = os.getenv("END_USER_ID")
    account_url = f"https://prod.fiskil.com/v1/energy/accounts?cursor=None&end_user_id={end_user_id}"

    headers = {
        "authorization": f"Bearer {access_token}",
        "content-type": "application/json",
        "cache-control": "no-cache"
    }
    response = requests.request("GET", account_url, headers=headers)
    response_data = response.json()
    return response_data


def fetch_service_point(access_token):
    end_user_id = os.getenv("END_USER_ID")
    service_point_url = f"https://prod.fiskil.com/v1/energy/service-points?cursor=&end_user_id={end_user_id}"

    headers = {
    "authorization": f"Bearer {access_token}",
    "content-type": "application/json",
    "cache-control": "no-cache"
    }
    # response = requests.request("GET", service_point_url, headers=headers)
    # response_data = response.json()
    # return response_data
    response = requests.get(service_point_url, headers=headers)
    response_data = response.json()
    return response_data
