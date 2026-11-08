"""Painel administrativo: login + cadastro de usuários, listagem e relatórios de acesso.

Execute com:  python admin.py      (usuário: admin | senha: 123)
O acesso aos cofres é feito em outro programa:  python cofre.py
"""
import hashlib
import hmac
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import cv2
import mysql.connector

import cadastro
import config
import db
import processamento as pr
import relatorio
from ui_comum import (BG, CINZA, ESCURO, FONTE, NIVEL_IDS, NIVEL_TEXTOS, VERDE, VERMELHO,
                      BGR_VERDE, CameraPanel, aplicar_estilo, cabecalho, centralizar,
                      erro_db, formatar_data)


def credenciais_validas(usuario, senha):
    """Compara usuário e hash SHA-256 da senha em tempo constante."""
    hash_senha = hashlib.sha256(senha.encode("utf-8")).hexdigest()
    ok_usuario = hmac.compare_digest(usuario.encode("utf-8"), config.ADMIN_USUARIO.encode("utf-8"))
    ok_senha = hmac.compare_digest(hash_senha.encode("utf-8"), config.ADMIN_SENHA_HASH.encode("utf-8"))
    return ok_usuario and ok_senha


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


# ---------- Tela de login ----------
class Login(tk.Tk):
    MAX_TENTATIVAS = 3

    def __init__(self):
        super().__init__()
        self.title("Painel Administrativo - Acesso restrito")
        self.resizable(False, False)
        aplicar_estilo(self)
        centralizar(self, 440, 420)
        self.autenticado = False
        self.tentativas = 0

        cabecalho(self, "ÁREA ADMINISTRATIVA", "Acesso restrito")
        corpo = ttk.Frame(self, padding=(32, 24))
        corpo.pack(fill="both", expand=True)
        ttk.Label(corpo, text="Login do administrador", style="Titulo.TLabel").pack(anchor="w")
        ttk.Label(corpo, text="Usuário:").pack(anchor="w", pady=(18, 2))
        self.ent_usuario = ttk.Entry(corpo, width=34)
        self.ent_usuario.pack(anchor="w", fill="x")
        ttk.Label(corpo, text="Senha:").pack(anchor="w", pady=(12, 2))
        self.ent_senha = ttk.Entry(corpo, width=34, show="\u25cf")
        self.ent_senha.pack(anchor="w", fill="x")

        self.lbl_erro = tk.Label(corpo, text="", bg=BG, fg=VERMELHO, font=(FONTE, 10, "bold"),
                                 wraplength=360, justify="left")
        self.lbl_erro.pack(anchor="w", pady=(10, 0))
        self.btn_entrar = ttk.Button(corpo, text="Entrar", style="Acc.TButton",
                                     command=self.entrar)
        self.btn_entrar.pack(fill="x", pady=(10, 0))

        self.bind("<Return>", self.entrar)
        self.ent_usuario.focus()

    def entrar(self, _evento=None):
        if self.btn_entrar.instate(["disabled"]):
            return
        if credenciais_validas(self.ent_usuario.get().strip(), self.ent_senha.get()):
            self.autenticado = True
            self.destroy()
            return
        self.tentativas += 1
        self.ent_senha.delete(0, "end")
        restantes = self.MAX_TENTATIVAS - self.tentativas
        if restantes <= 0:
            self.lbl_erro.config(text="Número máximo de tentativas excedido. "
                                      "O programa será encerrado.")
            self.btn_entrar.config(state="disabled")
            self.after(2500, self.destroy)
        else:
            self.lbl_erro.config(text="Usuário ou senha inválidos. "
                                      "Tentativas restantes: %d" % restantes)
            self.ent_senha.focus()


# ---------- Janela do painel ----------
class AppAdmin(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Painel Administrativo - Cofre Biométrico")
        self.geometry("1120x720")
        self.minsize(1040, 700)
        aplicar_estilo(self)

        cab = cabecalho(self, "PAINEL ADMINISTRATIVO",
                        "Cadastro de usuários e relatórios de acesso")
        tk.Button(cab, text="Sair", command=self.fechar, bg="white", fg=ESCURO, relief="flat",
                  cursor="hand2", font=(FONTE, 10, "bold"), padx=14, pady=4
                  ).pack(side="right", padx=18)
        tk.Label(cab, text="Administrador: %s" % config.ADMIN_USUARIO, bg=ESCURO, fg="#9ca3af",
                 font=(FONTE, 10)).pack(side="right")

        self.nb = ttk.Notebook(self)
        self.nb.pack(fill="both", expand=True, padx=10, pady=10)
        self.abas = [
            (AbaCadastro(self.nb), "  Cadastro  "),
            (AbaUsuarios(self.nb), "  Usuários  "),
            (AbaRelatorios(self.nb), "  Relatórios  "),
        ]
        for aba, titulo in self.abas:
            self.nb.add(aba, text=titulo)
        self.nb.bind("<<NotebookTabChanged>>", self.ao_trocar_aba)
        self.protocol("WM_DELETE_WINDOW", self.fechar)
        self.after(200, self.checar_banco)

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


def main():
    login = Login()
    login.mainloop()
    if login.autenticado:
        AppAdmin().mainloop()


if __name__ == "__main__":
    main()
