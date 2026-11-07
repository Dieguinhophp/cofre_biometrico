"""Acesso ao MySQL: usuários, vetores faciais e logs de acesso."""
import json

import mysql.connector
import numpy as np

import config


def conectar():
    return mysql.connector.connect(**config.DB_CONFIG)


# ---------- Usuários ----------
def criar_usuario(nome, nivel, encodings):
    """Cria o usuário e grava todos os seus vetores faciais. Retorna o id."""
    con = conectar()
    try:
        cur = con.cursor()
        cur.execute("INSERT INTO usuarios (nome, nivel) VALUES (%s, %s)", (nome, nivel))
        uid = cur.lastrowid
        for enc in encodings:
            cur.execute(
                "INSERT INTO encodings (usuario_id, vetor) VALUES (%s, %s)",
                (uid, json.dumps([float(x) for x in enc])),
            )
        con.commit()
        return uid
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()


def listar_usuarios():
    con = conectar()
    try:
        cur = con.cursor()
        cur.execute(
            "SELECT u.id, u.nome, u.nivel, u.ativo, COUNT(e.id) "
            "FROM usuarios u LEFT JOIN encodings e ON e.usuario_id = u.id "
            "GROUP BY u.id ORDER BY u.id"
        )
        return cur.fetchall()
    finally:
        con.close()


def remover_usuario(uid):
    con = conectar()
    try:
        cur = con.cursor()
        cur.execute("DELETE FROM usuarios WHERE id = %s", (uid,))
        con.commit()
        return cur.rowcount > 0
    finally:
        con.close()


def carregar_base():
    """Retorna uma lista de dicts {id, nome, nivel, vetor} de usuários ativos."""
    con = conectar()
    try:
        cur = con.cursor()
        cur.execute(
            "SELECT u.id, u.nome, u.nivel, e.vetor FROM encodings e "
            "JOIN usuarios u ON u.id = e.usuario_id WHERE u.ativo = 1"
        )
        return [
            {"id": i, "nome": n, "nivel": lv, "vetor": np.array(json.loads(v))}
            for (i, n, lv, v) in cur.fetchall()
        ]
    finally:
        con.close()


# ---------- Logs ----------
def registrar_log(usuario_id, nome, nivel_exigido, resultado, motivo, distancia=None):
    con = conectar()
    try:
        cur = con.cursor()
        cur.execute(
            "INSERT INTO logs_acesso "
            "(usuario_id, nome_detectado, nivel_exigido, resultado, motivo, distancia) "
            "VALUES (%s, %s, %s, %s, %s, %s)",
            (usuario_id, nome, nivel_exigido, resultado, motivo, distancia),
        )
        con.commit()
    finally:
        con.close()


def consultar_logs(limite=None):
    con = conectar()
    try:
        cur = con.cursor()
        sql = (
            "SELECT data_hora, COALESCE(nome_detectado, 'Desconhecido'), nivel_exigido, "
            "resultado, motivo, distancia FROM logs_acesso ORDER BY data_hora DESC"
        )
        if limite:
            sql += " LIMIT %d" % int(limite)
        cur.execute(sql)
        return cur.fetchall()
    finally:
        con.close()


def estatisticas():
    con = conectar()
    try:
        cur = con.cursor()
        cur.execute("SELECT resultado, COUNT(*) FROM logs_acesso GROUP BY resultado")
        por_resultado = dict(cur.fetchall())
        cur.execute(
            "SELECT motivo, COUNT(*) FROM logs_acesso WHERE resultado = 'NEGADO' "
            "GROUP BY motivo ORDER BY COUNT(*) DESC"
        )
        motivos = cur.fetchall()
        cur.execute(
            "SELECT COALESCE(nome_detectado, 'Desconhecido'), COUNT(*) FROM logs_acesso "
            "GROUP BY nome_detectado ORDER BY COUNT(*) DESC"
        )
        por_pessoa = cur.fetchall()
        return por_resultado, motivos, por_pessoa
    finally:
        con.close()
