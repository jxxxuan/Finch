import os
from constants import INTERVAL_OPTIONS, RULE_OPTIONS, FILE_DIRS, TEMP_FILE_DIRS, TYPE_OPTIONS, FIELD_OPTIONS
import socket
import logging
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()

SENDER_EMAIL = os.getenv("SENDER_EMAIL")
RECEIVER_EMAIL = os.getenv("RECEIVER_EMAIL")
SENDER_EMAIL_PASSWORD = os.getenv("SENDER_EMAIL_PASSWORD")

def init_logging(log_dir, log_id):
    safe_log_id = log_id.replace('*', 'all')
    os.makedirs(log_dir, exist_ok=True)
    log_filename = os.path.join(log_dir,safe_log_id)
    logging.basicConfig(
        filename=log_filename,
        level=logging.INFO,
        format="%(asctime)s - %(threadName)s - %(levelname)s - %(message)s",
    )
    return log_filename

def send_mail(subject,body):
    wait_until_online()
    sender_email = SENDER_EMAIL
    receiver_email = RECEIVER_EMAIL
    password = SENDER_EMAIL_PASSWORD

    # 创建邮件内容
    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = receiver_email
    message["Subject"] = subject

    # 邮件正文
    message.attach(MIMEText(body, "plain"))

    try:
        # 连接 Gmail SMTP
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()  # 启用加密
        server.login(sender_email, password)  # 登录
        server.send_message(message)  # 发送
        print("邮件发送成功！")
    except Exception as e:
        print(f"邮件发送失败: {e}")
    finally:
        server.quit()

def safe_int_input(prompt, default):
        try:
            value = input(f"{prompt} (default={default}): ")
            if value.strip() == "":
                return default
            return int(value)
        except ValueError:
            print("❌ 输入无效，使用默认值")
            return default
    
def safe_float_input(prompt, default):
        try:
            value = input(f"{prompt} (default={default}): ")
            if value.strip() == "":
                return default
            return float(value)
        except ValueError:
            print("❌ 输入无效，使用默认值")
            return default
        
def safe_interval_input(prompt, default):
    while True:
        value = input(f"{prompt} (options: {INTERVAL_OPTIONS}, default={default}): ").strip()
        if value == "":
            return default
        if value in INTERVAL_OPTIONS:
            return value
        print(f"❌ 无效的 interval: '{value}'，请输入 {INTERVAL_OPTIONS} 之一。")

def safe_rule_input(prompt, default):
    while True:
        value = input(f"{prompt} (options: {RULE_OPTIONS}, default={default}): ").strip()
        
        if value == "":
            return default
        return value

def safe_type_input(prompt, default):
    while True:
        value = input(f"{prompt} (options: {TYPE_OPTIONS}, default={default}): ").strip()

        if value == '':
            return default
        if value in TYPE_OPTIONS:
            return value
        print(f"❌ Invalid type: '{value}'，请输入 {TYPE_OPTIONS} 之一。")

def safe_field_input(prompt):
    while True:
        value = input(f"{prompt} (options: {FIELD_OPTIONS}): ").strip()

        if value in FIELD_OPTIONS:
            return value
        print(f"❌ 无效的 type: '{value}'，请输入 {FIELD_OPTIONS} 之一。")

def check_internet(host="8.8.8.8", port=53, timeout=3):
    """
    尝试连接 Google DNS 判断是否有网
    返回 True = 有网, False = 断网
    """
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return True
    except socket.error as ex:
        return False

def wait_until_online():
    while True:
        if not check_internet():
            time.sleep(60)
        else:
            break

def batch_iterable(iterable, batch_size):
    for i in range(0, len(iterable), batch_size):
        yield iterable[i:i + batch_size]

def write_parquet(data, name, type):
    temp_file_dir = os.path.join(TEMP_FILE_DIRS[type], name[0].upper())
    temp_file_path = os.path.join(file_dir, name + '.parquet')
    file_dir = os.path.join(FILE_DIRS[type], name[0].upper())
    file_path = os.path.join(file_dir, name + '.parquet')
    os.makedirs(temp_file_dir, exist_ok=True)
    data.to_parquet(temp_file_path, compression='zstd', engine='fastparquet')
    os.makedirs(file_dir, exist_ok=True)
    os.replace(temp_file_path,file_path)

if __name__ == '__main__':
    send_mail('test','test')