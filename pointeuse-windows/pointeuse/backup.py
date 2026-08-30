#!/usr/bin/env python3
"""Sauvegarde cohérente de la base, de la clé et des rapports PDF."""

from datetime import datetime
from pathlib import Path
import shutil
import sqlite3

root = Path(__file__).resolve().parent
source = root / "pointeuse.db"
backup_root = root / "sauvegardes"
stamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
target_dir = backup_root / stamp
target_dir.mkdir(parents=True, exist_ok=True)

if not source.exists():
    raise SystemExit("Aucune base pointeuse.db trouvée. Démarrez d'abord l'application.")

with sqlite3.connect(source) as src, sqlite3.connect(target_dir / "pointeuse.db") as dst:
    src.backup(dst)

secret = root / "pointeuse.secret"
if secret.exists():
    shutil.copy2(secret, target_dir / secret.name)

reports = root / "rapports"
if reports.exists():
    shutil.copytree(reports, target_dir / "rapports", dirs_exist_ok=True)

print(f"Sauvegarde créée : {target_dir}")
