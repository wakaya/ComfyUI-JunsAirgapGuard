from urllib.parse import urlparse
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
import locale
import os

from server import PromptServer


class JunsAirgapGuard:
    CATEGORY = "Jun's Nodes"
    FUNCTION = "check"
    RETURN_TYPES = ()
    OUTPUT_NODE = True
    DESCRIPTION = "Checks whether a specified URL is reachable and optionally blocks execution."

    I18N = {
        "en": {
            "invalid_url_prefix": "URL must start with http:// or https://",
            "invalid_host": "Host name is invalid",
            "invalid_url": "Invalid URL: {reason}",
            "checking": "Checking...",
            "reachable_http": "Reachable (HTTP {status})",
            "unreachable_reason": "Unreachable ({reason})",
            "unreachable_exception": "Unreachable ({etype}: {message})",
            "blocked_reachable": "Jun's Airgap Guard: blocked because the target was reachable. {message}",
            "blocked_unreachable": "Jun's Airgap Guard: blocked because the target was unreachable. {message}",
        },
        "ja": {
            "invalid_url_prefix": "URL は http:// または https:// で始めてください。",
            "invalid_host": "URL のホスト名が不正です。",
            "invalid_url": "URL 不正: {reason}",
            "checking": "確認中...",
            "reachable_http": "つながった (HTTP {status})",
            "unreachable_reason": "つながらなかった ({reason})",
            "unreachable_exception": "つながらなかった ({etype}: {message})",
            "blocked_reachable": "Jun's Airgap Guard: 指定先につながったので停止しました。 {message}",
            "blocked_unreachable": "Jun's Airgap Guard: 指定先につながらなかったので停止しました。 {message}",
        },
    }

    MODE_ALIASES = {
        "block_if_reachable": "block_if_reachable",
        "block_if_unreachable": "block_if_unreachable",
        "report_only": "report_only",

        "Block if reachable": "block_if_reachable",
        "Block if unreachable": "block_if_unreachable",
        "Report only": "report_only",

        "オンラインなら停止": "block_if_reachable",
        "オフラインなら停止": "block_if_unreachable",
        "停止しない": "report_only",
    }

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

    def _detect_lang(self):
        candidates = []

        try:
            loc = locale.getlocale()
            if loc and loc[0]:
                candidates.append(loc[0])
        except Exception:
            pass

        for key in ("LC_ALL", "LC_MESSAGES", "LANG", "LANGUAGE"):
            value = os.environ.get(key)
            if value:
                candidates.append(value)

        for value in candidates:
            lower = str(value).lower()
            if lower.startswith("ja"):
                return "ja"

        return "en"

    def _t(self, lang, key, **kwargs):
        table = self.I18N.get(lang, self.I18N["en"])
        text = table.get(key, self.I18N["en"].get(key, key))
        return text.format(**kwargs)

    def _normalize_mode(self, mode):
        if mode is None:
            return "block_if_reachable"
        return self.MODE_ALIASES.get(str(mode).strip(), "block_if_reachable")

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

    def _validate_url(self, url: str, lang: str):
        parsed = urlparse(url.strip())
        if parsed.scheme not in ("http", "https"):
            raise ValueError(self._t(lang, "invalid_url_prefix"))
        if not parsed.netloc:
            raise ValueError(self._t(lang, "invalid_host"))

    def _probe(self, url: str, timeout_seconds: int, lang: str):
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
                return True, self._t(lang, "reachable_http", status=status), status

        except HTTPError as e:
            return True, self._t(lang, "reachable_http", status=e.code), e.code

        except URLError as e:
            reason = getattr(e, "reason", e)
            return False, self._t(lang, "unreachable_reason", reason=reason), None

        except Exception as e:
            return False, self._t(
                lang,
                "unreachable_exception",
                etype=type(e).__name__,
                message=e,
            ), None

    def check(self, url, timeout_seconds, mode, probe_token, unique_id=None):
        lang = self._detect_lang()
        url = url.strip()
        mode = self._normalize_mode(mode)

        try:
            self._validate_url(url, lang)
        except Exception as e:
            msg = self._t(lang, "invalid_url", reason=e)
            self._send_status(unique_id, "invalid", None, msg, None)
            raise RuntimeError(f"Jun's Airgap Guard: {msg}")

        self._send_status(unique_id, "checking", None, self._t(lang, "checking"), None)

        reachable, message, http_status = self._probe(url, timeout_seconds, lang)
        state = "reachable" if reachable else "unreachable"
        self._send_status(unique_id, state, reachable, message, http_status)

        if mode == "block_if_reachable" and reachable:
            raise RuntimeError(self._t(lang, "blocked_reachable", message=message))

        if mode == "block_if_unreachable" and not reachable:
            raise RuntimeError(self._t(lang, "blocked_unreachable", message=message))

        return ()


NODE_CLASS_MAPPINGS = {
    "JunsAirgapGuard": JunsAirgapGuard,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "JunsAirgapGuard": "🛡️ Jun's Airgap Guard",
}
