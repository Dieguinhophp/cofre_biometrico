"""Elementos compartilhados pelas interfaces (painel administrativo e terminal dos cofres)."""
import tkinter as tk
from tkinter import messagebox, ttk

import cv2
from PIL import Image, ImageTk

import config
import processamento as pr

# ---------- Aparência ----------
BG = "#f3f4f6"
ESCURO = "#111827"
CINZA = "#6b7280"
VERDE = "#16a34a"
VERMELHO = "#dc2626"
AZUL = "#1d4ed8"
BGR_VERDE = (74, 163, 22)
BGR_VERMELHO = (38, 38, 220)
BGR_AZUL = (255, 200, 0)
FONTE = "Segoe UI"
LARG, ALT = 640, 480

NIVEL_IDS = list(config.NIVEIS.keys())
NIVEL_TEXTOS = list(config.NIVEIS.values())


def erro_db(e):
    messagebox.showerror(
        "Erro de banco de dados",
        "%s\n\nVerifique se o MySQL do XAMPP está ligado e se o schema.sql foi importado." % e,
    )


def formatar_data(d):
    return d.strftime("%d/%m/%Y %H:%M:%S") if hasattr(d, "strftime") else str(d)


def centralizar(janela, largura, altura):
    janela.update_idletasks()
    x = (janela.winfo_screenwidth() - largura) // 2
    y = (janela.winfo_screenheight() - altura) // 3
    janela.geometry("%dx%d+%d+%d" % (largura, altura, max(x, 0), max(y, 0)))


def aplicar_estilo(raiz):
    raiz.configure(bg=BG)
    st = ttk.Style(raiz)
    st.theme_use("clam")
    st.configure(".", background=BG, font=(FONTE, 10))
    st.configure("TNotebook", background=BG)
    st.configure("TNotebook.Tab", padding=(14, 8), font=(FONTE, 11, "bold"))
    st.configure("Titulo.TLabel", font=(FONTE, 16, "bold"), foreground=ESCURO)
    st.configure("Acc.TButton", font=(FONTE, 11, "bold"), padding=10,
                 background=AZUL, foreground="white")
    st.map("Acc.TButton", background=[("active", "#1e40af"), ("disabled", "#9ca3af")])
    st.configure("TButton", padding=6)
    st.configure("Treeview", rowheight=26, font=(FONTE, 10))
    st.configure("Treeview.Heading", font=(FONTE, 10, "bold"))


def cabecalho(raiz, titulo, subtitulo=""):
    """Faixa escura no topo da janela. Retorna o frame para quem quiser adicionar botões."""
    cab = tk.Frame(raiz, bg=ESCURO)
    cab.pack(fill="x")
    tk.Label(cab, text=titulo, bg=ESCURO, fg="white",
             font=(FONTE, 16, "bold")).pack(side="left", padx=18, pady=10)
    if subtitulo:
        tk.Label(cab, text=subtitulo, bg=ESCURO, fg="#9ca3af",
                 font=(FONTE, 10)).pack(side="left", pady=10)
    return cab


# ---------- Painel de vídeo ----------
class CameraPanel(tk.Label):
    """Mostra o vídeo da câmera dentro da janela. A cada frame chama processar(frame)."""

    def __init__(self, master, processar):
        self._vazio = ImageTk.PhotoImage(Image.new("RGB", (LARG, ALT), "#1f2937"))
        super().__init__(master, image=self._vazio, bg="#1f2937", bd=2, relief="groove")
        self.processar = processar
        self.cap = None
        self.job = None
        self._foto = None

    @property
    def ativa(self):
        return self.cap is not None

    def iniciar(self):
        if self.ativa:
            return
        self.cap = pr.abrir_camera()   # pode levantar RuntimeError
        self._loop()

    def parar(self, manter_imagem=False):
        if self.job is not None:
            self.after_cancel(self.job)
            self.job = None
        if self.cap is not None:
            self.cap.release()
            self.cap = None
        if not manter_imagem:
            self.configure(image=self._vazio)
            self._foto = None

    def mostrar(self, frame_bgr):
        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        self._foto = ImageTk.PhotoImage(Image.fromarray(rgb))
        self.configure(image=self._foto)

    def _loop(self):
        self.job = None
        if self.cap is None:
            return
        ok, frame = self.cap.read()
        if not ok:
            self.parar()
            messagebox.showerror("Câmera", "Falha na captura do frame da câmera.")
            return
        tela = self.processar(frame)
        if self.cap is None:        # o processamento encerrou a câmera
            return
        self.mostrar(tela if tela is not None else frame)
        self.job = self.after(10, self._loop)
