#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Temporary and Volatile File Manager (Final/Nihai Version)
# Copyright (C) 2026, Ergün Salman ergunsalman@hotmail.com Poyraz76
#
# ALTYAPI: Python 3.12+, x86_64, SQLite DB.
# GÜVENLİK: BLAKE3 (İçerik mühürleme ve doğrulama).
# ARŞİVLEME: Zstd (Geçici veri yönetimi ve yedekleme).
# SİSTEM: Systemd-free (Müdür + Çomar uyumlu).

import os
import sys
import stat
import shutil
import sqlite3
import logging
import zstandard as zstd
from pathlib import Path
from pwd import getpwnam
from grp import getgrnam
from blake3 import blake3

# --- 2026 Standart Konfigürasyonu ---
CONFIG_DIRS = [
    Path("/etc/tmpfiles.d"), 
    Path("/run/tmpfiles.d"), 
    Path("/usr/lib/tmpfiles.d")
]
DB_PATH = Path("/var/lib/pisi/inventory.db")

class TmpFileManager:
    """Sistemin geçici dosya ve dizin hiyerarşisini mühürleyen motor."""

    def __init__(self, boot_mode=False):
        self.boot = boot_mode
        self.logger = self.setup_logger()
        self.errors = []

    def setup_logger(self):
