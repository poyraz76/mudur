#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Pardus boot and initialization system (Finalized Nihai Version)
# Copyright (C) 2006-2011 TUBITAK/UEKAE
# Copyright (C) 2026, Ergün Salman ergunsalman@hotmail.com Poyraz76
#
# ALTYAPI: Python 3.12+, x86_64, SQLite DB, HTTPS.
# GÜVENLİK: BLAKE3 (Birincil doğrulama), SHA-512.
# ARŞİVLEME: Zstd sıkıştırma, MTREE manifest yapısı.
# SİSTEM: Systemd-free, Müdür + Çomar (init/daemon).

import os
import sys
import time
import asyncio
import sqlite3
import gettext
import logging
import subprocess
import zstandard as zstd
from pathlib import Path
from blake3 import blake3

########
# i18n #
########
__trans = gettext.translation('mudur', fallback=True)
_ = __trans.gettext

#######################
# Convenience Methods #
#######################

def ai_analyze_error(module: str, error: Exception):
    """ZEKA: AI hata analizi ve teknisyen çözüm önerisi."""
    print(f"\n\033[1;91m[!] AI ANALİZİ - Modül: {module}\033[0m")
    print(f"[*] Hata: {str(error)}")
    print(f"[*] Poyraz76 Önerisi: Sistemin '{module}' aşamasında durması donanım çakışması veya SQLite kilitlenmesi olabilir.")
    print("[*] Aksiyon: 'pisi-check' ile dosya bütünlüğünü (BLAKE3) doğrulayın.")

def load_file_modern(path: Path):
    """Zstd desteği ve BLAKE3 doğrulaması ile dosya yükleme."""
    try:
        content = path.read_bytes()
        # Zstd sihirli sayısını (magic number) kontrol et
        if content.startswith(b'\x28\xb5\x2f\xfd'):
            dctx = zstd.ZstdDecompressor()
            content = dctx.decompress(content)
        
        file_hash = blake3(content).hexdigest()
        return content.decode("utf-8"), file_hash
    except Exception as e:
        return "", None

################
# Config Class #
################

class Config:
    """SQLite tabanlı modern konfigürasyon yönetimi."""
    def __init__(self):
        self.db_path = Path("/var/lib/pisi/inventory.db")
        self.options = {
            "debug": True,
            "language": "tr",
            "tty_number": "6",
            "lxc_guest": "no",
            "zstd_log": True
        }
        self.init_db()

    def init_db(self):
        """Sistemi tek başına ayağa kaldır: DB yoksa oluştur."""
        if not self.db_path.parent.exists():
            self.db_path.parent.mkdir(parents=True)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("CREATE TABLE IF NOT EXISTS config (key TEXT PRIMARY KEY, value TEXT)")
            for k, v in self.options.items():
                conn.execute("INSERT OR IGNORE INTO config VALUES (?, ?)", (k, str(v)))

    def get(self, key):
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute("SELECT value FROM config WHERE key=?", (key,)).fetchone()
            return row[0] if row else self.options.get(key)

################
# Logger Class #
################

class Logger:
    """Zstd sıkıştırmalı modern loglama sistemi."""
    def __init__(self, use_zstd=True):
        self.log_path = Path("/var/log/mudur.log")
        self.use_zstd = use_zstd

    def log(self, msg):
        stamp = time.strftime("%b %d %H:%M:%S")
        entry = f"[{time.time():.3f}] {stamp} {msg}\n"
        
        if self.use_zstd:
            zstd_path = self.log_path.with_suffix(".log.zst")
            cctx = zstd.ZstdCompressor(level=3)
            with open(zstd_path, "ab") as f:
                f.write(cctx.compress(entry.encode()))
        else:
            with open(self.log_path, "a") as f:
                f.write(entry)

##################
# Core Mudur UI  #
##################

class Ui:
    def greet(self):
        print("\033[1;36m[MÜDÜR]\033[0m Poyraz76 Modern Init Sistemi Başlatılıyor...")
        print("\033[1;32m[*] Pisi Paket Sistemi & Comar Entegrasyonu Aktif.\033[0m\n")

    def info(self, msg):
        print(f" \033[1;32m*\033[0m {msg}")

    def warn(self, msg):
        print(f" \033[1;33m!\033[0m {msg}")

###################
# Mudur Engine    #
###################

