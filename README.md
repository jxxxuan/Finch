# Finch Quantitative Stock Data System

Finch 是一个面向量化分析与机器学习的高性能、自托管美股数据采集与服务系统。该系统集成了美股历史价格数据（日K与分钟级）、公司基本资料、财务三张表、新闻及评级数据的自动化定时抓取，支持增量物理备份与分库隔离，并提供统一的本地数据载入器（SDK）和基于 FastAPI 的轻量级 HTTP RESTful API 数据接口，完美适配 Google Colab 及远程 GPU 训练集群。

---

## 📂 项目目录结构

```text
Finch/
├── api/                  # 数据服务 API 模块
│   ├── server.py         # 基于 FastAPI 的数据服务接口
│   └── README.md         # API 端点详细使用文档
├── spider/               # 自动化数据抓取爬虫模块
│   ├── update_main.py    # 爬虫多线程并行执行引擎
│   ├── daily_history_updater.py  # 日K线价格爬虫
│   ├── minute_history_updater.py # 分钟K线价格爬虫
│   ├── financial_statement_updater.py # 财务报表爬虫基类
│   ├── info_updater.py   # 公司基本信息爬虫（按月归档）
│   └── news_updater.py   # 财经新闻爬虫
├── database/             # 数据库层与 ORM
│   ├── __init__.py       # 数据库物理分库隔离路由
│   ├── symbol.py         # 证券基础表操作接口
│   └── symbol_metadata.py# 抓取调度元数据表操作接口
├── processor/            # 数据处理与定时任务调度逻辑
│   └── next_update_updater.py  # 动态计算与更新下一次抓取时间
├── backuper/             # 增量差异备份与归档模块
│   ├── stock_backuper.py # 文件层级每日增量差异打包备份 (Daily Diff)
│   └── database_backuper.py # 数据库表向 Parquet 文件的物理备份
├── constants.py          # 核心常量与爬虫更新周期配置
├── data_loader.py        # 统一本地数据加载器 SDK (FinchDataLoader)
├── main.py               # 项目定时调度主入口
├── requirements.txt      # 依赖包列表
└── README.md             # 本项目主文档
```

---

## ⚙️ 快速开始

### 1. 环境准备
项目建议使用 **Python 3.10+**。

克隆仓库并安装 Python 依赖项：
```bash
pip install -r requirements.txt
```

### 2. 配置环境变量
在项目根目录下创建一个 `.env` 配置文件（可参考 `.env.example`）：
```ini
# 路径配置
LOCAL_DRIVE_PATH=Z:\test   # 数据存储主目录
TEST_PATH=Z:\test          # 测试环境数据存储目录
BACKUP_PATH=G:\My Drive\stock\backup # 备份存储路径

# 数据库配置 (PostgreSQL)
DB_USERNAME=your_username
DB_PASSWORD=your_password
HOST=192.168.2.2
DB_NAME=predictor          # 生产库名称
DB_NAME_DEV=predictor_dev  # 开发库名称

# 环境隔离标记 (True: 生产环境; False: 开发环境)
PRODUCTION=False

# 邮件预警设置
SENDER_EMAIL=your_email@gmail.com
SENDER_EMAIL_PASSWORD=your_app_password
RECEIVER_EMAIL=receiver_email@gmail.com
```

---

## 🔒 物理分库与环境隔离

Finch 实现了极简的环境隔离，通过在 `.env` 中切换 `PRODUCTION` 标志：
- **`PRODUCTION=True`**：读写生产库 `predictor`，使用生产存储路径。
- **`PRODUCTION=False`**（默认开发模式）：读写开发库 `predictor_dev`，使用测试存储路径，避免对生产数据产生任何写污染。
数据库底层连接池（`database/__init__.py`）会自动根据该配置进行路由切换，业务代码中**无需硬编码任何 `_test` 表名或判断逻辑**。

---

## 🚀 核心组件运行指南

