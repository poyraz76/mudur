# -*- coding: utf-8 -*-
#
# Copyright (C) 2026, Ergün Salman ergunsalman@hotmail.com Poyraz76
# [Lisans: GNU Library General Public License v2 ve sonrası]
#
# ALTYAPI: Python 3.12+, x86_64, SQLite DB.
# GÜVENLİK: BLAKE3 (Durum mühürleme ve doğrulama).
# ARŞİVLEME: Zstd (Sistem kaynak haritası yedekleme).
# SİSTEM: Systemd-free, Müdür + Çomar (init/daemon) uyumlu.

import os
import sys
import sqlite3
import subprocess
import logging
import zstandard as zstd
from pathlib import Path
from typing import Dict, List
from blake3 import blake3

# --- Sabitler ve Hiyerarşi ---
CGROUP_ROOT = Path("/sys/fs/cgroup")
PROC_CGROUPS = Path("/proc/cgroups")
DB_PATH = Path("/var/lib/pisi/inventory.db")
SNAPSHOT_PATH = Path("/var/lib/pisi/cgroup_snapshot.zst")

def is_mountpoint(path: Path) -> bool:
    """Aygıtın bağlı olup olmadığını modern yöntemle kontrol eder."""
    try:
        return subprocess.run(["mountpoint", "-q", str(path)], check=True).returncode == 0
    except subprocess.CalledProcessError:
        return False

class Controller:
    """Cgroup Kontrolcü (Subsystem) Yönetici Sınıfı."""
    def __init__(self, name: str, hierarchy: int, num_cgroups: int, enabled: bool):
        self.name = name
        self.hierarchy = hierarchy
        self.num_cgroups = num_cgroups
        self.enabled = enabled
        self.mount_path = CGROUP_ROOT / name

    def mount(self) -> bool:
        """Kontrolcüyü ilgili dizine mühürler."""
        if not self.enabled:
            return False

        try:
            if not is_mountpoint(self.mount_path):
                self.mount_path.mkdir(parents=True, exist_ok=True)
                # KURAL: Modern x86_64 performansı için doğrudan mount çağrısı.
                cmd = ["mount", "-n", "-t", "cgroup", "-o", self.name, "cgroup", str(self.mount_path)]
                subprocess.run(cmd, check=True, capture_output=True)
                return
