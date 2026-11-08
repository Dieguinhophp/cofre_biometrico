"""Interface gráfica (Tkinter) do sistema de acesso biométrico ao cofre.

Reaproveita os módulos já existentes (config, db, processamento, cadastro, relatorio).
Execute com:  python gui.py
"""
import time
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import cv2
import mysql.connector
from PIL import Image, ImageTk

import cadastro
import config
import db
import processamento as pr
import relatorio

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


# ---------- Aba: acesso ao cofre ----------
class AbaAcesso(ttk.Frame):
    def __init__(self, master):
        super().__init__(master, padding=14)
        self.camera = CameraPanel(self, self.processar)
        self.camera.grid(row=0, column=1, sticky="n")

        painel = ttk.Frame(self)
        painel.grid(row=0, column=0, sticky="n", padx=(0, 18))

        ttk.Label(painel, text="Acesso ao cofre", style="Titulo.TLabel").pack(anchor="w")
        ttk.Label(painel, text="Nível exigido pela área:").pack(anchor="w", pady=(14, 2))
        self.cb_nivel = ttk.Combobox(painel, state="readonly", values=NIVEL_TEXTOS, width=36)
        self.cb_nivel.current(0)
        self.cb_nivel.pack(anchor="w")

        self.btn_iniciar = ttk.Button(painel, text="Iniciar autenticação",
                                      style="Acc.TButton", command=self.iniciar)
        self.btn_iniciar.pack(fill="x", pady=(14, 4))
        self.btn_cancelar = ttk.Button(painel, text="Cancelar", command=self.cancelar,
                                       state="disabled")
        self.btn_cancelar.pack(fill="x")

        self.lbl_resultado = tk.Label(painel, text="AGUARDANDO", font=(FONTE, 15, "bold"),
                                      bg="#e5e7eb", fg=ESCURO, width=26, height=4,
                                      wraplength=300)
        self.lbl_resultado.pack(fill="x", pady=(18, 8))
        self.lbl_detalhe = ttk.Label(
            painel, wraplength=320, justify="left",
            text="Escolha o nível e clique em iniciar. Olhe para a câmera e pisque "
                 "quando solicitado (isso evita fraude com fotografia).")
        self.lbl_detalhe.pack(anchor="w")
        self._reset_estado()

    # -- estado --
    def _reset_estado(self):
        self.piscadas = 0
        self.frames_fechado = 0
        self.viu_rosto = False
        self.ultimo_frame = None
        self.inicio = 0.0
        self.base = []
        self.nivel_exigido = 1

    def _botoes(self, em_andamento):
        self.btn_iniciar.config(state="disabled" if em_andamento else "normal")
        self.btn_cancelar.config(state="normal" if em_andamento else "disabled")
        self.cb_nivel.config(state="disabled" if em_andamento else "readonly")

    def parar(self):
        """Chamado ao trocar de aba."""
        self.camera.parar()
        self._botoes(False)

    # -- ações --
    def iniciar(self):
        try:
            base = db.carregar_base()
        except mysql.connector.Error as e:
            erro_db(e)
            return
        if not base:
            messagebox.showwarning("Sem usuários",
                                   "Nenhum usuário cadastrado. Cadastre alguém antes.")
            return

        self._reset_estado()
        self.base = base
        self.nivel_exigido = NIVEL_IDS[self.cb_nivel.current()]
        self.inicio = time.time()
        try:
            self.camera.iniciar()
        except RuntimeError as e:
            messagebox.showerror("Câmera", str(e))
            return
        self._botoes(True)
        self.lbl_resultado.config(text="AUTENTICANDO...", bg="#e5e7eb", fg=ESCURO)

    def cancelar(self):
        if self.camera.ativa and self.ultimo_frame is not None:
            self.finalizar(self.ultimo_frame, False, "Cancelado pelo operador", "CANCELADO")
        else:
            self.parar()
            self.lbl_resultado.config(text="CANCELADO", bg="#e5e7eb", fg=ESCURO)

    def dica(self, texto, restante):
        self.lbl_detalhe.config(text="%s\nTempo restante: %ds" % (texto, restante))

    def processar(self, frame):
        self.ultimo_frame = frame
        decorrido = time.time() - self.inicio
        restante = max(0, int(config.TEMPO_LIMITE_SEGUNDOS - decorrido))

        if decorrido > config.TEMPO_LIMITE_SEGUNDOS:
            motivo = ("Vivacidade não comprovada (nenhuma piscada)" if self.viu_rosto
                      else "Nenhum rosto detectado no tempo limite")
            self.finalizar(frame, False, motivo, "TEMPO ESGOTADO")
            return None

        _, rgb = pr.pre_processar(frame)
        tela = frame.copy()

        if pr.brilho_medio(frame) < config.BRILHO_MINIMO:
            self.dica("Iluminação insuficiente. Melhore a luz.", restante)
            return tela

        locais = pr.segmentar_rostos(rgb)
        if len(locais) == 0:
            self.dica("Nenhum rosto detectado. Olhe para a câmera.", restante)
        elif len(locais) > 1:
            self.dica("Mais de um rosto detectado. Apenas uma pessoa.", restante)
            self.piscadas = 0
        else:
            self.viu_rosto = True
            t, r, b, l = locais[0]
            cv2.rectangle(tela, (l, t), (r, b), BGR_AZUL, 2)
            self.dica("Rosto detectado. PISQUE para confirmar.", restante)

            ear = pr.calcular_ear(rgb, locais[0])
            if ear is not None:
                if ear < config.EAR_LIMIAR:
                    self.frames_fechado += 1
                else:
                    if self.frames_fechado >= config.EAR_FRAMES_FECHADO:
                        self.piscadas += 1
                    self.frames_fechado = 0

            if self.piscadas >= config.PISCADAS_NECESSARIAS:
                encs = pr.extrair_caracteristicas(rgb, locais)
                if not encs:
                    self.piscadas = 0
                    return tela
                self.decidir(frame, encs[0])
                return None
        return tela

    def decidir(self, frame, encoding):
        usuario, distancia = pr.classificar(encoding, self.base)
        if usuario is None:
            self.finalizar(frame, False, "Rosto não reconhecido", "ACESSO NEGADO",
                           distancia=distancia)
            return
        uid, nome = usuario["id"], usuario["nome"]
        if usuario["nivel"] >= self.nivel_exigido:
            self.finalizar(frame, True, "Acesso autorizado", "ACESSO CONCEDIDO\n%s" % nome,
                           uid, nome, distancia)
        else:
            motivo = "Nível insuficiente (usuário nível %d, exigido %d)" % (
                usuario["nivel"], self.nivel_exigido)
            self.finalizar(frame, False, motivo, "ACESSO NEGADO\n%s" % nome,
                           uid, nome, distancia)

    def finalizar(self, frame, concedido, motivo, titulo,
                  uid=None, nome=None, distancia=None):
        final = frame.copy()
        h, w = final.shape[:2]
        cv2.rectangle(final, (0, 0), (w - 1, h - 1),
                      BGR_VERDE if concedido else BGR_VERMELHO, 14)
        self.camera.mostrar(final)
        self.camera.parar(manter_imagem=True)
        self._botoes(False)

        self.lbl_resultado.config(text=titulo, bg=VERDE if concedido else VERMELHO, fg="white")
        self.lbl_detalhe.config(text=motivo)
        try:
            db.registrar_log(uid, nome, self.nivel_exigido,
                             "CONCEDIDO" if concedido else "NEGADO", motivo, distancia)
        except mysql.connector.Error as e:
            erro_db(e)


