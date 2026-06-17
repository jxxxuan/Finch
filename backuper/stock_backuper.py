import tarfile
import os
import time
from constants import BACKUP_PATH, LOCAL_DRIVE_PATH
from backuper.backup_main import manually_run_backup
from datetime import datetime
from pathlib import Path

def backup(type, num_worker, **kwargs):
    """
    处理特定类型数据的增量差异备份逻辑 (Option C: Daily Diff Archiving)
    只备份自上次备份以来被修改或新增的文件。
    """
    start_time = time.time()
    now = datetime.now()
    year = now.strftime('%Y')
    month = now.strftime('%m')
    day = now.strftime('%d')

    parent_folder = Path(LOCAL_DRIVE_PATH) / type
    if not parent_folder.exists():
        print(f"源路径不存在，跳过: {parent_folder}")
        return

    # 1. 获取上次备份的时间戳
    timestamp_file = Path(BACKUP_PATH) / f"last_backup_{type}.txt"
    last_backup_time = 0.0
    if timestamp_file.exists():
        try:
            with open(timestamp_file, 'r', encoding='utf-8') as f:
                last_backup_time = float(f.read().strip())
        except Exception as e:
            print(f"读取上次备份时间戳失败，将执行全量备份: {e}")

    # 2. 递归扫描，收集新增或修改过的文件
    modified_files = []
    for root, dirs, files in os.walk(parent_folder):
        for file in files:
            file_path = Path(root) / file
            try:
                mtime = file_path.stat().st_mtime
                if mtime > last_backup_time:
                    modified_files.append(file_path)
            except Exception as e:
                print(f"读取文件属性失败 {file_path}: {e}")

    # 3. 如果没有文件修改，则直接跳过备份
    if not modified_files:
        print(f"📊 '{type}' 没有新增或修改的文件，跳过备份。")
        return

    print(f"📦 '{type}' 发现 {len(modified_files)} 个新增/修改的文件，开始压缩备份...")

    # 4. 创建目标目录并压缩打包
    target_base_dir = Path(BACKUP_PATH) / year / month / day / type
    target_base_dir.mkdir(parents=True, exist_ok=True)
    target_file = target_base_dir / "diff_backup.tar.gz"

    try:
        with tarfile.open(target_file, "w:gz") as tar:
            for file_path in modified_files:
                # 保持相对于 LOCAL_DRIVE_PATH 的结构，例如: history/A/AAPL.parquet
                relative_path = file_path.relative_to(LOCAL_DRIVE_PATH)
                tar.add(file_path, arcname=relative_path)
        
        # 5. 备份成功后，更新时间戳文件
        Path(BACKUP_PATH).mkdir(parents=True, exist_ok=True)
        with open(timestamp_file, 'w', encoding='utf-8') as f:
            f.write(str(start_time))
        print(f"✅ '{type}' 增量差异备份成功: {target_file}")
    except Exception as e:
        print(f"❌ '{type}' 打包备份失败: {e}")
        # 如果打包失败，删除可能生成的不完整压缩包
        if target_file.exists():
            try:
                target_file.unlink()
            except:
                pass

def clear_backup():
    pass

if __name__ == '__main__':
    manually_run_backup(backup, '*')