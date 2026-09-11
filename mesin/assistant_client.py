"""Klien HTTPS OpenAI-compatible khusus chat Pendamping."""

from __future__ import annotations

from dataclasses import dataclass
import json
import urllib.error
import urllib.parse
import urllib.request

BATAS_WAKTU_DETIK = 25
BATAS_RESPONS_BYTE = 128_000


class GalatProvider(RuntimeError):
    """Kegagalan provider yang aman ditampilkan sebagai kategori umum."""


@dataclass(frozen=True)
class Konfigurasi:
    base_url: str
    api_key: str
    model: str

    def __post_init__(self) -> None:
        hasil = urllib.parse.urlsplit(self.base_url)
        if hasil.scheme != "https" or not hasil.netloc or hasil.username or hasil.password:
            raise ValueError("Base URL provider wajib HTTPS.")
        if hasil.query or hasil.fragment:
            raise ValueError("Base URL provider tidak boleh memuat query.")
        if not self.api_key.strip() or not self.model.strip():
            raise ValueError("Konfigurasi provider belum lengkap.")
        object.__setattr__(self, "base_url", self.base_url.rstrip("/"))


class _TanpaRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def kirim(config: Konfigurasi, pesan: list[dict[str, str]]) -> dict:
    """Kirim request terbatas; redirect, response besar, dan JSON rusak gagal."""
    tubuh = json.dumps({
        "model": config.model,
        "messages": pesan,
        "temperature": 0.4,
        "max_tokens": 1200,
        "response_format": {"type": "json_object"},
    }, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    req = urllib.request.Request(
        config.base_url + "/chat/completions",
        data=tubuh,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {config.api_key}",
        },
        method="POST",
    )
    try:
        pembuka = urllib.request.build_opener(_TanpaRedirect())
        with pembuka.open(req, timeout=BATAS_WAKTU_DETIK) as respons:
            panjang = respons.headers.get("Content-Length") if respons.headers else None
            if panjang and int(panjang) > BATAS_RESPONS_BYTE:
                raise GalatProvider("respons terlalu besar")
            mentah = respons.read(BATAS_RESPONS_BYTE + 1)
            if len(mentah) > BATAS_RESPONS_BYTE:
                raise GalatProvider("respons terlalu besar")
    except urllib.error.HTTPError as galat:
        if 300 <= galat.code < 400:
            raise GalatProvider("redirect provider ditolak") from None
        if galat.code == 429:
            raise GalatProvider("batas provider tercapai") from None
        raise GalatProvider("provider tidak tersedia") from None
    except GalatProvider:
        raise
    except (urllib.error.URLError, OSError, ValueError):
        raise GalatProvider("provider tidak tersedia") from None
    try:
        data = json.loads(mentah.decode("utf-8"))
        konten = data["choices"][0]["message"]["content"]
        if type(konten) is not str:
            raise ValueError
        hasil = json.loads(konten)
        if type(hasil) is not dict:
            raise ValueError
        return hasil
    except (UnicodeDecodeError, json.JSONDecodeError, KeyError, IndexError, TypeError, ValueError):
        raise GalatProvider("respons provider tidak sah") from None
