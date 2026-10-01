import os
import threading
from flask import Flask
import telebot
from telebot import types
import yt_dlp

TOKEN = os.environ.get('TELEGRAM_TOKEN')
bot = telebot.TeleBot(TOKEN)

CANAL_USERNAME = "@baixatudo1921"

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot de Downloads do Telegram rodando perfeitamente!"

def run_flask():
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)

def usuario_inscrito(user_id):
    try:
        membro = bot.get_chat_member(CANAL_USERNAME, user_id)
        if membro.status in ['creator', 'administrator', 'member']:
            return True
        return False
    except Exception as e:
        print(f"Erro ao verificar membro: {e}")
        return False

def enviar_mensagem_inscricao(chat_id):
    markup = types.InlineKeyboardMarkup()
    btn_canal = types.InlineKeyboardButton("📢 Entrar no Canal", url=f"https://t.me/{CANAL_USERNAME.replace('@', '')}")
    markup.add(btn_canal)
    
    bot.send_message(
        chat_id,
        f"⚠️ **Acesso Restrito!**\n\n"
        f"Para utilizar o bot e baixar vídeos gratuitamente, você precisa estar inscrito no nosso canal oficial:\n\n"
        f"👉 **{CANAL_USERNAME}**\n\n"
        f"Após entrar no canal, tente enviar o link do vídeo novamente!",
        reply_markup=markup,
        parse_mode="Markdown"
    )

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    if not usuario_inscrito(message.from_user.id):
        enviar_mensagem_inscricao(message.chat.id)
        return

    bot.reply_to(
        message, 
        "Olá! Envie um link do **Instagram**, **TikTok** ou **YouTube** para eu baixar o vídeo para você!"
    )

@bot.message_handler(func=lambda message: True)
def process_link(message):
    user_id = message.from_user.id
    
    if not usuario_inscrito(user_id):
        enviar_mensagem_inscricao(message.chat.id)
        return

    url = message.text.strip()
    
    if not (url.startswith("http://") or url.startswith("https://")):
        bot.reply_to(message, "Por favor, envie um link válido de um vídeo.")
        return

    msg_status = bot.reply_to(message, "⏳ Processando o vídeo, aguarde um momento...")

    try:
        ydl_opts = {
            'format': 'b[filesize<50M]/best[filesize<50M]/best',
            'outtmpl': '/tmp/%(id)s.%(ext)s',
            'quiet': True,
            'no_warnings': True,
            'max_filesize': 50 * 1024 * 1024,
            'nocheckcertificate': True,
            'ignoreerrors': False,
            'logtostderr': False,
            'geo_bypass': True,
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
            }
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        with open(filename, 'rb') as video_file:
            bot.send_video(message.chat.id, video_file, caption="✅ Vídeo baixado com sucesso pelo @baixatudo1921_bot!")

        if os.path.exists(filename):
            os.remove(filename)

        bot.delete_message(message.chat.id, msg_status.message_id)

    except Exception as e:
        print(f"Erro detalhado no download: {e}")
        bot.edit_message_text(
            f"❌ Não foi possível baixar este vídeo.\n\nMotivo: O link pode ser privado, expirado ou exceder o limite de 50MB do Telegram.",
            chat_id=message.chat.id,
            message_id=msg_status.message_id
        )

if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    print("Bot rodando...")
    bot.infinity_polling()
