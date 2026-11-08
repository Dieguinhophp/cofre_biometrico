"""Terminal de acesso aos cofres (Níveis 1, 2 e 3) com autenticação facial.

O usuário escolhe o cofre, passa pelo reconhecimento facial com prova de vivacidade
(piscar) e, se o nível dele for suficiente, abre o conteúdo (fictício) do cofre.

Execute com:  python cofre.py
"""
import time
import tkinter as tk
from tkinter import messagebox, ttk

import cv2
import mysql.connector

import config
import db
import processamento as pr
from cofre_conteudo import COFRES
from ui_comum import (BG, BGR_AZUL, BGR_VERDE, BGR_VERMELHO, ESCURO, FONTE, NIVEL_IDS,
                      VERDE, VERMELHO, CameraPanel, aplicar_estilo, cabecalho, erro_db)

# cor principal de cada cofre
TEMAS = {1: "#1d4ed8", 2: "#b45309", 3: "#991b1b"}


# ---------- Tela inicial: escolha do cofre ----------
class Inicio(ttk.Frame):
    def __init__(self, master, ao_escolher):
        super().__init__(master, padding=24)
        ttk.Label(self, text="Selecione o cofre que deseja acessar",
                  style="Titulo.TLabel").pack(anchor="w")
        ttk.Label(self, text="A abertura exige reconhecimento facial e prova de vivacidade "
                             "(piscar). Cada cofre exige um nível mínimo de permissão."
                  ).pack(anchor="w", pady=(2, 18))

        linha = ttk.Frame(self)
        linha.pack(fill="both", expand=True)
        for i, nivel in enumerate(NIVEL_IDS):
            cor = TEMAS[nivel]
            cofre = COFRES[nivel]
            linha.columnconfigure(i, weight=1, uniform="cofres")
            card = tk.Frame(linha, bg="white", highlightbackground="#d1d5db",
                            highlightthickness=1)
            card.grid(row=0, column=i, sticky="nsew", padx=10, pady=4)
            tk.Frame(card, bg=cor, height=10).pack(fill="x")
            tk.Label(card, text="COFRE NÍVEL %d" % nivel, bg="white", fg=cor,
                     font=(FONTE, 18, "bold")).pack(pady=(26, 2))
            tk.Label(card, text=cofre["nome"], bg="white", fg=ESCURO,
                     font=(FONTE, 12, "bold")).pack()
            tk.Label(card, text=cofre["perfil"], bg="white", fg="#6b7280",
                     font=(FONTE, 10)).pack(pady=(2, 14))
            tk.Label(card, text=cofre["descricao"], bg="white", fg=ESCURO, wraplength=280,
                     justify="center", font=(FONTE, 10)).pack(padx=16)
            tk.Label(card, text="%d documentos" % len(cofre["documentos"]), bg="white",
                     fg="#6b7280", font=(FONTE, 10)).pack(pady=(14, 0))
            tk.Button(card, text="Acessar cofre", bg=cor, fg="white", activebackground=cor,
                      activeforeground="white", relief="flat", cursor="hand2",
                      font=(FONTE, 11, "bold"), padx=22, pady=10,
                      command=lambda n=nivel: ao_escolher(n)).pack(pady=(18, 28))


