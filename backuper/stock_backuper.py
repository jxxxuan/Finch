import tarfile
import os
from constants import BACKUP_PATH, LOCAL_DRIVE_PATH
from backuper.backup_main import manually_run_backup
from datetime import datetime
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor,as_completed

def make_targz(source_dir, output_filename):
    # "w:gz" 表示写入并使用 gzip 压缩
    with tarfile.open(output_filename, "w:gz") as tar:
        # arcname=os.path.basename(source_dir) 确保压缩包内不包含绝对路径
        tar.add(source_dir, arcname=os.path.basename(source_dir))

def backup(type, **kwargs):
    now = datetime.now()
    year = now.strftime('%Y')
    month = now.strftime('%m')
    day = now.strftime('%d')
    """处理特定类型的备份逻辑"""
    parent_folder = Path(LOCAL_DRIVE_PATH) / type
    target_base_dir = Path(BACKUP_PATH) / year / month / day / type
    
    if not parent_folder.exists():
        print(f"源路径不存在，跳过: {parent_folder}")
        return

    # 创建目标目录
    target_base_dir.mkdir(parents=True, exist_ok=True)

    tasks = []
    # 这一步就是你说的“只处理 A to Z 文件夹”
    for item in os.listdir(parent_folder):
        source_path = parent_folder / item
        if source_path.is_dir():
            target_path = target_base_dir / f"{item}.tar.gz"
            tasks.append((source_path, target_path))

    if not tasks:
        # print(f"No subfolders found in {type}")
        return

    # 4. 开启并行处理
    # print(f"--- Starting parallel backup for '{type}' ({len(tasks)} folders) ---")
    
    # 根据你的 Y 盘带宽，建议 max_workers 设为 2-4
    with ProcessPoolExecutor(max_workers=4) as executor:
        # 使用 map 提交所有任务
        futures = [executor.submit(make_targz, src, dst) for src, dst in tasks]

        for f in as_completed(futures):
            try:
                f.result()
            except Exception as e:
                print(f"任务失败: {e}")

def clear_backup():
    pass

if __name__ == '__main__':
    manually_run_backup(backup,'*')