# ---------- Aba: cadastro ----------
class AbaCadastro(ttk.Frame):
    def __init__(self, master):
        super().__init__(master, padding=14)
        self.camera = CameraPanel(self, self.processar)
        self.camera.grid(row=0, column=1, sticky="n")

        painel = ttk.Frame(self)
        painel.grid(row=0, column=0, sticky="n", padx=(0, 18))

        ttk.Label(painel, text="Cadastro de usuário", style="Titulo.TLabel").pack(anchor="w")
        ttk.Label(painel, text="Nome completo:").pack(anchor="w", pady=(14, 2))
        self.var_nome = tk.StringVar()
        self.ent_nome = ttk.Entry(painel, textvariable=self.var_nome, width=39)
        self.ent_nome.pack(anchor="w")

        ttk.Label(painel, text="Nível de acesso:").pack(anchor="w", pady=(10, 2))
        self.cb_nivel = ttk.Combobox(painel, state="readonly", values=NIVEL_TEXTOS, width=36)
        self.cb_nivel.current(0)
        self.cb_nivel.pack(anchor="w")

        self.btn_camera = ttk.Button(painel, text="Iniciar câmera", style="Acc.TButton",
                                     command=self.iniciar_camera)
        self.btn_camera.pack(fill="x", pady=(16, 4))
        self.btn_capturar = ttk.Button(painel, text="Capturar rosto", command=self.capturar,
                                       state="disabled")
        self.btn_capturar.pack(fill="x", pady=2)
        self.btn_cancelar = ttk.Button(painel, text="Cancelar cadastro", command=self.cancelar,
                                       state="disabled")
        self.btn_cancelar.pack(fill="x", pady=2)
        ttk.Separator(painel).pack(fill="x", pady=10)
        self.btn_pasta = ttk.Button(painel, text="Importar fotos de uma pasta...",
                                    command=self.importar_pasta)
        self.btn_pasta.pack(fill="x")

        self.progresso = ttk.Progressbar(painel, maximum=config.NUM_FOTOS_CADASTRO,
                                         length=300)
        self.progresso.pack(fill="x", pady=(16, 4))
        self.lbl_status = ttk.Label(painel, wraplength=320, justify="left",
                                    text="Informe nome e nível, depois inicie a câmera. "
                                         "Serão %d capturas, variando levemente a posição "
                                         "do rosto." % config.NUM_FOTOS_CADASTRO)
        self.lbl_status.pack(anchor="w")
        self._reset_estado()

    def _reset_estado(self):
        self.encodings = []
        self.ultimo = None
        self.progresso["value"] = 0

    def _botoes(self, capturando):
        self.btn_camera.config(state="disabled" if capturando else "normal")
        self.btn_capturar.config(state="normal" if capturando else "disabled")
        self.btn_cancelar.config(state="normal" if capturando else "disabled")
        self.btn_pasta.config(state="disabled" if capturando else "normal")
        self.ent_nome.config(state="disabled" if capturando else "normal")
        self.cb_nivel.config(state="disabled" if capturando else "readonly")

    def parar(self):
        """Chamado ao trocar de aba."""
        self.camera.parar()
        self._botoes(False)
        self._reset_estado()

    def _dados(self):
        nome = self.var_nome.get().strip()
        if not nome:
            messagebox.showwarning("Cadastro", "Informe o nome completo.")
            return None
        return nome, NIVEL_IDS[self.cb_nivel.current()]

    def iniciar_camera(self):
        if self._dados() is None:
            return
        self._reset_estado()
        try:
            self.camera.iniciar()
        except RuntimeError as e:
            messagebox.showerror("Câmera", str(e))
            return
        self._botoes(True)
        self.lbl_status.config(text="Capturas: 0/%d. Posicione o rosto e clique em "
                                    "'Capturar rosto'." % config.NUM_FOTOS_CADASTRO)

    def cancelar(self):
        self.parar()
        self.lbl_status.config(text="Cadastro cancelado.")

    def processar(self, frame):
        _, rgb = pr.pre_processar(frame)
        locais = pr.segmentar_rostos(rgb)
        self.ultimo = (frame, rgb, locais, pr.brilho_medio(frame))
        tela = frame.copy()
        for (t, r, b, l) in locais:
            cv2.rectangle(tela, (l, t), (r, b), BGR_VERDE, 2)
        return tela

    def capturar(self):
        if self.ultimo is None:
            return
        _, rgb, locais, brilho = self.ultimo
        if brilho < config.BRILHO_MINIMO:
            self.lbl_status.config(text="Iluminação insuficiente. Melhore a luz e tente de novo.")
        elif len(locais) == 0:
            self.lbl_status.config(text="Nenhum rosto detectado.")
        elif len(locais) > 1:
            self.lbl_status.config(text="Mais de um rosto na imagem. Apenas uma pessoa por vez.")
        else:
            encs = pr.extrair_caracteristicas(rgb, locais)
            if not encs:
                self.lbl_status.config(text="Não foi possível extrair as características.")
                return
            self.encodings.append(encs[0])
            self.progresso["value"] = len(self.encodings)
            self.lbl_status.config(text="Capturas: %d/%d" % (
                len(self.encodings), config.NUM_FOTOS_CADASTRO))
            if len(self.encodings) >= config.NUM_FOTOS_CADASTRO:
                self.salvar()

    def salvar(self):
        nome, nivel = self._dados()
        encodings = list(self.encodings)
        self.parar()
        try:
            uid = db.criar_usuario(nome, nivel, encodings)
        except mysql.connector.Error as e:
            erro_db(e)
            return
        self.var_nome.set("")
        self.lbl_status.config(text="Usuário '%s' cadastrado (id=%d, nível %d)." % (
            nome, uid, nivel))
        messagebox.showinfo("Cadastro concluído",
                            "Usuário '%s' cadastrado com sucesso (nível %d)." % (nome, nivel))

    def importar_pasta(self):
        dados = self._dados()
        if dados is None:
            return
        nome, nivel = dados
        pasta = filedialog.askdirectory(title="Pasta com as fotos do usuário")
        if not pasta:
            return
        self.lbl_status.config(text="Processando imagens...")
        self.update_idletasks()
        try:
            uid = cadastro.cadastrar_por_pasta(nome, nivel, pasta)
        except (RuntimeError, mysql.connector.Error) as e:
            messagebox.showerror("Cadastro", str(e))
            self.lbl_status.config(text="Falha no cadastro.")
            return
        if uid is None:
            messagebox.showwarning("Cadastro", "Nenhuma imagem válida (um rosto por foto) "
                                               "foi encontrada. Usuário não cadastrado.")
            self.lbl_status.config(text="Nenhuma imagem válida.")
        else:
            self.var_nome.set("")
            self.lbl_status.config(text="Usuário '%s' cadastrado (id=%d)." % (nome, uid))
            messagebox.showinfo("Cadastro concluído",
                                "Usuário '%s' cadastrado a partir da pasta." % nome)


