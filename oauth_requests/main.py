import httpx
import sys
import types
import nest_asyncio
import os
import base64

nest_asyncio.apply()
BASE_URL = "${env.NEXT_PUBLIC_MANAFLOW_SERVER_URL}/notebook"
MANAFLOW_TOKEN = "${manaflowToken}"

class ProxiedClient(httpx.Client):
    def request(self, method, url, *args, **kwargs):
        proxied_url = f"{BASE_URL}/oauth_proxy/{url}"
        headers = kwargs.pop("headers", {}) or {}
        headers["X-Manaflow-Token"] = MANAFLOW_TOKEN
        kwargs["timeout"] = httpx.Timeout(connect=10, read=300, write=300, pool=60)
        return super().request(method, proxied_url, headers=headers, *args, **kwargs)

oauth_requests = ProxiedClient()

__fake_oauth_requests_module__ = types.ModuleType("oauth_requests")
__fake_oauth_requests_module__.get = oauth_requests.get
__fake_oauth_requests_module__.post = oauth_requests.post
__fake_oauth_requests_module__.put = oauth_requests.put
__fake_oauth_requests_module__.patch = oauth_requests.patch
__fake_oauth_requests_module__.delete = oauth_requests.delete
__fake_oauth_requests_module__.request = oauth_requests.request

sys.modules["oauth_requests"] = __fake_oauth_requests_module__

del __fake_oauth_requests_module__

class ManaflowUtils:
    def get_public_url(self, filepath: str) -> str:
        filename = os.path.basename(filepath)
        with open(filepath, 'rb') as f:
            files = {'file': (filename, f)}
            response = httpx.post('https://fileio.debussy.workers.dev', files=files, timeout=None)
            response.raise_for_status()
            return response.json()['url']

    def get_public_url_old(self, filepath: str) -> str:
        if filepath.startswith("/"):
            filepath = filepath[1:]
        return f"{BASE_URL}/download/{filepath}"

    def get_public_url_fileio(self, filepath: str) -> str:
        filename = os.path.basename(filepath)
        with open(filepath, 'rb') as f:
            files = {'file': (filename, f)}
            response = httpx.post('https://fileio.debussy.workers.dev', files=files, timeout=None)
            response.raise_for_status()
            return response.json()['url']

    def send_email(self, to: list[str], subject: str, html: str, attachments: list[dict[str, str]] = []):
        attachment_data = []
        for attachment in attachments:
            path = attachment.get("path")
            if not path or not os.path.isfile(path):
                raise ValueError(f"Invalid attachment path: {path}")
            with open(path, "rb") as f:
                base64content = base64.b64encode(f.read()).decode("utf-8")
                filename = os.path.basename(path)
                attachment_data.append({"filename": filename, "base64content": base64content})
        timeout = httpx.Timeout(900, connect=120.0)  # 900 seconds total, 120 seconds to establish a connection
        response = httpx.post(f"{BASE_URL}/utils/send_email", json={
            "to": to,
            "subject": subject,
            "html": html,
            "attachments": attachment_data
        }, timeout=timeout, headers={"X-Manaflow-Token": MANAFLOW_TOKEN})
        response.raise_for_status()
        return response.json()

utils = ManaflowUtils()
__fake_utils_module__ = types.ModuleType("utils")
__fake_utils_module__.get_public_url = utils.get_public_url
__fake_utils_module__.get_public_url_fileio = utils.get_public_url_fileio
__fake_utils_module__.send_email = utils.send_email

sys.modules["utils"] = __fake_utils_module__

del __fake_utils_module__