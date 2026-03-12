from urllib.parse import urlparse
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

from server import PromptServer


class JunsAirgapGuard:
    CATEGORY = "Jun's Nodes"
    FUNCTION = "check"
    RETURN_TYPES = ()
    OUTPUT_NODE = True
    DESCRIPTION = "Checks whether a specified URL is reachable and optionally blocks execution."

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "url": (
                    "STRING",
                    {
                        "default": "https://example.com",
                        "multiline": False,
                        "tooltip": "Target URL to test. Only http:// and https:// are allowed.",
                    },
                ),
                "timeout_seconds": (
                    "INT",
                    {
                        "default": 3,
                        "min": 1,
                        "max": 60,
                        "step": 1,
                        "tooltip": "Timeout in seconds for the connectivity check.",
                    },
                ),
                "mode": (
                    [
                        "block_if_reachable",
                        "block_if_unreachable",
                        "report_only",
                    ],
                    {
                        "default": "block_if_reachable",
                        "tooltip": "Choose whether to stop when the target is reachable, unreachable, or never stop.",
                    },
                ),
                "probe_token": (
                    "INT",
                    {
                        "default": 0,
                        "min": 0,
                        "max": 2147483647,
                        "step": 1,
                        "tooltip": "Change this value each run to force re-checking in V1.",
                    },
                ),
            },
            "hidden": {
                "unique_id": "UNIQUE_ID",
            },
        }

    @classmethod
    def IS_CHANGED(cls, url, timeout_seconds, mode, probe_token, unique_id=None):
        return f"{url}|{timeout_seconds}|{mode}|{probe_token}"

    def _send_status(self, unique_id, state, reachable, message, http_status=None):
        if unique_id is None:
            return

        payload = {
            "node_id": str(unique_id),
            "state": state,              # idle / checking / reachable / unreachable / invalid
            "reachable": reachable,      # True / False / None
            "message": message,
            "http_status": http_status,
        }

        try:
            PromptServer.instance.send_sync("juns_airgap_guard_status", payload)
        except Exception:
            pass

    def _validate_url(self, url: str):
        parsed = urlparse(url.strip())
        if parsed.scheme not in ("http", "https"):
            raise ValueError("URL must start with http:// or https://")
        if not parsed.netloc:
            raise ValueError("Host name is invalid")

    def _probe(self, url: str, timeout_seconds: int):
        req = Request(
            url,
            method="HEAD",
            headers={
                "User-Agent": "JunsAirgapGuard/1.1",
            },
        )

        try:
            with urlopen(req, timeout=timeout_seconds) as resp:
                status = getattr(resp, "status", 200)
                return True, f"Reachable (HTTP {status})", status

        except HTTPError as e:
            return True, f"Reachable (HTTP {e.code})", e.code

        except URLError as e:
            reason = getattr(e, "reason", e)
            return False, f"Unreachable ({reason})", None

        except Exception as e:
            return False, f"Unreachable ({type(e).__name__}: {e})", None

    def check(self, url, timeout_seconds, mode, probe_token, unique_id=None):
        url = url.strip()

        try:
            self._validate_url(url)
        except Exception as e:
            msg = f"Invalid URL: {e}"
            self._send_status(unique_id, "invalid", None, msg, None)
            raise RuntimeError(f"Jun's Airgap Guard: {msg}")

        self._send_status(unique_id, "checking", None, "Checking...", None)

        reachable, message, http_status = self._probe(url, timeout_seconds)
        state = "reachable" if reachable else "unreachable"
        self._send_status(unique_id, state, reachable, message, http_status)

        if mode == "block_if_reachable" and reachable:
            raise RuntimeError(
                f"Jun's Airgap Guard: blocked because the target was reachable. {message}"
            )

        if mode == "block_if_unreachable" and not reachable:
            raise RuntimeError(
                f"Jun's Airgap Guard: blocked because the target was unreachable. {message}"
            )

        return ()


NODE_CLASS_MAPPINGS = {
    "JunsAirgapGuard": JunsAirgapGuard,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "JunsAirgapGuard": "🛡️ Jun's Airgap Guard",
}
