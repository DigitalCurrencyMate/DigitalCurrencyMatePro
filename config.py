import os
from dotenv import load_dotenv

# 加载 .env 文件中的环境变量
load_dotenv()

class Config:
    # Telegram 配置
    TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
    ADMIN_USER_ID = int(os.getenv('ADMIN_USER_ID', 0))
    DEBUG_MODE = os.getenv('DEBUG_MODE', 'false').lower() == 'true'

    # 支持的币种 (用于 /list 命令)
    SUPPORTED_COINS = {
        'BTC': '比特币', 'ETH': '以太坊', 'BNB': '币安币', 'SOL': 'Solana',
        'XRP': '瑞波币', 'ADA': '卡尔达诺', 'DOGE': '狗狗币', 'MATIC': 'Polygon', 'LINK': 'Chainlink'
    }

    # 性能与限制配置 (保护 MateBook)
    MAX_CONCURRENT_REQUESTS = 3
    REQUEST_TIMEOUT = 10000  # 毫秒
    ALERT_CHECK_INTERVAL = 60  # 秒

# 启动时打印配置信息（如果开启调试）
if Config.DEBUG_MODE:
    print("--- CryptoMatePro 配置信息 ---")
    print(f"Admin User ID: {Config.ADMIN_USER_ID}")
    print(f"Debug Mode: {Config.DEBUG_MODE}")
    print("-----------------------------")
