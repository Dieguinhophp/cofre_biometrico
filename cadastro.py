"""Cadastro de usuários: pela câmera (tempo real) ou por pasta de imagens (foto/scanner)."""
import os

import cv2

import config
import db
import processamento as pr

EXTENSOES = (".jpg", ".jpeg", ".png", ".bmp")


def cadastrar_com_camera(nome, nivel):
    cap = pr.abrir_camera()
    encodings = []
    try:
        while len(encodings) < config.NUM_FOTOS_CADASTRO:
            ok, frame = cap.read()
            if not ok:
                raise RuntimeError("Falha na captura do frame da câmera.")
            _, rgb = pr.pre_processar(frame)
            locais = pr.segmentar_rostos(rgb)

            tela = frame.copy()
            for (t, r, b, l) in locais:
                cv2.rectangle(tela, (l, t), (r, b), (0, 255, 0), 2)
            texto = "Capturas %d/%d | ESPACO = capturar | ESC = cancelar" % (
                len(encodings), config.NUM_FOTOS_CADASTRO)
            cv2.putText(tela, texto, (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            cv2.imshow("Cadastro - " + nome, tela)

            tecla = cv2.waitKey(1) & 0xFF
            if tecla == 27:
                print("Cadastro cancelado.")
                return None
            if tecla == 32:
                if pr.brilho_medio(frame) < config.BRILHO_MINIMO:
                    print("  [!] Iluminação insuficiente. Melhore a luz e tente de novo.")
                elif len(locais) == 0:
                    print("  [!] Nenhum rosto detectado.")
                elif len(locais) > 1:
                    print("  [!] Mais de um rosto na imagem. Apenas uma pessoa por vez.")
                else:
                    encodings.append(pr.extrair_caracteristicas(rgb, locais)[0])
                    print("  [ok] Captura %d/%d" % (len(encodings), config.NUM_FOTOS_CADASTRO))
    finally:
        cap.release()
        cv2.destroyAllWindows()

    uid = db.criar_usuario(nome, nivel, encodings)
    print("Usuário '%s' cadastrado (id=%d, nível %d)." % (nome, uid, nivel))
    return uid


def cadastrar_por_pasta(nome, nivel, pasta):
    """Usa imagens já existentes (câmera, celular ou scanner) de uma pasta."""
    if not os.path.isdir(pasta):
        raise RuntimeError("Pasta não encontrada: %s" % pasta)

    encodings = []
    for arquivo in sorted(os.listdir(pasta)):
        if not arquivo.lower().endswith(EXTENSOES):
            continue
        img = cv2.imread(os.path.join(pasta, arquivo))
        if img is None:
            print("  [!] Não foi possível ler %s" % arquivo)
            continue
        _, rgb = pr.pre_processar(img)
        locais = pr.segmentar_rostos(rgb)
        if len(locais) != 1:
            print("  [!] %s ignorada (rostos detectados: %d)" % (arquivo, len(locais)))
            continue
        encodings.append(pr.extrair_caracteristicas(rgb, locais)[0])
        print("  [ok] %s" % arquivo)

    if not encodings:
        print("Nenhuma imagem válida encontrada. Usuário não cadastrado.")
        return None
    uid = db.criar_usuario(nome, nivel, encodings)
    print("Usuário '%s' cadastrado com %d imagens (id=%d)." % (nome, len(encodings), uid))
    return uid
