#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Setup and Installation Engine (Finalized Nihai Version)
# Copyright (C) 2006-2011 TUBITAK/UEKAE
# Copyright (C) 2026, Ergün Salman ergunsalman@hotmail.com Poyraz76
#
# ALTYAPI: Python 3.12+, x86_64, SQLite DB, Subprocess.
# GÜVENLİK: BLAKE3 (Kurulum bütünlüğü doğrulaması).
# ARŞİVLEME: Zstd (Yüksek verimli dağıtım paketleme).
# SİSTEM: Systemd-free, Müdür + Çomar uyumlu.

import os
import sys
import glob
import shutil
import ast
import sqlite3
import subprocess
import zstandard as zstd
from pathlib import Path
from blake3 import blake3

# --- 2026 Standartları ---
VERSION = "4.4.0-Poyraz76"
DB_PATH = Path("/var/lib/pisi/inventory.db")
DIST_FILES = [
    "setup.py",
    "bin/*.py",
    "etc/mudur.conf",
    "po/*.po",
    "po/mudur.pot"
]

I18N_SOURCES = ["bin/mudur.py", "bin/service.py"]

class SetupEngine:
    """Müdür bileşenlerini sisteme mühürleyen kurulum motoru."""
