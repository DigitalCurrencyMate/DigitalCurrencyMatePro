#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CryptoMatePro - 数字货币AI分析机器人 (Windows 64位完整版)
"""

import logging
import os
import json
import asyncio
from datetime import datetime, time
import pytz
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, ContextTypes, JobQueue
)
import ccxt
from config import Config
from sentiment import fetch_reddit_sentiment # 导入情绪分析模块

# --- 日志配置 ---
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO if not Config.DEBUG_MODE else logging.DEBUG,
    handlers=[
        logging.FileHandler('bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# --- 全局变量 ---
user_alerts = {}  # 存储用户提醒 {user_id: [{symbol, price, active}]}
ALERTS_FILE = 'alerts.json'

# --- 数据持久化 ---
def load_alerts():
    global user_alerts
    if os.path.exists(ALERTS_FILE):
        try:
            with open(ALERTS_FILE, 'r', encoding='utf-8') as f:
                user_alerts = json.load(f)
            logger.info(f"✅ 从 {ALERTS_FILE} 加载了 {len(user_alerts)} 个用户的提醒。")
        except Exception as e:
            logger.error(f"❌ 加载提醒文件失败: {e}")
            user_alerts = {}

def save_alerts():
    try:
        with open(ALERTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(user_alerts, f, ensure_ascii=False, indent=2)
        # logger.debug("💾 提醒数据已保存。")
    except Exception as e:
        logger.error(f"❌ 保存提醒文件失败: {e}")

# --- 核心功能：价格获取 ---
def get_crypto_price(symbol: str):
    """获取单个币种价格"""
    try:
        exchange = ccxt.binance({'timeout': Config.REQUEST_TIMEOUT, 'enableRateLimit': True})
        ticker = exchange.fetch_ticker(symbol)
        return {
            'success': True, 'symbol': symbol, 'price': ticker['last'],
            'change': ticker['percentage'], 'time': datetime.now().strftime('%H:%M:%S')
        }
    except Exception as e:
        logger.error(f"获取价格失败 {symbol}: {e}")
        return {'success': False, 'error': str(e)}

async def get_multiple_prices(symbols: list):
    """并发获取多个币种价格"""
    results = []
    for symbol in symbols:
        # 简单并发控制，避免请求过快
        await asyncio.sleep(0.2)
        price_data = get_crypto_price(symbol)
        if price_data['success']:
            results.append(price_data)
    return results

# --- Telegram 命令处理器 ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    welcome_text = (
        f"🎉 欢迎使用 CryptoMateProBot, {user.first_name}!\n\n"
        "我是您的AI数字货币助手，提供价格查询、智能提醒和市场情绪分析。\n\n"
        "📋 可用命令:\n"
        "/price - 查看主流币价格\n"
        "/price BTC - 查看特定币种价格\n"
        "/alert BTC 50000 - 设置价格提醒\n"
        "/myalerts - 查看我的提醒\n"
        "/sentiment - 获取AI市场情绪分析\n"
        "/list - 查看支持的币种\n"
        "/help - 查看详细帮助"
    )
    keyboard = [[InlineKeyboardButton("📈 查看价格", callback_data='price_all'), InlineKeyboardButton("🔔 设置提醒", callback_data='set_alert')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(welcome_text, reply_markup=reply_markup)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = ("📖 帮助中心\n\n"
                 "1. 查询价格:\n"
                 "   /price 或 /price BTC\n\n"
                 "2. 设置提醒:\n"
                 "   /alert [币种] [价格] (例: /alert ETH 3000)\n\n"
                 "3. 查看提醒:\n"
                 "   /myalerts\n\n"
                 "4. AI情绪分析:\n"
                 "   /sentiment (获取Reddit社区情绪报告)\n\n"
                 "⚠️ 免责声明: 本机器人提供的信息不构成任何投资建议。")
    await update.message.reply_text(help_text)

async def list_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    coins_text = "💰 支持的币种:\n" + "\n".join([f"• {s} - {n}" for s, n in Config.SUPPORTED_COINS.items()])
    await update.message.reply_text(coins_text)

async def price_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    symbol_arg = context.args[0].upper() + '/USDT' if context.args else None
    loading_msg = await update.message.reply_text("⏳ 正在获取最新价格...")

    if symbol_arg:
        if symbol_arg.split('/')[0] not in Config.SUPPORTED_COINS:
            await loading_msg.edit_text(f"❌ 暂不支持该币种。使用 /list 查看支持的币种。")
            return
        price_data = get_crypto_price(symbol_arg)
    else:
        symbols = ['BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'SOL/USDT']
        price_data_list = await get_multiple_prices(symbols)
        if not price_data_list:
            await loading_msg.edit_text("❌ 获取价格失败，请稍后重试。")
            return
        price_data = price_data_list[0] # Use first item for single display logic below

    if price_data['success']:
        change_icon = "📈" if price_data['change'] >= 0 else "📉"
        change_color = "🟢" if price_data['change'] >= 0 else "🔴"
        text = (f"{change_color} {price_data['symbol']} 价格\n"
                f"💰 当前价格: ${price_data['price']:,.2f}\n"
                f"{change_icon} 24h涨跌: {price_data['change']:+.2f}%\n"
                f"⏰ 更新时间: {price_data['time']}")
        
        # 获取并显示情绪
        sentiment_result = fetch_reddit_sentiment(limit=5) # 快速获取一次情绪
        mood_icon = "😐"
        mood_text = "中性"
        if 'classification' in sentiment_result:
             if sentiment_result['classification'] == 'bullish': mood_icon, mood_text = "📈", "看涨"
             elif sentiment_result['classification'] == 'bearish': mood_icon, mood_text = "📉", "看跌"
        text += f"\n{mood_icon} 市场情绪: {mood_text}"

        await loading_msg.edit_text(text)
    else:
        await loading_msg.edit_text(f"❌ 获取价格失败: {price_data['error']}")

async def alert_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 2:
        await update.message.reply_text("❌ 格式错误！正确格式: /alert 币种 价格\n例如: /alert BTC 50000")
        return
    symbol, price_str = context.args[0].upper(), context.args[1]
    try:
        target_price = float(price_str)
    except ValueError:
        await update.message.reply_text("❌ 价格必须是有效的数字。")
        return

    if symbol not in Config.SUPPORTED_COINS:
        await update.message.reply_text(f"❌ 暂不支持 {symbol} 币种。使用 /list 查看支持的币种。")
        return

    user_id = str(update.effective_user.id)
    if user_id not in user_alerts:
        user_alerts[user_id] = []
    
    user_alerts[user_id].append({'symbol': symbol, 'price': target_price, 'active': True})
    save_alerts()
    await update.message.reply_text(f"✅ 提醒设置成功！当 {symbol} 价格到达 ${target_price:,.2f} 时，我会通知您。")

async def myalerts_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    alerts = user_alerts.get(user_id, [])
    if not alerts:
        await update.message.reply_text("📭 您还没有设置任何价格提醒。使用 /alert 命令来添加一个吧！")
        return
    response = "📋 您的价格提醒列表:\n" + "\n".join([f"{i+1}. {a['symbol']} -> ${a['price']:,.2f} {'✅' if a['active'] else '⏸️'}" for i, a in enumerate(alerts)])
    await update.message.reply_text(response)

async def sentiment_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 正在连接AI大脑，分析市场情绪中...")
    result = fetch_reddit_sentiment(limit=15)
    if 'error' in result:
        await update.message.reply_text(f"❌ 分析失败: {result['error']}")
        return
    emoji = "📈" if result['classification'] == 'bullish' else "📉" if result['classification'] == 'bearish' else "➡️"
    text = (f"{emoji} AI市场情绪分析报告\n\n"
            f"📊 整体趋势: {result['classification'].upper()}\n"
            f"📈 情绪指数: {result['score']}\n"
            f"🔍 分析样本: {result['total_posts']} 条热门帖\n"
            f"🕒 报告时间: {result['timestamp']}\n\n"
            "近期热点标题情绪:\n")
    for p in result['posts'][:5]:
        marker = "🟢" if p['score'] > 0 else "🔴" if p['score'] < 0 else "⚪"
        text += f"{marker} {p['title'][:50]}...\n"
    await update.message.reply_text(text)

# --- 定时任务 ---
async def check_alerts_job(context: ContextTypes.DEFAULT_TYPE):
    logger.info("开始检查价格提醒...")
    for user_id, alerts in list(user_alerts.items()):
        for alert in alerts:
            if alert['active']:
                symbol = f"{alert['symbol']}/USDT"
                price_data = get_crypto_price(symbol)
                if price_data['success']:
                    current_price = price_data['price']
                    target_price = alert['price']
                    if abs(current_price - target_price) / target_price <= 0.005: # 0.5% 容差
                        try:
                            await context.bot.send_message(chat_id=int(user_id), text=f"🔔 价格提醒!\n{alert['symbol']} 当前价格 ${current_price:,.2f}，已接近您的目标 ${target_price:,.2f}。")
                            alert['active'] = False # 触发后设为非活跃
                            logger.info(f"提醒触发: User {user_id}, {symbol} -> {target_price}")
                        except Exception as e:
                            logger.error(f"发送提醒给用户 {user_id} 失败: {e}")
    save_alerts()

async def daily_sentiment_report_job(context: ContextTypes.DEFAULT_TYPE):
    logger.info("开始发送每日情绪报告...")
    result = fetch_reddit_sentiment(limit=20)
    if 'error' in result or Config.ADMIN_USER_ID == 0:
        return
    emoji = "📈" if result['classification'] == 'bullish' else "📉" if result['classification'] == 'bearish' else "➡️"
    report = (f"🌞 每日AI市场情绪早报\n\n"
              f"{emoji} 整体趋势: {result['classification'].upper()}\n"
              f"📈 情绪指数: {result['score']}\n"
              f"🔍 分析样本: {result['total_posts']} 条\n"
              f"🕒 报告时间: {result['timestamp']}")
    try:
        await context.bot.send_message(chat_id=Config.ADMIN_USER_ID, text=report)
    except Exception as e:
        logger.error(f"发送每日报告失败: {e}")

# --- 按钮回调 ---
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == 'price_all':
        context.args = []
        await price_command(update, context)

# --- 错误处理 ---
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"更新 {update} 导致错误 {context.error}", exc_info=context.error)

# --- 主函数 ---
def main():
    load_alerts()
    if not Config.TELEGRAM_TOKEN or Config.TELEGRAM_TOKEN.startswith("你的机器人"):
        print("❌ 错误: 请在 .env 文件中设置正确的 TELEGRAM_TOKEN")
        return

    print("="*50)
    print("🤖 CryptoMateProBot 启动中...")
    print(f"💻 系统: Windows {os.environ['PROCESSOR_ARCHITECTURE']}")
    print(f"🐍 Python: {os.sys.version.split()[0]}")
    print("="*50)

    app = Application.builder().token(Config.TELEGRAM_TOKEN).build()

    # 命令处理器
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("price", price_command))
    app.add_handler(CommandHandler("alert", alert_command))
    app.add_handler(CommandHandler("myalerts", myalerts_command))
    app.add_handler(CommandHandler("sentiment", sentiment_command))
    app.add_handler(CommandHandler("list", list_command))
    # 按钮回调
    app.add_handler(CallbackQueryHandler(button_handler))
    # 错误处理器
    app.add_error_handler(error_handler)

    # 定时任务
    job_queue: JobQueue = app.job_queue
    job_queue.run_repeating(check_alerts_job, interval=Config.ALERT_CHECK_INTERVAL, first=10)
    
    # 每天北京时间早上9点发送报告
    beijing_tz = pytz.timezone('Asia/Shanghai')
    report_time = time(hour=9, minute=0, tzinfo=beijing_tz)
    job_queue.run_daily(daily_sentiment_report_job, report_time)

    print("✅ 机器人启动成功! 按 Ctrl+C 停止。")
    print("="*50)
    app.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True
    )

if __name__ == '__main__':
    main()
