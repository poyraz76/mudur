#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2007-2009 TUBITAK/UEKAE
# Copyright (C) 2026, Ergün Salman ergunsalman@hotmail.com Poyraz76
#
# ALTYAPI: Python 3.12+, x86_64, SQLite DB.
# GÜVENLİK: BLAKE3 (Bütünlük doğrulaması).
# ARŞİVLEME: Zstd (Eski init.d yapısı yedeği).
# SİSTEM: Systemd-free (Müdür + Çomar Uyumluluk Katmanı).

import subprocess
import sys
import os
import sqlite3
import logging
import zstandard as zstd
from pathlib import Path
from blake3 import blake3

# --- Konfigürasyon ---
DB_PATH = Path("/var/lib/pisi/inventory.db")
INITD_PATH = Path("/etc/init.d")
SERVICE_BINARY = Path("/bin/service")
BACKUP_PATH = Path("/var/cache/pisi/backups/initd_legacy.tar.zst")

class CompatManager:
    """Legacy init.d komutlarını modern Müdür servis
