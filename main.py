import os
import threading
import requests
from flask import Flask
import telebot
from telebot import types

TOKEN = os.environ.get('TELEGRAM_TOKEN')
bot = telebot.TeleBot(TOKEN)

CANAL_USERNAME = "@baixatudo1921"

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot de Downloads rodando!"

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
        return True

def enviar_mensagem_inscricao(chat_id):
    markup = types.InlineKeyboardMarkup()
    btn_canal = types.InlineKeyboardButton("📢 Entrar no Canal", url=f"https://t.me/{CANAL_USERNAME.replace('@', '')}")
    markup.add(btn_canal)
    
    bot.send_message(
        chat_id,
        f"⚠️ **Acesso Restrito!**\n\n"
        f"Para utilizar o bot, inscreva-se no nosso canal oficial:\n\n"
        f"👉 **{CANAL_USERNAME}**",
        reply_markup=markup,
        parse_mode="Markdown"
    )

def baixar_tiktok_api(url):
    api_url = f"https://www.tikwm.com/api/?url={url}"
    response = requests.get(api_url, timeout=10).json()
    if response.get("code") == 0:
        return response["data"]["play"]
    return None

def baixar_cobalt_api(url):
    api_url = "https://api.cobalt.tools/api/json"
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    payload = {"url": url}
    response = requests.post(api_url, json=payload, headers=headers, timeout=15).json()
    if "url" in response:
        return response["url"]
    return None

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    if not usuario_inscrito(message.from_user.id):
        enviar_mensagem_inscricao(message.chat.id)
        return

    bot.reply_to(message, "Envie o link de um vídeo do TikTok, Instagram ou YouTube para baixar!")

@bot.message_handler(func=lambda message: True)
def process_link(message):
    user_id = message.from_user.id
    
    if not usuario_inscrito(user_id):
        enviar_mensagem_inscricao(message.chat.id)
        return

    url = message.text.strip()
    
    if not (url.startswith("http://") or url.startswith("https://")):
        bot.reply_to(message, "Por favor, envie um link válido.")
        return

    msg_status = bot.reply_to(message, "⏳ Baixando o vídeo, aguarde...")

    video_url = None

    try:
        # Se for TikTok, usa a API dedicada do TikWm
        if "tiktok.com" in url:
            video_url = baixar_tiktok_api(url)
        
        # Para Instagram / YouTube ou fallback do TikTok
        if not video_url:
            video_url = baixar_cobalt_api(url)

        if video_url:
            # Envia o vídeo direto a partir da URL gerada pela API
            bot.send_video(
                message.chat.id, 
                video_url, 
                caption="✅ Vídeo baixado com sucesso pelo @baixatudo1921_bot!"
            )
            bot.delete_message(message.chat.id, msg_status.message_id)
        else:
            raise Exception("Não foi possível extrair a URL do vídeo pelas APIs.")

    except Exception as e:
        print(f"Erro no processamento: {e}")
        bot.edit_message_text(
            "❌ Não foi possível baixar este vídeo. Tente outro link ou tente novamente em alguns instantes.",
            chat_id=message.chat.id,
            message_id=msg_status.message_id
        )

if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    print("Bot rodando...")
    bot.infinity_polling()
