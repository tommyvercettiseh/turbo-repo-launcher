from __future__ import annotations

import base64
import ctypes
import ftplib
import json
import ssl
from ctypes import wintypes
from pathlib import Path
from typing import Any

from .config import load_settings, save_settings


class DATA_BLOB(ctypes.Structure):
    _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_byte))]


def _protect(value: str) -> str:
    if not value:
        return ""
    if not hasattr(ctypes, "windll"):
        return base64.b64encode(value.encode("utf-8")).decode("ascii")
    raw = value.encode("utf-8")
    source = DATA_BLOB(len(raw), ctypes.cast(ctypes.create_string_buffer(raw), ctypes.POINTER(ctypes.c_byte)))
    target = DATA_BLOB()
    if not ctypes.windll.crypt32.CryptProtectData(ctypes.byref(source), "Turbo Repo Hub FTP", None, None, None, 0, ctypes.byref(target)):
        raise RuntimeError("FTP-wachtwoord kon niet veilig worden opgeslagen.")
    try:
        data = ctypes.string_at(target.pbData, target.cbData)
        return base64.b64encode(data).decode("ascii")
    finally:
        ctypes.windll.kernel32.LocalFree(target.pbData)


def _unprotect(value: str) -> str:
    if not value:
        return ""
    encrypted = base64.b64decode(value)
    if not hasattr(ctypes, "windll"):
        return encrypted.decode("utf-8")
    source = DATA_BLOB(len(encrypted), ctypes.cast(ctypes.create_string_buffer(encrypted), ctypes.POINTER(ctypes.c_byte)))
    target = DATA_BLOB()
    if not ctypes.windll.crypt32.CryptUnprotectData(ctypes.byref(source), None, None, None, None, 0, ctypes.byref(target)):
        raise RuntimeError("FTP-wachtwoord kon niet worden gelezen.")
    try:
        return ctypes.string_at(target.pbData, target.cbData).decode("utf-8")
    finally:
        ctypes.windll.kernel32.LocalFree(target.pbData)


class FtpService:
    @staticmethod
    def get_settings(include_password: bool = False) -> dict[str, Any]:
        data = dict(load_settings().get("ftp") or {})
        result = {
            "host": data.get("host", ""),
            "username": data.get("username", ""),
            "port": int(data.get("port") or 21),
            "protocol": data.get("protocol") or "ftps",
            "base_directory": data.get("base_directory") or "/public_html/",
            "password_saved": bool(data.get("password_encrypted")),
        }
        if include_password:
            result["password"] = _unprotect(data.get("password_encrypted", ""))
        return result

    @staticmethod
    def save_settings(payload: dict[str, Any]) -> dict[str, Any]:
        settings = load_settings()
        existing = dict(settings.get("ftp") or {})
        password = payload.get("password") or ""
        existing.update({
            "host": payload.get("host", "").strip(),
            "username": payload.get("username", "").strip(),
            "port": int(payload.get("port") or 21),
            "protocol": payload.get("protocol") or "ftps",
            "base_directory": FtpService.normalize_directory(payload.get("base_directory") or "/public_html/"),
        })
        if password:
            existing["password_encrypted"] = _protect(password)
        settings["ftp"] = existing
        save_settings(settings)
        return FtpService.get_settings()

    @staticmethod
    def normalize_directory(directory: str) -> str:
        value = "/" + directory.strip().replace("\\", "/").strip("/") + "/"
        return value.replace("//", "/")

    @staticmethod
    def set_project_directory(slug: str, directory: str) -> dict[str, str]:
        settings = load_settings()
        directories = settings.setdefault("ftp_project_directories", {})
        directories[slug] = FtpService.normalize_directory(directory)
        save_settings(settings)
        return {"slug": slug, "directory": directories[slug]}

    @staticmethod
    def get_project_directory(slug: str) -> str:
        settings = load_settings()
        custom = (settings.get("ftp_project_directories") or {}).get(slug)
        if custom:
            return custom
        base = FtpService.get_settings().get("base_directory") or "/public_html/"
        return FtpService.normalize_directory(f"{base}/{slug}")

    @staticmethod
    def test_connection() -> dict[str, Any]:
        cfg = FtpService.get_settings(include_password=True)
        if not cfg["host"] or not cfg["username"] or not cfg.get("password"):
            raise RuntimeError("Vul eerst FTP-server, gebruikersnaam en wachtwoord in.")
        protocol = cfg["protocol"].lower()
        if protocol == "sftp":
            raise RuntimeError("SFTP-test vereist een aparte SSH-module. Kies FTP of FTPS voor Hostnet.")
        ftp = ftplib.FTP_TLS() if protocol == "ftps" else ftplib.FTP()
        try:
            ftp.connect(cfg["host"], cfg["port"], timeout=12)
            ftp.login(cfg["username"], cfg["password"])
            if protocol == "ftps":
                ftp.prot_p()
            ftp.cwd(cfg["base_directory"])
            return {"ok": True, "message": f"Verbinding gelukt met {cfg['host']}{cfg['base_directory']}"}
        except (OSError, ftplib.all_errors, ssl.SSLError) as exc:
            raise RuntimeError(f"FTP-verbinding mislukt: {exc}") from exc
        finally:
            try:
                ftp.quit()
            except Exception:
                pass
