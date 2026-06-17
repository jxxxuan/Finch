import os
import pandas as pd
from datetime import datetime
from pathlib import Path
from database import create_pandas_conn
from constants import BACKUP_PATH

def backup(type, num_worker, **kwargs):
    """
    处理特定类型数据的增量/备份逻辑 (物理数据库备份)
    将数据库中的表结构与数据备份为高压缩率的 Parquet 文件。
    """
    now = datetime.now()
    year = now.strftime('%Y')
    month = now.strftime('%m')
    day = now.strftime('%d')

    # 从 database 模块获取当前连接的数据库名
    from database import DB_NAME

    print(f"🗄️ 开始备份数据库 '{DB_NAME}' 的核心数据表...")

    # 目标备份根目录下的 database 子目录
    target_base_dir = Path(BACKUP_PATH) / year / month / day / "database"
    target_base_dir.mkdir(parents=True, exist_ok=True)

    # 普通表与带 schema 别名表定义
    tables = ['symbol', 'symbol_metadata', 'news']
    schemas_tables = [('monitor.task_status', 'monitor_task_status')]

    conn = create_pandas_conn()
    try:
        # 1. 备份普通表
        for table in tables:
            try:
                df = pd.read_sql(f'SELECT * FROM "{table}";', conn)
                output_file = target_base_dir / f"{table}.parquet"
                df.to_parquet(output_file, compression='zstd', engine='pyarrow')
                print(f"  - 数据表 '{table}' 备份成功 -> {output_file} ({len(df)} 行)")
            except Exception as e:
                print(f"  - 数据表 '{table}' 备份失败: {e}")

        # 2. 备份带 schema 的表 (例如 monitor.task_status)
        for full_name, file_name in schemas_tables:
            try:
                df = pd.read_sql(f'SELECT * FROM {full_name};', conn)
                output_file = target_base_dir / f"{file_name}.parquet"
                df.to_parquet(output_file, compression='zstd', engine='pyarrow')
                print(f"  - 数据表 '{full_name}' 备份成功 -> {output_file} ({len(df)} 行)")
            except Exception as e:
                print(f"  - 数据表 '{full_name}' 备份失败: {e}")

        print(f"✅ 数据库 '{DB_NAME}' 核心数据备份完成。")
    except Exception as e:
        print(f"❌ 数据库备份失败: {e}")
    finally:
        conn.close()