# ---------- Autenticação facial ----------
class Autenticacao(ttk.Frame):
    def __init__(self, master, nivel, ao_sucesso, ao_voltar):
        super().__init__(master, padding=14)
        self.nivel_exigido = nivel
        self.ao_sucesso = ao_sucesso
        self.ao_voltar = ao_voltar
        self._raiz = self.winfo_toplevel()
        self._job = None
        self._zerar()

        self.camera = CameraPanel(self, self.processar)
        self.camera.grid(row=0, column=1, sticky="n")

        painel = ttk.Frame(self)
        painel.grid(row=0, column=0, sticky="n", padx=(0, 18))
        tk.Label(painel, text="COFRE NÍVEL %d" % nivel, bg=BG, fg=TEMAS[nivel],
                 font=(FONTE, 18, "bold")).pack(anchor="w")
        ttk.Label(painel, text="Autenticação facial", style="Titulo.TLabel").pack(anchor="w")
        ttk.Label(painel, text="Nível mínimo exigido: %d" % nivel).pack(anchor="w", pady=(4, 14))

        self.lbl_resultado = tk.Label(painel, text="AUTENTICANDO...", font=(FONTE, 15, "bold"),
                                      bg="#e5e7eb", fg=ESCURO, width=26, height=4,
                                      wraplength=300)
        self.lbl_resultado.pack(fill="x", pady=(0, 8))
        self.lbl_detalhe = ttk.Label(painel, wraplength=320, justify="left", text="Iniciando câmera...")
        self.lbl_detalhe.pack(anchor="w")

        self.btn_tentar = ttk.Button(painel, text="Tentar novamente", style="Acc.TButton",
                                     command=self.iniciar, state="disabled")
        self.btn_tentar.pack(fill="x", pady=(18, 4))
        ttk.Button(painel, text="Voltar à seleção de cofres", command=self.ao_voltar
                   ).pack(fill="x")

        self.after(150, self.iniciar)

    def destroy(self):
        # O temporizador é agendado na janela principal (que vive mais que esta tela);
        # agendar na própria tela e destruí-la dentro do callback corrompe nomes de
        # comandos Tcl do Tkinter.
        if self._job is not None:
            try:
                self._raiz.after_cancel(self._job)
            except tk.TclError:
                pass
            self._job = None
        self.camera.parar()
        super().destroy()

    def _zerar(self):
        self.piscadas = 0
        self.frames_fechado = 0
        self.viu_rosto = False
        self.ultimo_frame = None
        self.inicio = 0.0
        self.base = []

    def iniciar(self):
        try:
            base = db.carregar_base()
        except mysql.connector.Error as e:
            erro_db(e)
            self.btn_tentar.config(state="normal")
            return
        if not base:
            messagebox.showwarning("Sem usuários",
                                   "Nenhum usuário cadastrado. Peça ao administrador.")
            self.lbl_resultado.config(text="SEM USUÁRIOS", bg="#e5e7eb", fg=ESCURO)
            self.btn_tentar.config(state="normal")
            return
        self._zerar()
        self.base = base
        self.inicio = time.time()
        try:
            self.camera.iniciar()
        except RuntimeError as e:
            messagebox.showerror("Câmera", str(e))
            self.btn_tentar.config(state="normal")
            return
        self.btn_tentar.config(state="disabled")
        self.lbl_resultado.config(text="AUTENTICANDO...", bg="#e5e7eb", fg=ESCURO)

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
                           uid, nome, distancia, usuario["nivel"])
        else:
            motivo = "Nível insuficiente (usuário nível %d, exigido %d)" % (
                usuario["nivel"], self.nivel_exigido)
            self.finalizar(frame, False, motivo, "ACESSO NEGADO\n%s" % nome,
                           uid, nome, distancia)

    def finalizar(self, frame, concedido, motivo, titulo,
                  uid=None, nome=None, distancia=None, nivel_usuario=None):
        final = frame.copy()
        h, w = final.shape[:2]
        cv2.rectangle(final, (0, 0), (w - 1, h - 1),
                      BGR_VERDE if concedido else BGR_VERMELHO, 14)
        self.camera.mostrar(final)
        self.camera.parar(manter_imagem=True)

        self.lbl_resultado.config(text=titulo, bg=VERDE if concedido else VERMELHO, fg="white")
        self.lbl_detalhe.config(text=motivo)
        try:
            db.registrar_log(uid, nome, self.nivel_exigido,
                             "CONCEDIDO" if concedido else "NEGADO", motivo, distancia)
        except mysql.connector.Error as e:
            erro_db(e)

        if concedido:
            self.lbl_detalhe.config(text="Abrindo o cofre...")
            self._job = self._raiz.after(1600, lambda: self.ao_sucesso(nome, nivel_usuario))
        else:
            self.btn_tentar.config(state="normal")


