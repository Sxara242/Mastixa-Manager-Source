from pathlib import Path
import shutil

def create_backup(db_path: Path, backup_dir: Path):
    backup_dir.mkdir(parents=True, exist_ok=True)
    target = backup_dir / db_path.name
    shutil.copy2(db_path, target)
    return target
