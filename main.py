import os
from threading import Thread
from flask import Flask
import telebot
from yt_dlp import YoutubeDL

# 1. Servidor Web (Flask) para manter o Render ativo
app = Flask('')

@app.route('/')
def home():
    return "Bot de Downloads a funcionar!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_flask)
    t.start()

# 2. Inicialização do Bot do Telegram
TOKEN = os.environ.get("TELEGRAM_TOKEN")

if not TOKEN:
    print("ERRO: TELEGRAM_TOKEN não configurado nas variáveis de ambiente.")
else:
    bot = telebot.TeleBot(TOKEN)

    @bot.message_handler(commands=['start', 'help'])
    def send_welcome(message):
        bot.reply_to(
            message, 
            "👋 Olá! Envia o link de um vídeo (Instagram, TikTok, YouTube) para eu fazer o download."
        )

    @bot.message_handler(func=lambda message: True)
    def download_video(message):
        url = message.text.strip()

        if not url.startswith("http"):
            bot.reply_to(message, "⚠️ Envia um link válido (começado por http ou https).")
            return

        msg_espera = bot.reply_to(message, "⏳ A processar o vídeo, aguarda um momento...")

        ydl_opts = {
            'format': 'best',
            'outtmpl': 'video_%(id)s.%(ext)s',
            'quiet': True,
            'no_warnings': True,
        }

        try:
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                
                if info is None:
                    bot.edit_message_text("❌ Não foi possível extrair informação deste link.", chat_id=message.chat.id, message_id=msg_espera.message_id)
                    return

                filename = ydl.prepare_filename(info)

            with open(filename, 'rb') as video_file:
                bot.send_video(message.chat.id, video_file)

            bot.delete_message(chat_id=message.chat.id, message_id=msg_espera.message_id)
            if os.path.exists(filename):
                os.remove(filename)

        except Exception as e:
            print(f"Erro ao transferir vídeo: {e}")
            bot.edit_message_text("❌ Ocorreu um erro ao tentar transferir este vídeo.", chat_id=message.chat.id, message_id=msg_espera.message_id)

    keep_alive()
    print("Bot do Telegram iniciado...")
    bot.infinity_polling()
