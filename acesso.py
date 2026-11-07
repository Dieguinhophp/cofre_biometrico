"""Autenticação em tempo real: detecção de piscada (vivacidade) + reconhecimento + nível."""
import time

import cv2

import config
import db
import processamento as pr

VERDE = (0, 200, 0)
VERMELHO = (0, 0, 220)
BRANCO = (255, 255, 255)


def _mostrar_resultado(frame, concedido, texto):
    cor = VERDE if concedido else VERMELHO
    tela = frame.copy()
    cv2.rectangle(tela, (0, 0), (tela.shape[1], 50), cor, -1)
    cv2.putText(tela, texto, (10, 33), cv2.FONT_HERSHEY_SIMPLEX, 0.8, BRANCO, 2)
    cv2.imshow("Cofre - Autenticacao", tela)
    cv2.waitKey(2500)


def autenticar(nivel_exigido):
    """
    Retorna True se o acesso foi concedido. Todo resultado é registrado no log.
    Regra: usuário.nivel >= nivel_exigido (nível 3 = somente o ministro).
    """
    base = db.carregar_base()
    if not base:
        print("Nenhum usuário cadastrado. Cadastre alguém antes de tentar o acesso.")
        return False

    cap = pr.abrir_camera()
    inicio = time.time()
    piscadas = 0
    frames_fechado = 0
    ultimo_frame = None

    concedido = False
    texto_final = "Tempo esgotado"
    usuario_id = nome = distancia = None
    motivo = "Vivacidade não comprovada (nenhuma piscada)"

    try:
        while time.time() - inicio < config.TEMPO_LIMITE_SEGUNDOS:
            ok, frame = cap.read()
            if not ok:
                motivo = "Falha na captura da câmera"
                texto_final = "Falha na camera"
                break
            ultimo_frame = frame

            _, rgb = pr.pre_processar(frame)
            tela = frame.copy()
            msg = "Olhe para a camera e PISQUE"

            if pr.brilho_medio(frame) < config.BRILHO_MINIMO:
                msg = "Iluminacao insuficiente"
            else:
                locais = pr.segmentar_rostos(rgb)
                if len(locais) == 0:
                    msg = "Nenhum rosto detectado"
                elif len(locais) > 1:
                    msg = "Mais de um rosto detectado"
                    piscadas = 0
                else:
                    t, r, b, l = locais[0]
                    cv2.rectangle(tela, (l, t), (r, b), (255, 200, 0), 2)

                    ear = pr.calcular_ear(rgb, locais[0])
                    if ear is not None:
                        if ear < config.EAR_LIMIAR:
                            frames_fechado += 1
                        else:
                            if frames_fechado >= config.EAR_FRAMES_FECHADO:
                                piscadas += 1
                            frames_fechado = 0

                    if piscadas >= config.PISCADAS_NECESSARIAS:
                        enc = pr.extrair_caracteristicas(rgb, locais)[0]
                        usuario, distancia = pr.classificar(enc, base)
                        if usuario is None:
                            motivo = "Rosto não reconhecido"
                            texto_final = "ACESSO NEGADO - nao reconhecido"
                        else:
                            usuario_id, nome = usuario["id"], usuario["nome"]
                            if usuario["nivel"] >= nivel_exigido:
                                concedido = True
                                motivo = "Acesso autorizado"
                                texto_final = "ACESSO CONCEDIDO - %s" % nome
                            else:
                                motivo = "Nível insuficiente (usuário nível %d, exigido %d)" % (
                                    usuario["nivel"], nivel_exigido)
                                texto_final = "ACESSO NEGADO - nivel insuficiente"
                        break

            cv2.putText(tela, msg, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, BRANCO, 2)
            restante = int(config.TEMPO_LIMITE_SEGUNDOS - (time.time() - inicio))
            cv2.putText(tela, "Tempo: %ds | ESC cancela" % restante, (10, tela.shape[0] - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, BRANCO, 1)
            cv2.imshow("Cofre - Autenticacao", tela)
            if cv2.waitKey(1) & 0xFF == 27:
                motivo = "Cancelado pelo operador"
                texto_final = "Cancelado"
                break

        if ultimo_frame is not None:
            _mostrar_resultado(ultimo_frame, concedido, texto_final)
    finally:
        cap.release()
        cv2.destroyAllWindows()

    db.registrar_log(usuario_id, nome, nivel_exigido,
                     "CONCEDIDO" if concedido else "NEGADO", motivo, distancia)
    print(("[CONCEDIDO] " if concedido else "[NEGADO] ") + motivo)
    return concedido
