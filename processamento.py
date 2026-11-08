"""
As cinco fases do processamento de imagens digitais aplicadas ao reconhecimento facial:

  1. Aquisição              -> cv2.VideoCapture (câmera) ou arquivo de imagem
  2. Pré-processamento      -> suavização + equalização de histograma
  3. Segmentação            -> detecção/localização do rosto (HOG + SVM, dlib)
  4. Extração de caract.    -> embedding facial de 128 dimensões (ResNet, dlib)
  5. Classificação/Interp.  -> menor distância euclidiana + limiar de decisão
"""
import cv2
import numpy as np
import face_recognition

import config


# ---------- 1. Aquisição ----------
def abrir_camera():
    # No Windows, o backend padrão (MSMF) pode demorar quase 1 minuto para abrir.
    # O DirectShow (CAP_DSHOW) abre em poucos segundos.
    cap = cv2.VideoCapture(config.CAMERA_INDEX, cv2.CAP_DSHOW)
    if not cap.isOpened():
        cap.release()
        cap = cv2.VideoCapture(config.CAMERA_INDEX)
    if not cap.isOpened():
        raise RuntimeError("Não foi possível abrir a câmera. Verifique a conexão/permissões.")
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    return cap


# ---------- 2. Pré-processamento ----------
def brilho_medio(frame_bgr):
    """Brilho médio (0-255) medido ANTES da equalização."""
    return float(cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY).mean())


def pre_processar(frame_bgr):
    """Reduz ruído e equaliza a luminância. Retorna (imagem_bgr, imagem_rgb)."""
    suave = cv2.GaussianBlur(frame_bgr, (3, 3), 0)
    ycrcb = cv2.cvtColor(suave, cv2.COLOR_BGR2YCrCb)
    ycrcb[:, :, 0] = cv2.equalizeHist(ycrcb[:, :, 0])
    equalizada = cv2.cvtColor(ycrcb, cv2.COLOR_YCrCb2BGR)
    rgb = cv2.cvtColor(equalizada, cv2.COLOR_BGR2RGB)
    return equalizada, rgb


# ---------- 3. Segmentação ----------
def segmentar_rostos(rgb):
    """Retorna lista de (top, right, bottom, left) na escala da imagem original."""
    pequena = cv2.resize(rgb, (0, 0), fx=config.ESCALA_DETECCAO, fy=config.ESCALA_DETECCAO)
    locs = face_recognition.face_locations(pequena, model="hog")
    k = 1.0 / config.ESCALA_DETECCAO
    return [(int(t * k), int(r * k), int(b * k), int(l * k)) for (t, r, b, l) in locs]


# ---------- 4. Extração de características ----------
def extrair_caracteristicas(rgb, locais):
    """Um vetor de 128 dimensões por rosto localizado."""
    return face_recognition.face_encodings(rgb, known_face_locations=locais, num_jitters=1)


def _ear(olho):
    p = np.array(olho, dtype=float)
    a = np.linalg.norm(p[1] - p[5])
    b = np.linalg.norm(p[2] - p[4])
    c = np.linalg.norm(p[0] - p[3])
    return (a + b) / (2.0 * c)


def calcular_ear(rgb, local):
    """Eye Aspect Ratio médio dos dois olhos (usado na detecção de piscada)."""
    pontos = face_recognition.face_landmarks(rgb, [local])
    if not pontos:
        return None
    return (_ear(pontos[0]["left_eye"]) + _ear(pontos[0]["right_eye"])) / 2.0


# ---------- 5. Classificação / Interpretação ----------
def classificar(encoding, base):
    """
    Compara o vetor com toda a base. Retorna (usuario_ou_None, menor_distancia).
    A decisão é: menor distância <= limiar.
    """
    vetores = np.array([b["vetor"] for b in base])
    distancias = face_recognition.face_distance(vetores, encoding)
    i = int(np.argmin(distancias))
    if distancias[i] <= config.LIMIAR_DISTANCIA:
        return base[i], float(distancias[i])
    return None, float(distancias[i])
