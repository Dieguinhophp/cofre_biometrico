"""Menu principal - Sistema de identificação e autenticação biométrica do cofre."""
import mysql.connector

import acesso
import cadastro
import config
import db
import relatorio


def ler_nivel(prompt="Nível (1, 2 ou 3): "):
    while True:
        try:
            n = int(input(prompt))
            if n in config.NIVEIS:
                return n
        except ValueError:
            pass
        print("  Valor inválido. Digite 1, 2 ou 3.")


def ler_nome():
    while True:
        nome = input("Nome completo: ").strip()
        if nome:
            return nome
        print("  O nome não pode ficar vazio.")


def listar():
    usuarios = db.listar_usuarios()
    if not usuarios:
        print("Nenhum usuário cadastrado.")
        return
    print("\n%-4s %-30s %-6s %-6s %s" % ("ID", "Nome", "Nível", "Ativo", "Amostras"))
    for uid, nome, nivel, ativo, n in usuarios:
        print("%-4d %-30s %-6d %-6s %d" % (uid, nome, nivel, "sim" if ativo else "não", n))


def menu():
    while True:
        print("\n===== COFRE - MINISTÉRIO DO MEIO AMBIENTE =====")
        print("1) Cadastrar usuário (câmera)")
        print("2) Cadastrar usuário (pasta de imagens / scanner)")
        print("3) Acessar o cofre")
        print("4) Listar usuários")
        print("5) Remover usuário")
        print("6) Relatório de acessos")
        print("7) Exportar relatório CSV")
        print("0) Sair")
        opcao = input("Escolha: ").strip()

        try:
            if opcao == "1":
                cadastro.cadastrar_com_camera(ler_nome(), ler_nivel())
            elif opcao == "2":
                nome, nivel = ler_nome(), ler_nivel()
                cadastro.cadastrar_por_pasta(nome, nivel, input("Caminho da pasta: ").strip())
            elif opcao == "3":
                print("\n".join("  %d = %s" % (k, v) for k, v in config.NIVEIS.items()))
                acesso.autenticar(ler_nivel("Nível exigido pela área (1-3): "))
            elif opcao == "4":
                listar()
            elif opcao == "5":
                listar()
                uid = int(input("ID a remover: "))
                print("Removido." if db.remover_usuario(uid) else "ID não encontrado.")
            elif opcao == "6":
                relatorio.mostrar_relatorio()
            elif opcao == "7":
                relatorio.exportar_csv()
            elif opcao == "0":
                break
            else:
                print("Opção inválida.")
        except mysql.connector.Error as e:
            print("[ERRO DE BANCO] %s\nVerifique se o MySQL do XAMPP está ligado e se o schema.sql foi importado." % e)
        except ValueError:
            print("[ERRO] Valor numérico inválido.")
        except RuntimeError as e:
            print("[ERRO] %s" % e)
        except KeyboardInterrupt:
            print("\nOperação interrompida.")


if __name__ == "__main__":
    menu()
