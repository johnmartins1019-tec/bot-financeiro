import os
import io
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram import Update
from pydub import AudioSegment
import speech_recognition as sr
from datetime import datetime
import matplotlib.pyplot as plt
import db

def start(update, context):
    update.message.reply_text("Olá! Use /gasto ou envie um áudio com algo como 'gastei 50 reais no mercado'.")

def registrar_gasto_cmd(update, context):
    try:
        valor = float(context.args[0])
        categoria = " ".join(context.args[1:])
        user_id = update.effective_user.id
        data = datetime.now().strftime("%Y-%m-%d %H:%M")
        db.registrar_gasto(user_id, valor, categoria, data)
        update.message.reply_text(f"Gasto de R${valor:.2f} registrado em '{categoria}'.")
    except:
        update.message.reply_text("Use o formato: /gasto 30 mercado")

def total(update, context):
    user_id = update.effective_user.id
    total = db.obter_total(user_id)
    update.message.reply_text(f"Total gasto: R${total:.2f}")

def extrato(update, context):
    user_id = update.effective_user.id
    registros = db.obter_extrato(user_id)
    if not registros:
        update.message.reply_text("Nenhum gasto registrado.")
        return

    texto = "🧾 *Últimos Gastos:*\n\n"
    for valor, categoria, data in registros:
        texto += f"• R${valor:.2f} - {categoria} ({data})\n"
    update.message.reply_text(texto, parse_mode='Markdown')

def enviar_grafico_categoria(update, context):
    user_id = update.effective_user.id
    dados = db.gastos_por_categoria(user_id)
    if not dados:
        update.message.reply_text("Sem dados para gerar gráfico.")
        return

    categorias = [d[0] for d in dados]
    valores = [d[1] for d in dados]

    fig, ax = plt.subplots()
    ax.pie(valores, labels=categorias, autopct='%1.1f%%', startangle=90)
    ax.set_title('Gastos por Categoria')
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    plt.close()
    update.message.reply_photo(photo=buffer)

def enviar_grafico_diario(update, context):
    user_id = update.effective_user.id
    dados = db.gastos_por_dia(user_id)
    if not dados:
        update.message.reply_text("Sem dados para gerar gráfico.")
        return

    datas = [d[0] for d in dados]
    valores = [d[1] for d in dados]

    fig, ax = plt.subplots()
    ax.plot(datas, valores, marker='o')
    ax.set_title('Gastos por Dia')
    ax.set_ylabel('Valor (R$)')
    ax.set_xlabel('Data')
    plt.xticks(rotation=45)
    plt.tight_layout()
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    plt.close()
    update.message.reply_photo(photo=buffer)

def processa_voz(update: Update, context):
    file = update.message.voice.get_file()
    file_path = "voz.ogg"
    wav_path = "voz.wav"
    file.download(file_path)

    sound = AudioSegment.from_ogg(file_path)
    sound.export(wav_path, format="wav")

    r = sr.Recognizer()
    with sr.AudioFile(wav_path) as source:
        audio = r.record(source)

    try:
        texto = r.recognize_google(audio, language="pt-BR").lower()
        update.message.reply_text(f"Você disse: {texto}")
        if "gastei" in texto:
            palavras = texto.split()
            for i, palavra in enumerate(palavras):
                try:
                    valor = float(palavra.replace(",", ".").replace("reais", "").replace("r$", ""))
                    categoria = " ".join(palavras[i+1:])
                    db.registrar_gasto(update.effective_user.id, valor, categoria, datetime.now().strftime("%Y-%m-%d %H:%M"))
                    update.message.reply_text(f"Gasto de R${valor:.2f} registrado como '{categoria}'.")
                    break
                except:
                    continue
        else:
            update.message.reply_text("Tente dizer: 'gastei 20 reais no mercado'")
    except:
        update.message.reply_text("Erro ao reconhecer voz.")
    os.remove(file_path)
    os.remove(wav_path)

def run():
    db.conectar()
    TOKEN = os.getenv("TOKEN")
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("gasto", registrar_gasto_cmd))
    dp.add_handler(CommandHandler("total", total))
    dp.add_handler(CommandHandler("extrato", extrato))
    dp.add_handler(CommandHandler("grafico_categoria", enviar_grafico_categoria))
    dp.add_handler(CommandHandler("grafico_dia", enviar_grafico_diario))
    dp.add_handler(MessageHandler(Filters.voice, processa_voz))

    updater.start_polling()
    updater.idle()
