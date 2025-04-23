import cv2

# ----------- Função de Melhoria de Imagem -----------

def aplicar_clahe(imagem_path):
    imagem_bgr = cv2.imread(imagem_path)
    lab = cv2.cvtColor(imagem_bgr, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    cl = clahe.apply(l)
    limg = cv2.merge((cl, a, b))
    final = cv2.cvtColor(limg, cv2.COLOR_LAB2RGB)
    return final