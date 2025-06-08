# 🕵️‍♂️ AntiStaff PokeOld Chat Monitor 🎮🔔

Welcome to **AntiStaff PokeOld Chat Monitor**, a lightweight Python utility that automatically watches and alerts you to new chat messages in the **PokeOld** game window. Never miss that important lobby message again!

---

## 🚀 Features

- 🔍 **Automatic Chat Detection**  
  Captures only highlighted (yellow) chat lines from the PokeOld window.

- 🔔 **Real-time Alerts**  
  Plays a beep sound and pushes a Windows toast notification for every new message.

- ⚙️ **Minimal Setup**  
  Uses PySimpleGUI for a simple launcher + GUI, plus popular libs (NumPy, OpenCV, pytesseract).

- 🤖 **Auto-Installer**  
  Checks for Tesseract OCR and offers to auto-download & install if missing.

---

## 📋 Requirements

- **Python** ≥ 3.11 (3.13 compatibility currently experimental)
- Windows 7/8/10/11
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) (installed to `C:\Program Files\Tesseract-OCR\tesseract.exe`)
- [Git](https://git-scm.com/) (optional, for cloning)

### Python Dependencies

```text
PySimpleGUI
pywinauto
numpy
opencv-python
pytesseract
winotify
Pillow
