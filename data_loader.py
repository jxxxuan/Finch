import os
import json
import pandas as pd
from typing import Optional, Union, Dict, Any, Tuple
from database import create_conn
from database.symbol import get_by_symbol
from constants import FILE_DIRS

class FinchDataLoader:
    """
    Finch 项目数据加载类，用于为量化分析人员提供统一的数据加载接口。
    支持加载日K历史、分钟K历史、财务报表数据、公司基本资料及描述。
    """
    def __init__(self):
        pass

    def load_history(self, symbol: str) -> pd.DataFrame:
        """
        加载指定股票的日K历史价格数据 (Parquet)
        
        :param symbol: 股票代码，例如 'AAPL'
        :return: 包含日K线数据的 Pandas DataFrame
        """
        symbol = symbol.upper()
        first_letter = symbol[0]
        file_path = os.path.join(FILE_DIRS['history'], first_letter, f"{symbol}.parquet")
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"日K历史数据不存在: {file_path}")
        return pd.read_parquet(file_path, engine='fastparquet')

    def load_minute_history(self, symbol: str) -> pd.DataFrame:
        """
        加载指定股票的分钟级历史价格数据 (Parquet)
        
        :param symbol: 股票代码，例如 'AAPL'
        :return: 包含分钟K线数据的 Pandas DataFrame
        """
        symbol = symbol.upper()
        first_letter = symbol[0]
        file_path = os.path.join(FILE_DIRS['minute_history'], first_letter, f"{symbol}.parquet")
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"分钟K历史数据不存在: {file_path}")
        return pd.read_parquet(file_path, engine='fastparquet')

    def load_financials(self, symbol: str, statement_type: str = 'balance_sheet') -> pd.DataFrame:
        """
        加载股票财务报表数据 (Parquet)
        
        :param symbol: 股票代码，例如 'AAPL'
        :param statement_type: 报表类型，支持: 'balance_sheet', 'cash_flow', 'income_stmt'
        :return: 财务报表的 Pandas DataFrame
        """
        symbol = symbol.upper()
        statement_type = statement_type.lower()
        valid_types = ['balance_sheet', 'cash_flow', 'income_stmt']
        if statement_type not in valid_types:
            raise ValueError(f"无效的财务报表类型，必须是 {valid_types} 之一")

        first_letter = symbol[0]
        file_path = os.path.join(FILE_DIRS[statement_type], first_letter, f"{symbol}.parquet")
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"财务报表数据不存在: {file_path}")
        return pd.read_parquet(file_path, engine='fastparquet')

    def _find_latest_info_file(self, symbol: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        自动在 info 目录下寻找指定股票最新月份对应的 JSON 路径
        """
        base_info_dir = FILE_DIRS.get('info')
        if not base_info_dir or not os.path.exists(base_info_dir):
            return None, None, None
        
        symbol = symbol.upper()
        first_letter = symbol[0]
        
        # 扫描并以降序排序年份目录 (如 ['2026', '2025'])
        years = sorted([y for y in os.listdir(base_info_dir) if y.isdigit()], reverse=True)
        for year in years:
            year_dir = os.path.join(base_info_dir, year)
            # 扫描并以降序排序月份目录 (如 ['06', '05'])
            months = sorted([m for m in os.listdir(year_dir) if m.isdigit()], reverse=True)
            for month in months:
                file_path = os.path.join(year_dir, month, first_letter, f"{symbol}.json")
                if os.path.exists(file_path):
                    return file_path, year, month
        return None, None, None

    def load_info(self, symbol: str, year: Optional[Union[str, int]] = None, month: Optional[Union[str, int]] = None) -> Dict[str, Any]:
        """
        读取指定的 info JSON 数据。
        如果不指定 year 或 month，将自动加载最新月份的数据。
        
        :param symbol: 股票代码，例如 'AAPL'
        :param year: 年份，如 2026
        :param month: 月份，如 6 或 '06'
        :return: 包含公司全部信息字典
        """
        symbol = symbol.upper()
        first_letter = symbol[0]
        
        if year is not None and month is not None:
            year_str = str(year)
            month_str = str(month).zfill(2)
            file_path = os.path.join(FILE_DIRS['info'], year_str, month_str, first_letter, f"{symbol}.json")
        else:
            file_path, year_found, month_found = self._find_latest_info_file(symbol)
            if not file_path:
                raise FileNotFoundError(f"未找到股票 {symbol} 的最新 info 数据")
                
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"info 数据文件不存在: {file_path}")
            
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def get_description(self, symbol: str) -> str:
        """
        获取股票对应的公司详细业务描述 (longBusinessSummary)
        
        :param symbol: 股票代码
        :return: 公司详细英文介绍
        """
        try:
            info = self.load_info(symbol)
            return info.get("longBusinessSummary", "暂无公司详情介绍。")
        except FileNotFoundError:
            return f"未找到该股票 {symbol} 的公司描述。"

    def get_stock_profile(self, symbol: str) -> Optional[pd.Series]:
        """
        从数据库的 symbol 表获取股票基础维度资料（如名称、板块、行业、国家、交易所、退市状态等）
        
        :param symbol: 股票代码
        :return: 包含基础信息的 Pandas Series
        """
        symbol = symbol.upper()
        conn = create_conn()
        try:
            cols = ['name', 'sector', 'industry', 'country', 'exchange', 'asset_type', 'delisted']
            profile = get_by_symbol(conn, symbol, cols=cols)
            return profile
        except Exception as e:
            print(f"从数据库获取 {symbol} 基本资料失败: {e}")
            return None
        finally:
            conn.close()