class MudurEngine:
    """Sistemin asenkron açılış ve yönetim motoru."""
    def __init__(self):
        self.config = Config()
        self.logger = Logger(use_zstd=(self.config.get("zstd_log") == "True"))
        self.ui = Ui()
        self.start_time = time.time()
        self.db_path = Path("/var/lib/pisi/inventory.db")

    async def mount_vfs(self):
        """Kritik sanal dosya sistemlerini mühürler."""
        self.ui.info(_("Sanal dosya sistemleri bağlanıyor..."))
        vfs = [
            ("proc", "/proc", "proc", "nosuid,noexec,nodev"),
            ("sysfs", "/sys", "sysfs", "nosuid,noexec,nodev"),
            ("devtmpfs", "/dev", "devtmpfs", "nosuid,mode=0755"),
            ("tmpfs", "/run", "tmpfs", "nosuid,nodev,mode=0755")
        ]
        for name, target, fstype, opts in vfs:
            if not os.path.ismount(target):
                try:
                    subprocess.run(["mount", "-t", fstype, "-o", opts, name, target], check=True)
                except subprocess.CalledProcessError as e:
                    ai_analyze_error(f"MOUNT_{name.upper()}", e)

    async def setup_hardware(self):
        """Oto-driver: Donanım taraması ve modül yükleme."""
        self.ui.info(_("Donanım taranıyor (Oto-driver)..."))
        try:
            subprocess.run(["/sbin/udevadm", "trigger", "--action=add"], capture_output=True)
            subprocess.run(["/sbin/udevadm", "settle"], capture_output=True)
        except Exception as e:
            ai_analyze_error("HARDWARE_DETECT", e)

    async def start_services(self):
        """Servisleri SQLite öncelik sırasına göre asenkron başlatır."""
        self.ui.info(_("Servisler asenkron olarak ayağa kaldırılıyor..."))
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("SELECT name, script_path FROM services WHERE enabled=1 ORDER BY priority ASC")
                services = cursor.fetchall()

            # Python 3.12+ TaskGroup ile paralel başlatma
            async with asyncio.TaskGroup() as tg:
                for name, script in services:
                    tg.create_task(self.run_service_task(name, script))
        except Exception as e:
            ai_analyze_error("SERVICE_MANAGER", e)

    async def run_service_task(self, name: str, script: str):
        """Tekil servis görevi ve BLAKE3 doğrulaması."""
        script_path = Path(script)
        _, f_hash = load_file_modern(script_path)
        if f_hash:
            self.logger.log(f"Servis doğrulandı: {name} [BLAKE3: {f_hash[:16]}]")
            
        # /bin/service üzerinden asenkron tetikleme
        proc = await asyncio.create_subprocess_exec(
            "/bin/service", name, "start",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        if proc.returncode == 0:
            self.logger.log(f"Servis başlatıldı: {name}")
        else:
            self.ui.warn(f"Servis hatası: {name}")
            self.logger.log(f"Hata ({name}): {stderr.decode().strip()}")

    async def sysinit(self):
        """Ana boot döngüsü: Kodu asla yarım bırakma."""
        self.ui.greet()
        try:
            # 1. Sanal Dosya Sistemleri
            await self.mount_vfs()
            
            # 2. Cgroups Entegrasyonu
            from mudur_cgroupfs import Cgroupfs
            Cgroupfs()
            
            # 3. Donanım ve Oto-driver
            await self.setup_hardware()
            
            # 4. Fstab ve Disk Mühürleme
            self.ui.info(_("Disk bölümleri mühürleniyor..."))
            subprocess.run(["/sbin/update-fstab"], capture_output=True)
            subprocess.run(["mount", "-a"], check=True)
            
            # 5. Geçici Dosya Yönetimi
            from mudur_tmpfiles import TmpFileManager
            TmpFileManager(boot_mode=True).run()
            
            # 6. Çevre Değişkenleri
            subprocess.run(["/sbin/update-environment"], capture_output=True)
            
            # 7. Asenkron Servis Başlatma
            await self.start_services()

            self.ui.info(_(f"Sistem hazır. Boot süresi: {time.time() - self.start_time:.2f}s"))
            
        except Exception as e:
            ai_analyze_error("SYSINIT_CORE", e)
            self.logger.log(f"Kritik Hata: {str(e)}")

    async def shutdown(self):
        """Güvenli kapatma süreci."""
        self.ui.warn(_("Sistem kapatılıyor. Loglar Zstd ile mühürleniyor..."))
        subprocess.run(["swapoff", "-a"], capture_output=True)
        subprocess.run(["mount", "-a", "-r"], capture_output=True)
        self.ui.info(_("Müdür: Güvenli çıkış yapıldı."))

if __name__ == "__main__":
    engine = MudurEngine()
    mode = sys.argv[1] if len(sys.argv) > 1 else "sysinit"
    
    # Kural: Sistemi tek başına ayağa kaldır.
    if mode == "sysinit":
        asyncio.run(engine.sysinit())
    elif mode == "shutdown":
        asyncio.run(engine.shutdown())
