import os, threading
import telebot, yt_dlp
from flask import Flask

TOKEN = os.environ.get("TOKEN")
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot online 24h!"

@bot.message_handler(commands=['start'])
def start(m):
    bot.reply_to(m, "Fala! Manda link do TikTok, Insta, Face ou YouTube que eu baixo sem marca d'agua.")

@bot.message_handler(func=lambda m: True)
def baixar(m):
    url = m.text
    if "http" not in url:
        return
    msg = bot.reply_to(m, "⏳ Baixando...")
    try:
        opts = {'outtmpl': 'video.%(ext)s', 'format': 'mp4', 'quiet': True, 'noplaylist': True}
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
        with open(filename, 'rb') as f:
            bot.send_video(m.chat.id, f, caption="Pronto! ✅ @baixatudo1921_bot")
        os.remove(filename)
        bot.delete_message(m.chat.id, msg.message_id)
    except Exception as e:
        bot.reply_to(m, f"Erro nesse link: {e}")

def run_bot():
    bot.infinity_polling()

threading.Thread(target=run_bot).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
