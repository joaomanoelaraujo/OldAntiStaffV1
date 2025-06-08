import os
import subprocess
import sys
import tempfile
import urllib.request
import threading
import time
import re

import PySimpleGUI as sg
from pywinauto import Desktop
import numpy as np
import cv2
import pytesseract
import winsound
from winotify import Notification, audio
from PIL import Image

# ----------------------------------------
# Configurações de dependência
# ----------------------------------------
TESSERACT_CMD = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
TESSERACT_INSTALLER_URL = (
    "https://github.com/tesseract-ocr/tesseract/"
    "releases/download/5.5.0/"
    "tesseract-ocr-w64-setup-5.5.0.20241111.exe"
)
pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD
MONITOR_INTERVAL = 0.5  # segundos

# ----------------------------------------
# 1) Janelinha “console” de lançamento
# ----------------------------------------
def run_launcher_window():
    msgs = [
        ("Verificando dependências...", 0.8),
        # depois a checagem real disponibiliza a mensagem seguinte...
    ]

    # prepararmos a lista dinamicamente
    result_msgs = []
    if os.path.exists(TESSERACT_CMD):
        result_msgs.append(("Dependência encontrada!", 0.8))
    else:
        result_msgs.append(("Dependência não encontrada.", 0.8))
        result_msgs.append(("Instalando Tesseract automaticamente…", 0.8))
        try:
            tmp = tempfile.gettempdir()
            inst = os.path.join(tmp, "tesseract_installer.exe")
            urllib.request.urlretrieve(TESSERACT_INSTALLER_URL, inst)
            subprocess.Popen([inst], shell=True)
            result_msgs.append(("Instalador executado, aguarde a instalação e clique em OK...", 0.8))
        except Exception as e:
            result_msgs.append((f"Erro ao baixar/instalar: {e}", 1.2))
            result_msgs.append(("Por favor baixe manualmente em:", 1.2))
            result_msgs.append((TESSERACT_INSTALLER_URL, 2.0))
            # exibe tudo e sai
            _show_console_and_exit(msgs + result_msgs)
            return

        # espera confirmação do usuário
        _show_console(msgs + result_msgs)
        sg.popup("→ Conclua a instalação do Tesseract e clique em OK para continuar...",
                 title="Instalação do Tesseract", keep_on_top=True)
        # re-verifica
        if os.path.exists(TESSERACT_CMD):
            result_msgs.append(("Dependência encontrada!", 0.8))
        else:
            result_msgs.append(("Ainda não encontrada.", 0.8))
            result_msgs.append(("Faça download manual em:", 0.8))
            result_msgs.append((TESSERACT_INSTALLER_URL, 2.0))
            _show_console_and_exit(msgs + result_msgs)
            return

    # se chegou até aqui com tudo ok:
    result_msgs.extend([
        ("Abrindo software AntiStaff Poke Old", 0.8),
        ("Programa feito por Losttz: https://github.com/joaomanoelaraujo", 1.2),
        ("Abrindo programa...", 0.8)
    ])
    _show_console(msgs + result_msgs)
    # tudo certo, volta para main()

def _show_console(sequence):
    """
    Cria uma janela pequena que imita um console e vai escrevendo
    cada (mensagem, delay) da lista sequence.
    """
    sg.theme("DarkGrey14")
    layout = [[sg.Multiline(
        default_text="",
        size=(60, 10),
        font=("Consolas", 11),
        autoscroll=True,
        disabled=True,
        key="-ML-"
    )]]
    win = sg.Window("Launcher", layout, finalize=True, keep_on_top=True, no_titlebar=False)
    ml = win["-ML-"]
    for text, delay in sequence:
        ml.print(text)
        win.refresh()
        time.sleep(delay)
    win.close()

def _show_console_and_exit(sequence):
    _show_console(sequence)
    sys.exit(1)

# ----------------------------------------
# 2) Funções de monitoramento de chat
# ----------------------------------------
def list_window_titles():
    return [
        w.window_text()
        for w in Desktop(backend="uia").windows()
        if w.window_text().strip()
    ]

def monitor_chat_auto(window_title, stop_event):
    win = Desktop(backend="uia").window(title=window_title)
    rect = win.rectangle()
    left, top, right, bottom = rect.left, rect.top, rect.right, rect.bottom

    h = bottom - top
    chat_top    = top  + int(h * 0.70)
    chat_bottom = bottom - 10
    chat_left   = left + 10
    chat_right  = right - 10
    w_chat = chat_right - chat_left
    h_chat = chat_bottom - chat_top

    lower_yellow = np.array([15, 100, 100])
    upper_yellow = np.array([35, 255, 255])
    timestamp_re = re.compile(r"^\d{2}:\d{2}")

    last_seen   = []
    active_msgs = set()

    while not stop_event.is_set():
        img = win.capture_as_image()
        arr = np.array(img)
        chat = arr[
               (chat_top - top):(chat_top - top + h_chat),
               (chat_left - left):(chat_left - left + w_chat),
               :
               ]

        hsv  = cv2.cvtColor(chat, cv2.COLOR_RGB2HSV)
        mask = cv2.inRange(hsv, lower_yellow, upper_yellow)
        gray = cv2.cvtColor(chat, cv2.COLOR_RGB2GRAY)
        proc = cv2.bitwise_and(gray, gray, mask=mask)

        text  = pytesseract.image_to_string(proc)
        lines = [l.strip() for l in text.splitlines() if timestamp_re.match(l.strip())]

        new_msgs = [l for l in lines if l not in last_seen]
        for msg in new_msgs:
            active_msgs.add(msg)
            winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
            toast = Notification(app_id="Chat Monitor", title="Nova mensagem no chat", msg=msg)
            toast.set_audio(audio.Default, loop=False)
            toast.show()

        for msg in list(active_msgs):
            if msg in lines:
                winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
            else:
                active_msgs.remove(msg)

        last_seen = lines
        time.sleep(MONITOR_INTERVAL)

def chat_monitor_gui():
    sg.theme("DarkBlue3")
    layout = [
        [sg.Text("Janela:"),
         sg.Combo(list_window_titles(), key="-WINS-", size=(40,1)),
         sg.Button("Refresh")],
        [sg.Button("Start"), sg.Button("Stop", disabled=True), sg.Button("Exit")],
    ]
    window = sg.Window("Chat Monitor Automático", layout)
    stop_evt = threading.Event()
    thread   = None

    while True:
        ev, vals = window.read(timeout=100)
        if ev in (sg.WINDOW_CLOSED, "Exit"):
            break
        if ev == "Refresh":
            window["-WINS-"].update(values=list_window_titles())
        if ev == "Start":
            title = vals["-WINS-"]
            if not title:
                sg.popup_error("Escolha uma janela antes de iniciar.")
                continue
            stop_evt.clear()
            thread = threading.Thread(
                target=monitor_chat_auto,
                args=(title, stop_evt),
                daemon=True
            )
            thread.start()
            window["Start"].update(disabled=True)
            window["Stop"].update(disabled=False)
        if ev == "Stop":
            stop_evt.set()
            window["Start"].update(disabled=False)
            window["Stop"].update(disabled=True)

    stop_evt.set()
    window.close()

# ----------------------------------------
# 3) Main
# ----------------------------------------
if __name__ == "__main__":
    # 1) abre a janelinha “console” de lançamento
    run_launcher_window()
    # 2) aí abre a GUI de monitoramento
    chat_monitor_gui()
