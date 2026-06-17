from constants import UPDATE_INTERVAL, UPDATE_FREQUENCY
from database.symbol_metadata import get_by_rule, update_symbols_by_symbols
import pandas as pd
import numpy as np
from datetime import timedelta
from processor.process_main import manually_run_process
from utils import safe_type_input

def update_by_interval(db_pool, type):
    try:
        if type == '*':
            types = UPDATE_INTERVAL.keys()
        elif type == 'INTV':
            types = [k for k in UPDATE_INTERVAL.keys() if k != 'news']
        elif type in UPDATE_INTERVAL:
            types = [type]
        else:
            raise ValueError("Invalid type")

        conn = db_pool.getconn()
        for current_type in types:
            base_interval = UPDATE_INTERVAL[current_type]
            
            interval_str = (
                f"{base_interval.years} years" if base_interval.years else ""
            ) + (
                f"{base_interval.months} months" if base_interval.months else ""
            ) + (
                f"{base_interval.days} days" if base_interval.days else ""
            )

            print(f"\n🛠️ processing type: {current_type} (updater interval: {interval_str or 'customize'})")

            type_last_update = f"""{current_type}_last_update"""
            type_next_update = f"""{current_type}_next_update"""

            #"{last_update} < {next_update} OR ({next_update} IS NOT NULL AND {last_update} IS NULL)"
            sql = f"""
                NOT delisted AND (
                    NOT ready for update OR {type_next_update} IS NULL
                )
            """
            df = get_by_rule(conn, current_type, sql, cols=['symbol', type_last_update, type_next_update], limit=999999)
            # 查询需要更新的记录
            
            if df.empty:
                print("   ⚠️ no record need to update")
                continue
                
            print(f"   📊 found {len(df)} records need to update")
            
            df[type_last_update] = pd.to_datetime(df[type_last_update])
            now = pd.Timestamp.now()

            existed_df = df[df[type_last_update].notna()]
            if not existed_df.empty:
                # 对剩下的才去算均匀分布
                # 计算最晚允许更新时间
                deadline = existed_df[type_last_update].min() + base_interval
                total_days = max((deadline - now).days, 0)

                # 严格均匀分布
                existed_df = existed_df.sort_values(by=type_last_update)
                existed_df["delay_days"] = np.floor(
                    np.linspace(0, total_days+0.01, len(existed_df))
                ).astype(int)

                existed_df[type_next_update] = pd.to_datetime(existed_df["delay_days"].apply(
                    lambda days: now + timedelta(days=days)
                ))

            new_df = df[df[type_last_update].isna()]
            if not new_df.empty:
                new_df.loc[:,type_next_update] = pd.Timestamp.now()
                new_df.loc[:,'delay_days'] = 0

                df = pd.concat([existed_df,new_df])
            else:
                df = existed_df
            df['delay_days'] = df['delay_days'].astype(int)
            df[type_next_update] = pd.to_datetime(df[type_next_update])
            # 更新数据库
            update_symbols_by_symbols(conn,type_next_update,df)
            
            '''print(df)
            plt.figure(figsize=(10, 5))
            plt.hist(df["delay_days"], bins=range(df["delay_days"].min(), df["delay_days"].max() + 1), color='skyblue', edgecolor='black')
            plt.title(f"{current_type} - delay_days 分布图")
            plt.xlabel("延迟天数")
            plt.ylabel("记录数")
            plt.grid(True)
            plt.show()'''
            
            # 打印统计信息
            stats = {
                "earliest update": df[type_next_update].min().strftime("%Y-%m-%d"),
                "latest update": df[type_next_update].max().strftime("%Y-%m-%d"),
                "average delay days": f"{df['delay_days'].mean():.1f}",
            }
            
            print("   ✅ done")
            for k, v in stats.items():
                print(f"   - {k}: {v}")
                
            # 检查紧急记录
            df["days_left"] = (df[type_next_update] - now).dt.days
            urgent = df[df["days_left"] < 2]  # 剩余时间不足3天的
            if not urgent.empty:
                print(f"   ⚠️ attention: {len(urgent)} records need to update within 2 days")
                
    except Exception as e:
        print(f"❌ Error when update {current_type}: {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        db_pool.putconn(conn)

def update_by_frequency(db_pool, type):
    try:
        if type == '*':
            types = UPDATE_FREQUENCY.keys()
        elif type == 'FREQ':
            types = ['news', 'minute_history']
        elif type in UPDATE_FREQUENCY:
            types = [type]
        else:
            raise ValueError("Invalid type")
        pass

        conn = db_pool.getconn()
        for current_type in types:
            frequency = UPDATE_FREQUENCY[current_type]

            print(f"\n🛠️ processing type: {current_type} (updater frequency: {frequency or 'customize'})")

            type_next_update = f"""{current_type}_next_update"""

            sql = f"""
                (NOT delisted AND minute_history_frequency > {frequency}) OR {type_next_update} IS NULL 
            """
            df = get_by_rule(conn, current_type, sql, cols=['symbol', type_next_update, 'minute_history_frequency'], limit=999999)
            # 查询需要更新的记录
            
            if df.empty:
                print("   ⚠️ no record need to update")
                continue
                
            print(f"   📊 found {len(df)} records need to update")
            
            df.loc[:,type_next_update] = pd.Timestamp.now()
            print(df)

            # 更新数据库
            update_symbols_by_symbols(conn, type_next_update, df)
            
            print("   ✅ done")
            print(f"   ⚠️ attention: {len(df)} records need to update within 2 days")
                
    except Exception as e:
        print(f"❌ Error when update {current_type}: {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        db_pool.putconn(conn)

if __name__ == '__main__':
    type = safe_type_input("Type to update",'*')
    manually_run_process(update_by_interval, type)