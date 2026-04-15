# -*- coding: utf-8 -*-
#
# Copyright (C) 2026, Ergün Salman ergunsalman@hotmail.com Poyraz76
# [Lisans: GNU General Public License v2 ve sonrası]
#
# ALTYAPI: Python 3.12+, x86_64, SQLite DB.
# GÜVENLİK: BLAKE3 (İşlem doğrulaması).
# ARŞİVLEME: Zstd (Silinen kullanıcı yedeği).
# SİSTEM: Systemd-free, Müdür + Çomar uyumlu.

import os
import pwd
import sys
import dbus
import sqlite3
import logging
import argparse
import tarfile
import zstandard as zstd
from pathlib import Path
from blake3 import blake3

# --- Yapılandırma ---
DB_PATH = Path("/var/lib/pisi/inventory.db")
BACKUP_DIR = Path("/var/cache/pisi/backups")

class UserDeleter:
    """Çomar üzerinden güvenli kullanıcı silme motoru."""
    
    def __init__(self):
        self.logger = self.setup_logger()
        self.bus = self.connect_to_dbus()

    def setup_logger(self):
        """Temiz hiyerarşik log yapısı."""
        logging.basicConfig(level=logging.INFO, format='[*] %(message)s')
        return logging.getLogger("UserDeleter")

    def connect_to_dbus(self):
        """Çomar ile asenkron bağ için DBus bağlantısı."""
        try:
            return dbus.SystemBus()
        except dbus.DBusException:
            self.ai_error_analysis("DBus bağlantısı kurulamadı.", "SİSTEM")
            sys.exit(1)

    def ai_error_analysis(self, msg: str, context: str):
        """ZEKA: AI hata analizi ve teknisyen çözüm önerisi."""
        print(f"\n\033[1;91m[!] AI ANALİZİ - {context}: {msg}\033[0m")
        print("[*] Poyraz76 Önerisi: Çomar servisi (comar-daemon) çalışmıyor olabilir.")
        print("[*] Aksiyon: 'mudur status comar' komutuyla servis durumunu kontrol edin.")

    def archive_user_home(self, username: str):
        """Silmeden önce kullanıcı ev dizinini Zstd (Level 12) ile arşivler."""
        user_home = Path(f"/home/{username}")
        if not user_home.exists():
            self.logger.warning(f"Ev dizini bulunamadı, arşivleme atlanıyor: {user_home}")
            return

        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        archive_path = BACKUP_
