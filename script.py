"""Rogue IoT Camera Defense Sweep: audit -> assess -> quarantine."""
import logging
import os

import requests

GET_URL = "https://httpbin.org/get"
POST_URL = "https://httpbin.org/post"
AGENT_NAME = "defense-agent-01"
TOKEN = os.getenv("ADMIN_TOKEN", "demo-admin-token")  # dummy fallback, never commit real secrets
TIMEOUT = 10

DEVICES = [
    "cam-lobby-public",
    "sensor-vault-internal",
    "cam-parking-public",
    "thermostat-office-internal",
]

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
log = logging.getLogger("sweep")


def audit(device: str) -> bool:
    """Probe a device. Return True only if it answers with HTTP 200."""
    params = {"device_identifier": device, "operation": "probe"}
    try:
        resp = requests.get(GET_URL, params=params, timeout=TIMEOUT)
    except requests.RequestException as exc:
        log.warning("%s unreachable (%s) - skipping", device, exc)
        return False
    if resp.status_code != 200:
        log.warning("%s offline (status %s) - skipping", device, resp.status_code)
        return False
    return True


def is_compromised(device: str) -> bool:
    """A camera exposed to the public is a breach risk."""
    return "cam" in device and "public" in device


def quarantine(device: str) -> None:
    """Issue an emergency lockdown and validate the response."""
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "X-Emergency-Priority": "high",
    }
    payload = {
        "device_identifier": device,
        "containment_action": "sever_network_access",
        "agent": AGENT_NAME,
    }
    try:
        resp = requests.post(POST_URL, headers=headers, json=payload, timeout=TIMEOUT)
        if resp.status_code != 200:
            raise ValueError(f"status {resp.status_code}")
        action = resp.json()["json"]["containment_action"]
    except (requests.RequestException, ValueError, KeyError) as exc:
        log.error("ESCALATION ALERT: %s could not be isolated (%s)", device, exc)
        return
    log.info("%s isolated - containment action applied: %s", device, action)


def main() -> None:
    for device in DEVICES:
        if not audit(device):
            continue
        if is_compromised(device):
            log.error("%s classified as COMPROMISED BREACH RISK", device)
            quarantine(device)
        else:
            log.info("%s is safe", device)


if __name__ == "__main__":
    main()
