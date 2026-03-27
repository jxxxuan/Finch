from constants import UPDATE_INTERVAL
from database.symbol_metadata import get_by_rule, update_symbols_by_symbols
import pandas as pd
import numpy as np
from datetime import timedelta
from processor.process_main import manually_run_process
from utils import safe_type_input

def next_update(db_pool, type):
    try:
        #temporary use UPDATE_INTERVAL
        if type == '*':
            types = UPDATE_INTERVAL.keys()
        elif type in UPDATE_INTERVAL:
            types = [type]
        else:
            raise ValueError("Invalid type")

        conn = db_pool.getconn()
        for current_type in types:
            print(f"\n🛠️ processing type: {current_type}")

            type_last_check = f"""{current_type}_last_check"""
            type_next_check = f"""{current_type}_next_check"""

            sql = f"""
                NOT delisted AND (
                    NOT ready for check OR {type_next_check} IS NULL
                )
            """
            df = get_by_rule(conn, current_type, sql, cols=['symbol', type_last_check, type_next_check], limit=999999)
            # 查询需要更新的记录
            
            if df.empty:
                print("   ⚠️ no record need to check")
                continue
                
            print(f"   📊 found {len(df)} records need to check")
            
            df[type_last_check] = pd.to_datetime(df[type_last_check])
            now = pd.Timestamp.now()

            existed_df = df[df[type_last_check].notna()]
            if not existed_df.empty:
                # 对剩下的才去算均匀分布
                # 计算最晚允许更新时间
                deadline = existed_df[type_last_check].min() + base_interval
                total_days = max((deadline - now).days, 0)

                # 严格均匀分布
                existed_df = existed_df.sort_values(by=type_last_check)
                existed_df["delay_days"] = np.floor(
                    np.linspace(0, total_days+0.01, len(existed_df))
                ).astype(int)

                existed_df[type_next_check] = pd.to_datetime(existed_df["delay_days"].apply(
                    lambda days: now + timedelta(days=days)
                ))

            new_df = df[df[type_last_check].isna()]
            if not new_df.empty:
                new_df.loc[:,type_next_check] = pd.Timestamp.now()
                new_df.loc[:,'delay_days'] = 0

                df = pd.concat([existed_df,new_df])
            else:
                df = existed_df
            df['delay_days'] = df['delay_days'].astype(int)
            # 更新数据库
            update_symbols_by_symbols(conn,type_next_check,df)
            
            print(df)
            '''plt.figure(figsize=(10, 5))
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

if __name__ == '__main__':
    type = safe_type_input("Type to update",'*')
    manually_run_process(next_update, type)