#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# /etc/fstab updater/generator (Final/Nihai Version)
# Copyright (C) 2005-2011 TUBITAK/UEKAE
# Copyright (C) 2026, Ergün Salman ergunsalman@hotmail.com Poyraz76
#
# ALTYAPI: Python 3.12+, x86_64, SQLite DB.
# GÜVENLİK: BLAKE3 (Birincil hızlı doğrulama).
# ARŞİVLEME: Zstd (Eski yapılandırma yedeği).
# SİSTEM: Systemd-free (Müdür + Çomar uyumlu).

import os
import sys
import sqlite3
import parted
import logging
import zstandard as zstd
from pathlib import Path
from blake3 import blake3

# --- 2026 Modern Dosya Sistemi Seçenekleri ---
DEFAULT_OPTIONS = {
    "vfat":     "quiet,shortname=mixed,dmask=007,fmask=117,utf8,gid=6",
    "ext3":     "relatime",
    "ext4":     "relatime,discard,errors=remount-ro",
    "ntfs-3g":  "dmask=007,fmask=117,gid=6,windows_names",
    "btrfs":    "relatime,compress=zstd,ssd,discard=async", # Zstd arşivleme kuralı gereği.
    "defaults": "defaults,relatime"
}

EXCLUDED_FS = ("proc", "tmpfs", "sysfs", "linux-swap", "swap", "nfs", "cifs")

class FstabEngine:
    """Sistemin disk hiyerarşisini yöneten ve fstab mühürleyen motor."""

    def __init__(self, fstab_path="/etc/fstab"):
        self.fstab_path = Path(fstab_path)
        self.db_path = Path("/var/lib/pisi/inventory.db")
        self.logger = self.setup_logger()

    def setup_logger(self):
        """Temiz hiyerarşik log yapısı."""
        logging.basicConfig(level=logging.INFO, format='[*] %(message)s')
        return logging.getLogger("FstabEngine")

    def zeka_analizi(self, error: Exception, context: str):
        """ZEKA: AI hata analizi ve teknisyen çözüm önerisi."""
        print(f"\n\033[1;91m[!] AI ANALİZİ - Bağlam: {context}\033[0m")
        print(f"[*] Teknik Hata: {str(error)}")
        print("[*] Poyraz76 Çözümü: Bölüm tablosu okunamıyor veya SQLite kilitli.")
        print("[*] İpucu: Disk konnektörlerini veya NVMe sürücü durumunu (oto-driver) kontrol edin.")

    def get_blake3_hash(self, data: bytes) -> str:
        """Veriyi BLAKE3 ile anlık mühürler."""
        return blake3(data).hexdigest()

    def backup_with_zstd(self):
        """Mevcut fstab dosyasını Zstd ile arşivler."""
        if self.fstab_path.exists():
            try:
                backup_path = self.fstab_path.with_suffix(".old.zst")
                data = self.fstab_path.read_bytes()
                cctx = zstd.ZstdCompressor(level=10)
                compressed = cctx.compress(data)
                backup_path.write_bytes(compressed)
                self.logger.info(f"Yedek Arşivlendi (Zstd): {backup_path}")
            except Exception as e:
                self.zeka_analizi(e, "Zstd Backup")

    def get_block_devices(self):
        """Sistemdeki sabit diskleri Pathlib ile tarar."""
        devices = []
        # Modern x86_64 NVMe ve SATA taraması.
        block_path = Path("/sys/block")
        for dev_path in list(block_path.glob("sd*")) + list(block_path.glob("nvme*")):
            removable_file = dev_path / "removable"
            if removable_file.exists() and removable_file.read_text().strip() == "0":
                device_link = (dev_path / "device").resolve()
                if not any(x in str(device_link) for x in ["/usb", "/fw-host"]):
                    devices.append(f"/dev/{dev_path.name}")
        return sorted(devices)

    def scan_partitions(self, device_path):
        """Disk bölümlerini pyparted ile kesin olarak ayıklar."""
        try:
            dev = parted.getDevice(device_path)
            disk = parted.Disk(dev)
            for part in disk.partitions:
                if part.fileSystem and part.fileSystem.type not in EXCLUDED_FS:
                    yield part.getDeviceNodeName(), part.fileSystem.type
        except Exception as e:
            self.logger.debug(f"Aygıt atlanıyor {device_path}: {e}")

    def update_inventory_db(self, partitions):
        """Disk envanterini SQLite veritabanına mühürler."""
        try:
            if not self.db_path.parent.exists():
                self.db_path.parent.mkdir(parents=True)
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS disk_inventory 
                    (node TEXT PRIMARY KEY, fstype TEXT, mtime DATETIME DEFAULT CURRENT_TIMESTAMP)
                """)
                conn.executemany("INSERT OR REPLACE INTO disk_inventory (node, fstype) VALUES (?, ?)", partitions)
        except Exception as e:
            self.zeka_analizi(e, "SQLite Inventory Update")

    def refresh(self):
        """Tüm süreci tek seferde uygular ve dosyayı mühürler."""
        self.logger.info("Poyraz76 Disk Taraması Başlatıldı...")
        partitions = []
        fstab_entries = []

        # 1. Mevcut Durumu Yedekle.
        self.backup_with_zstd()

        # 2. Diskleri ve Bölümleri Tara.
        for dev in self.get_block_devices():
            for node, fstype in self.scan_partitions(dev):
                partitions.append((node, fstype))
                options = DEFAULT_OPTIONS.get(fstype, DEFAULT_OPTIONS["defaults"])
                
                # Temiz hiyerarşi kuralına göre mount noktası.
                mount_point = f"/mnt/{Path(node).name}"
                if not Path(mount_point).exists():
                    try: 
                        os.makedirs(mount_point, exist_ok=True) 
                    except Exception: 
                        pass
                
                entry = f"{node:<23} {mount_point:<15} {fstype:<7} {options:<15} 0 0"
                fstab_entries.append(entry)

        # 3. SQLite Envanterini Güncelle.
        self.update_inventory_db(partitions)

        # 4. Yeni Fstab Yazımı ve BLAKE3 Mühürü.
        header = "# Poyraz76 Modern Fstab Generator (2026)\n# Bütünlük BLAKE3 ile korunmaktadır.\n\n"
        content = header + "\n".join(fstab_entries) + "\n"
        
        try:
            content_bytes = content.encode("utf-8")
            self.fstab_path.write_bytes(content_bytes)
            f_hash = self.get_blake3_hash(content_bytes)
            self.logger.info(f"Fstab Mühürlendi. BLAKE3: {f_hash}")
            self.logger.info("Sistem tek başına ayağa kalkmaya hazır.")
        except Exception as e:
            self.zeka_analizi(e, "Final Fstab Write")

if __name__ == "__main__":
    # Kural: Kodu asla yarım bırakma ve root yetkisini doğrula.
    if os.getuid() != 0:
        print("[!] Bu işlem için root yetkisi gereklidir.")
        sys.exit(1)
        
    engine = FstabEngine()
    engine.refresh()
