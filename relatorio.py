"""Relatórios de acesso: tela e exportação CSV."""
import csv

import db


def mostrar_relatorio(limite=20):
    por_resultado, motivos, por_pessoa = db.estatisticas()
    concedidos = por_resultado.get("CONCEDIDO", 0)
    negados = por_resultado.get("NEGADO", 0)

    print("\n=== RESUMO ===")
    print("Total de tentativas: %d (concedidos: %d | negados: %d)" % (
        concedidos + negados, concedidos, negados))

    if motivos:
        print("\nMotivos de negação:")
        for motivo, qtd in motivos:
            print("  - %s: %d" % (motivo, qtd))

    if por_pessoa:
        print("\nTentativas por pessoa:")
        for nome, qtd in por_pessoa:
            print("  - %s: %d" % (nome, qtd))

    print("\n=== ÚLTIMAS %d TENTATIVAS ===" % limite)
    for data, nome, nivel, resultado, motivo, dist in db.consultar_logs(limite):
        d = "-" if dist is None else "%.3f" % dist
        print("%s | %-18s | nível %d | %-9s | dist %s | %s" % (
            data, nome, nivel, resultado, d, motivo))


def exportar_csv(caminho="relatorio_acessos.csv"):
    linhas = db.consultar_logs()
    with open(caminho, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["data_hora", "nome", "nivel_exigido", "resultado", "motivo", "distancia"])
        w.writerows(linhas)
    print("Relatório exportado para %s (%d registros)." % (caminho, len(linhas)))