# ---------- Aba: usuários ----------
class AbaUsuarios(ttk.Frame):
    def __init__(self, master):
        super().__init__(master, padding=14)
        ttk.Label(self, text="Usuários cadastrados", style="Titulo.TLabel").pack(anchor="w")

        colunas = ("id", "nome", "nivel", "ativo", "amostras")
        self.tree = ttk.Treeview(self, columns=colunas, show="headings", height=16)
        for col, titulo, larg in (("id", "ID", 60), ("nome", "Nome", 320),
                                  ("nivel", "Nível", 260), ("ativo", "Ativo", 80),
                                  ("amostras", "Amostras", 90)):
            self.tree.heading(col, text=titulo)
            self.tree.column(col, width=larg, anchor="w" if col in ("nome", "nivel") else "center")
        self.tree.pack(fill="both", expand=True, pady=10)

        barra = ttk.Frame(self)
        barra.pack(anchor="w")
        ttk.Button(barra, text="Atualizar", command=self.atualizar).pack(side="left", padx=(0, 8))
        ttk.Button(barra, text="Remover selecionado", command=self.remover).pack(side="left")

    def atualizar(self):
        try:
            usuarios = db.listar_usuarios()
        except mysql.connector.Error as e:
            erro_db(e)
            return
        self.tree.delete(*self.tree.get_children())
        for uid, nome, nivel, ativo, n in usuarios:
            self.tree.insert("", "end", values=(
                uid, nome, config.NIVEIS.get(nivel, nivel), "sim" if ativo else "não", n))

    def remover(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Usuários", "Selecione um usuário na tabela.")
            return
        uid, nome = self.tree.item(sel[0])["values"][:2]
        if not messagebox.askyesno("Confirmar", "Remover o usuário '%s'?\n"
                                   "Os dados faciais também serão apagados." % nome):
            return
        try:
            db.remover_usuario(int(uid))
        except mysql.connector.Error as e:
            erro_db(e)
            return
        self.atualizar()


# ---------- Aba: relatórios ----------
class AbaRelatorios(ttk.Frame):
    LARGURA_BARRA = 460

    def __init__(self, master):
        super().__init__(master, padding=14)
        ttk.Label(self, text="Relatório de acessos", style="Titulo.TLabel").pack(anchor="w")

        topo = ttk.Frame(self)
        topo.pack(fill="x", pady=(8, 6))
        esq = ttk.Frame(topo)
        esq.pack(side="left", anchor="n")
        self.lbl_resumo = ttk.Label(esq, text="")
        self.lbl_resumo.pack(anchor="w")
        self.canvas = tk.Canvas(esq, width=self.LARGURA_BARRA, height=34, bg=BG,
                                highlightthickness=0)
        self.canvas.pack(anchor="w", pady=6)
        self.lbl_motivos = ttk.Label(topo, text="", justify="left")
        self.lbl_motivos.pack(side="left", anchor="n", padx=30)

        colunas = ("data", "nome", "nivel", "resultado", "motivo", "dist")
        self.tree = ttk.Treeview(self, columns=colunas, show="headings", height=13)
        for col, titulo, larg in (("data", "Data/hora", 150), ("nome", "Nome", 170),
                                  ("nivel", "Nível exigido", 100), ("resultado", "Resultado", 100),
                                  ("motivo", "Motivo", 360), ("dist", "Distância", 80)):
            self.tree.heading(col, text=titulo)
            self.tree.column(col, width=larg, anchor="w" if col in ("nome", "motivo") else "center")
        self.tree.tag_configure("ok", foreground=VERDE)
        self.tree.tag_configure("negado", foreground=VERMELHO)
        self.tree.pack(fill="both", expand=True)

        barra = ttk.Frame(self)
        barra.pack(anchor="w", pady=(10, 0))
        ttk.Button(barra, text="Atualizar", command=self.atualizar).pack(side="left", padx=(0, 8))
        ttk.Button(barra, text="Exportar CSV...", command=self.exportar).pack(side="left")

    def _barra(self, concedidos, negados):
        c = self.canvas
        c.delete("all")
        total = concedidos + negados
        L = self.LARGURA_BARRA
        if total == 0:
            c.create_rectangle(0, 0, L, 34, fill="#d1d5db", outline="")
            c.create_text(L / 2, 17, text="Sem registros", fill=ESCURO, font=(FONTE, 10, "bold"))
            return
        wv = L * concedidos / total
        if concedidos:
            c.create_rectangle(0, 0, wv, 34, fill=VERDE, outline="")
            c.create_text(wv / 2, 17, text="Concedidos: %d" % concedidos, fill="white",
                          font=(FONTE, 10, "bold"))
        if negados:
            c.create_rectangle(wv, 0, L, 34, fill=VERMELHO, outline="")
            c.create_text((wv + L) / 2, 17, text="Negados: %d" % negados, fill="white",
                          font=(FONTE, 10, "bold"))

    def atualizar(self):
        try:
            por_resultado, motivos, _ = db.estatisticas()
            logs = db.consultar_logs(200)
        except mysql.connector.Error as e:
            erro_db(e)
            return
        c = por_resultado.get("CONCEDIDO", 0)
        n = por_resultado.get("NEGADO", 0)
        self.lbl_resumo.config(text="Total de tentativas: %d" % (c + n))
        self._barra(c, n)

        if motivos:
            linhas = ["Motivos de negação:"] + ["  • %s: %d" % (m, q) for m, q in motivos[:5]]
        else:
            linhas = ["Nenhuma negação registrada."]
        self.lbl_motivos.config(text="\n".join(linhas))

        self.tree.delete(*self.tree.get_children())
        for data, nome, nivel, resultado, motivo, dist in logs:
            self.tree.insert("", "end", tags=("ok" if resultado == "CONCEDIDO" else "negado",),
                             values=(formatar_data(data), nome, nivel, resultado, motivo,
                                     "-" if dist is None else "%.3f" % dist))

    def exportar(self):
        caminho = filedialog.asksaveasfilename(
            defaultextension=".csv", initialfile="relatorio_acessos.csv",
            filetypes=[("CSV", "*.csv")], title="Exportar relatório")
        if not caminho:
            return
        try:
            relatorio.exportar_csv(caminho)
        except (OSError, mysql.connector.Error) as e:
            messagebox.showerror("Exportar", str(e))
            return
        messagebox.showinfo("Exportar", "Relatório exportado para:\n%s" % caminho)


# ---------- Janela principal ----------
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Cofre Biométrico - Ministério do Meio Ambiente")
        self.geometry("1120x720")
        self.minsize(1040, 700)
        self.configure(bg=BG)
        self._estilo()

        cab = tk.Frame(self, bg=ESCURO)
        cab.pack(fill="x")
        tk.Label(cab, text="COFRE DE SEGURANÇA MÁXIMA", bg=ESCURO, fg="white",
                 font=(FONTE, 16, "bold")).pack(side="left", padx=18, pady=10)
        tk.Label(cab, text="Identificação e autenticação biométrica facial", bg=ESCURO,
                 fg="#9ca3af", font=(FONTE, 10)).pack(side="left", pady=10)

        self.nb = ttk.Notebook(self)
        self.nb.pack(fill="both", expand=True, padx=10, pady=10)
        self.abas = [
            (AbaAcesso(self.nb), "  Acesso ao cofre  "),
            (AbaCadastro(self.nb), "  Cadastro  "),
            (AbaUsuarios(self.nb), "  Usuários  "),
            (AbaRelatorios(self.nb), "  Relatórios  "),
        ]
        for aba, titulo in self.abas:
            self.nb.add(aba, text=titulo)
        self.nb.bind("<<NotebookTabChanged>>", self.ao_trocar_aba)
        self.protocol("WM_DELETE_WINDOW", self.fechar)

        self.after(200, self.checar_banco)

    def _estilo(self):
        st = ttk.Style(self)
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

    def checar_banco(self):
        try:
            db.conectar().close()
        except mysql.connector.Error as e:
            erro_db(e)

    def ao_trocar_aba(self, _evento=None):
        for aba, _ in self.abas:
            if hasattr(aba, "camera"):
                aba.parar()
        atual = self.nametowidget(self.nb.select())
        if hasattr(atual, "atualizar"):
            atual.atualizar()

    def fechar(self):
        for aba, _ in self.abas:
            if hasattr(aba, "camera"):
                aba.camera.parar()
        self.destroy()


if __name__ == "__main__":
    App().mainloop()