### 1. 数据爬虫主调度程序
执行以下命令启动完整的自动化数据更新流程。系统会自动根据数据库中各 Symbol 的 `next_update` 元数据，多线程增量抓取有更新需要的股票：
```bash
python main.py
```

### 2. 增量备份系统 (Delta Backup)
Finch 提供双重备份保障，并在 `main.py` 流程结束时自动触发：
*   **文件增量备份 (`backuper/stock_backuper.py`)**：系统利用 **Daily Diff Archiving** 机制，每天只打包当天被修改或写入的 Parquet 价格文件为 `.tar.gz` 压缩包，彻底防范备份空间无限膨胀，提高云同步效率。
*   **数据库物理备份 (`backuper/database_backuper.py`)**：纯 Python 实现，利用 `pyarrow` 引擎快速将 PostgreSQL 里的 `symbol`, `symbol_metadata`, `news` 等大表导出为高度压缩的 Parquet 文件并归档。

### 3. 数据 API 服务 (FastAPI)
如果您需要远程（例如在 Google Colab 里）免拷文件、高速获取最新的特征和价格，可以启动 API 服务：
```bash
python -m uvicorn api.server:app --host 0.0.0.0 --port 8000
```
> 💡 绑定 `0.0.0.0` 使得局域网内其他电脑或通过 Tailscale 映射的外部网络可以正常访问。详细端点设计请参考 [api/README.md](file:///c:/Users/User/Documents/GitHub/Finch/api/README.md)。

## 🐳 Docker 容器化部署 (推荐生产环境)

项目提供了针对 Linux 服务器（如 `xserver-01`）优化的 `Dockerfile` 与 `docker-compose.yml` 配置，采用 `host` 网络模式无缝连接宿主机的 PostgreSQL（`127.0.0.1:5432`）并直接挂载宿主机绝对路径，无需数据迁移。

### 1. 构建镜像
在根目录下执行以下命令构建 Finch 的 Docker 镜像：
```bash
docker compose build
```

### 2. 启动 API 常驻服务
以守护进程模式启动 API 数据端服务容器：
```bash
docker compose up -d api-server
```
启动后，容器内运行的 FastAPI 将通过宿主机网络在端口 `8000` 上提供数据查询服务，您可以使用 `curl http://127.0.0.1:8000/health` 检查健康状态。

### 3. 定时触发爬虫与备份任务
您可以通过 Docker Compose 容器以一次性运行（One-off）的形式，启动爬虫及归档备份流程：
```bash
docker compose run --rm spider-job
```
> 💡 **小贴士**：您可以将该命令写入 Linux 宿主机的 `crontab` 任务中，实现定时自动抓取，例如每天凌晨 1 点执行：
> `0 1 * * * cd /home/jxxxuan/Github/Finch && /usr/bin/docker compose run --rm spider-job >> /home/jxxxuan/cron_spider.log 2>&1`


## 📊 数据载入与量化分析 (SDK)

量化研究员或机器学习训练脚本可以直接使用 `FinchDataLoader`。该工具封装了底层的文件定位和数据库连接细节，提供一致且高效的数据接口：

```python
from data_loader import FinchDataLoader

loader = FinchDataLoader()

# 1. 瞬间载入股票日K历史价格 (DataFrame)
df_daily = loader.load_history("YELP")

# 2. 载入分钟K线历史价格
df_min = loader.load_minute_history("YELP")

# 3. 载入公司最新的月度基本资料 JSON (自动定位最新月份归档)
info = loader.load_info("AAPL")
summary = loader.get_description("AAPL") # 快速获取业务描述
```

---

## 🛠️ 测试与验证
您可以通过在项目根目录运行 `test.py` 或测试脚本来确保依赖和环境正常：
```bash
python test.py
```
或运行 API 服务连通性测试：
```bash
python -m unittest C:\Users\User\.gemini\antigravity\brain\f90c8b2a-61df-43c4-af94-4a36f6d49a02\scratch\test_api_server.py
```
