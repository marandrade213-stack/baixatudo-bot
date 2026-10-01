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
    return "Bot de Downloads Ativo!"

def run_flask():
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)

def usuario_inscrito(user_id):
    try:
        membro = bot.get_chat_member(CANAL_USERNAME, user_id)
        return membro.status in ['creator', 'administrator', 'member']
    except Exception as e:
        print(f"Erro na verificação de membro: {e}")
        return True

def enviar_mensagem_inscricao(chat_id):
    markup = types.InlineKeyboardMarkup()
    btn_canal = types.InlineKeyboardButton("📢 Entrar no Canal", url=f"https://t.me/{CANAL_USERNAME.replace('@', '')}")
    markup.add(btn_canal)
    
    bot.send_message(
        chat_id,
        f"⚠️ **Acesso Restrito!**\n\nInscreva-se no canal para usar o bot:\n👉 **{CANAL_USERNAME}**",
        reply_markup=markup,
        parse_mode="Markdown"
    )

def extrair_midia(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    # 1. TikTok (API TikWm)
    if "tiktok.com" in url:
        try:
            res = requests.get(f"https://www.tikwm.com/api/?url={url}", headers=headers, timeout=12).json()
            if res.get("code") == 0 and "play" in res.get("data", {}):
                return res["data"]["play"]
        except Exception as e:
            print(f"Erro TikTok: {e}")

    # 2. YouTube Shorts / Videos (API Piped / Invidious Proxy)
    if "youtube.com" in url or "youtu.be" in url:
        try:
            # Extrai o ID do vídeo
            video_id = url.split("shorts/")[-1].split("v=")[-1].split("?")[0].split("&")[0]
            api_res = requests.get(f"https://pipedapi.kavin.rocks/streams/{video_id}", headers=headers, timeout=12).json()
            
            # Pega a melhor stream de vídeo que já contém áudio
            for stream in api_res.get("videoStreams", []):
                if stream.get("videoOnly") is False and stream.get("container") == "mp4":
                    return stream.get("url")
            
            # Fallback para qualquer stream mp4 válida
            if api_res.get("videoStreams"):
                return api_res["videoStreams"][0]["url"]
        except Exception as e:
            print(f"Erro YouTube Piped: {e}")

    # 3. Instagram / Fallback Geral (API SaveFrom)
    try:
        res = requests.post(
            "https://worker.sf-tools.com/savefrom.php",
            data={"sf_url": url},
            headers=headers,
            timeout=12
        ).json()
        if res and len(res) > 0 and "url" in res[0]:
            return res[0]["url"][0]["url"]
    except Exception as e:
        print(f"Erro SaveFrom: {e}")

    return None

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    if not usuario_inscrito(message.from_user.id):
        enviar_mensagem_inscricao(message.chat.id)
        return
    bot.reply_to(message, "Envie o link de um vídeo para baixar!")

@bot.message_handler(func=lambda message: True)
def process_link(message):
    if not usuario_inscrito(message.from_user.id):
        enviar_mensagem_inscricao(message.chat.id)
        return

    url = message.text.strip()
    if not (url.startswith("http://") or url.startswith("https://")):
        bot.reply_to(message, "Envie um link válido.")
        return

    msg_status = bot.reply_to(message, "⏳ Processando vídeo...")
    temp_filepath = f"/tmp/{message.message_id}.mp4"

    try:
        download_url = extrair_midia(url)

        if not download_url:
            raise Exception("Não foi possível extrair a URL direta.")

        # Baixa o conteúdo do vídeo
        res = requests.get(download_url, stream=True, timeout=30)
        with open(temp_filepath, 'wb') as f:
            for chunk in res.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    f.write(chunk)

        # Envia o vídeo baixado
        with open(temp_filepath, 'rb') as video_file:
            bot.send_video(
                message.chat.id, 
                video_file, 
                caption="✅ Baixado por @baixatudo1921_bot"
            )

        if os.path.exists(temp_filepath):
            os.remove(temp_filepath)

        bot.delete_message(message.chat.id, msg_status.message_id)

    except Exception as e:
        print(f"Erro detalhado: {e}")
        if os.path.exists(temp_filepath):
            os.remove(temp_filepath)
            
        bot.edit_message_text(
            "❌ Falha ao processar o link. Verifique se o vídeo é público e tente novamente.",
            chat_id=message.chat.id,
            message_id=msg_status.message_id
        )

if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    bot.infinity_polling()