# ---------- Conteúdo do cofre aberto ----------
class VistaCofre(ttk.Frame):
    def __init__(self, master, nivel, nome, ao_sair):
        super().__init__(master)
        self.ao_sair = ao_sair
        self.restante = config.SESSAO_COFRE_SEGUNDOS
        self._raiz = self.winfo_toplevel()
        self._job = None
        cor = TEMAS[nivel]
        cofre = COFRES[nivel]

        topo = tk.Frame(self, bg=cor)
        topo.pack(fill="x")
        tk.Label(topo, text="COFRE NÍVEL %d  -  %s" % (nivel, cofre["nome"].upper()),
                 bg=cor, fg="white", font=(FONTE, 15, "bold")).pack(side="left", padx=18, pady=12)
        tk.Button(topo, text="Encerrar sessão", command=lambda: self.ao_sair(False),
                  bg="white", fg=cor, relief="flat", cursor="hand2",
                  font=(FONTE, 10, "bold"), padx=12, pady=4).pack(side="right", padx=18)
        self.lbl_tempo = tk.Label(topo, bg=cor, fg="white", font=(FONTE, 10))
        self.lbl_tempo.pack(side="right", padx=8)
        tk.Label(topo, text="Usuário: %s" % nome, bg=cor, fg="white",
                 font=(FONTE, 10, "bold")).pack(side="right", padx=18)

        corpo = ttk.Frame(self, padding=14)
        corpo.pack(fill="both", expand=True)
        corpo.columnconfigure(1, weight=1)
        corpo.rowconfigure(0, weight=1)

        self.docs = {d["codigo"]: d for d in cofre["documentos"]}
        self.tree = ttk.Treeview(corpo, columns=("codigo", "titulo", "classificacao"),
                                 show="headings", height=14)
        for col, titulo, larg in (("codigo", "Código", 70), ("titulo", "Documento", 250),
                                  ("classificacao", "Classificação", 110)):
            self.tree.heading(col, text=titulo)
            self.tree.column(col, width=larg, anchor="w")
        for d in cofre["documentos"]:
            self.tree.insert("", "end", iid=d["codigo"],
                             values=(d["codigo"], d["titulo"], d["classificacao"]))
        self.tree.grid(row=0, column=0, sticky="ns", padx=(0, 12))
        self.tree.bind("<<TreeviewSelect>>", self.mostrar)

        self.texto = tk.Text(corpo, wrap="word", font=("Consolas", 11), bg="white",
                             relief="solid", bd=1, padx=14, pady=12, state="disabled")
        self.texto.tag_configure("titulo", font=(FONTE, 15, "bold"), foreground=cor)
        self.texto.tag_configure("meta", font=(FONTE, 10), foreground="#6b7280")
        self.texto.grid(row=0, column=1, sticky="nsew")

        ttk.Label(self, text="Conteúdo fictício, criado apenas para demonstração acadêmica."
                  ).pack(anchor="w", padx=14, pady=(0, 8))

        self.tree.selection_set(cofre["documentos"][0]["codigo"])
        self._tick()

    def destroy(self):
        if self._job is not None:
            try:
                self._raiz.after_cancel(self._job)
            except tk.TclError:
                pass
            self._job = None
        super().destroy()

    def mostrar(self, _evento=None):
        sel = self.tree.selection()
        if not sel:
            return
        d = self.docs[sel[0]]
        self.texto.config(state="normal")
        self.texto.delete("1.0", "end")
        self.texto.insert("end", d["titulo"] + "\n", "titulo")
        self.texto.insert("end", "%s  |  %s  |  %s  |  %s\n\n" % (
            d["codigo"], d["classificacao"], d["data"], d["autor"]), "meta")
        self.texto.insert("end", d["corpo"])
        self.texto.config(state="disabled")

    def _tick(self):
        self.lbl_tempo.config(text="Sessão expira em %ds" % self.restante)
        if self.restante <= 0:
            self._job = None
            self.ao_sair(True)
            return
        self.restante -= 1
        self._job = self._raiz.after(1000, self._tick)


# ---------- Janela principal ----------
class AppCofre(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Terminal de Acesso aos Cofres - Ministério do Meio Ambiente")
        self.geometry("1120x720")
        self.minsize(1040, 700)
        self.configure(bg=BG)
        aplicar_estilo(self)
        cabecalho(self, "TERMINAL DE ACESSO AOS COFRES",
                  "Autenticação biométrica facial com prova de vivacidade")
        self.container = ttk.Frame(self)
        self.container.pack(fill="both", expand=True)
        self.atual = None
        self.protocol("WM_DELETE_WINDOW", self.fechar)
        self.mostrar_inicio()
        self.after(200, self.checar_banco)

    def checar_banco(self):
        try:
            import db as _db
            _db.conectar().close()
        except mysql.connector.Error as e:
            erro_db(e)

    def _trocar(self, criar):
        if self.atual is not None:
            self.atual.destroy()
            self.atual = None
        self.atual = criar()
        self.atual.pack(fill="both", expand=True)

    def mostrar_inicio(self):
        self._trocar(lambda: Inicio(self.container, self.mostrar_autenticacao))

    def mostrar_autenticacao(self, nivel):
        self._trocar(lambda: Autenticacao(
            self.container, nivel,
            ao_sucesso=lambda nome, nivel_usuario: self.mostrar_cofre(nivel, nome),
            ao_voltar=self.mostrar_inicio))

    def mostrar_cofre(self, nivel, nome):
        self._trocar(lambda: VistaCofre(self.container, nivel, nome, self.sair_do_cofre))

    def sair_do_cofre(self, expirou):
        self.mostrar_inicio()
        if expirou:
            messagebox.showinfo("Sessão encerrada",
                                "A sessão expirou por tempo e o cofre foi fechado.")

    def fechar(self):
        if self.atual is not None:
            self.atual.destroy()
            self.atual = None
        self.destroy()


if __name__ == "__main__":
    AppCofre().mainloop()
