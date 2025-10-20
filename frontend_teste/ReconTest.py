import requests
import base64
import cv2, dlib, numpy as np, pickle, os, time

# --- URLs da API ---
API_URL_CADASTRAR = "http://127.0.0.1:5000/api/cadastrar"
API_URL_VALIDAR = "http://127.0.0.1:5000/api/validar" # <-- Nova URL

# Modelos necessários (ainda úteis para salvar localmente, se quisermos)
PREDICTOR = "shape_predictor_5_face_landmarks.dat"
RECOG = "dlib_face_recognition_resnet_model_v1.dat"
DB_FILE = "db.pkl" # <-- O DB LOCAL AGORA É OPCIONAL / CACHE
THRESH = 0.6

# Carrega banco de dados local (pode ser útil como fallback ou cache)
db = pickle.load(open(DB_FILE, "rb")) if os.path.exists(DB_FILE) else {}

# Inicializa detector e modelos
detector = dlib.get_frontal_face_detector()
sp = dlib.shape_predictor(PREDICTOR)
rec = dlib.face_recognition_model_v1(RECOG)

# Captura da webcam
cap = cv2.VideoCapture(0)
validando = False
nome_identificado = "Pressione V" # Variável para guardar o nome vindo da API

print("[C]=Cadastrar  [V]=Validar ON/OFF  [L]=Listar cadastrados  [X]=Excluir usuário  [S]=Sair")

# Variável global para o frame RGB
rgb = None

while True:
    ok, frame = cap.read()
    if not ok:
        break

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    rects = detector(rgb, 1)

    # --- LÓGICA DE VALIDAÇÃO VIA API ---
    if validando and len(rects) == 1: # Só valida se tiver UM rosto
        try:
            # 1. Converte o frame atual para Base64
            _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
            img_base64 = base64.b64encode(buffer).decode('utf-8')
            
            # 2. Monta o payload
            payload = {'imagem_base64': img_base64}

            # 3. Envia para a API de validação
            response = requests.post(API_URL_VALIDAR, json=payload, timeout=1.0) # Timeout curto

            # 4. Processa a resposta
            if response.status_code == 200: # 200 OK = Identificado
                dados_resposta = response.json()
                nome_identificado = dados_resposta.get('usuario', 'Erro API')
                distancia_api = dados_resposta.get('distancia', 999)
                print(f"API Identificou: {nome_identificado} (Dist: {distancia_api:.4f})") # Log no terminal
            elif response.status_code == 404: # 404 Not Found = Desconhecido
                nome_identificado = "Desconhecido"
                print("API: Desconhecido") # Log no terminal
            else: # Outros erros da API (ex: sem rosto na imagem)
                nome_identificado = "Erro API"
                print(f"API Erro: {response.status_code} - {response.text}") # Log no terminal

        except requests.RequestException as e:
            nome_identificado = "API Offline"
            print(f"Erro de Conexão com API Validação: {e}") # Log no terminal
            time.sleep(1) # Espera um pouco antes de tentar de novo

    elif not validando:
        nome_identificado = "Pressione V" # Reseta o nome quando sai do modo validação

    # --- DESENHO NA TELA ---
    # (Agora usa 'nome_identificado' vindo da API)
    for r in rects:
        # Define a cor baseado no resultado
        if nome_identificado == "Pressione V":
            color = (255, 0, 0) # Azul
        elif nome_identificado == "Desconhecido" or nome_identificado == "API Offline" or nome_identificado == "Erro API":
            color = (0, 0, 255) # Vermelho
        else: # Nome identificado!
            color = (0, 255, 0) # Verde

        cv2.rectangle(frame, (r.left(), r.top()), (r.right(), r.bottom()), color, 2)
        cv2.putText(frame, nome_identificado, (r.left(), r.top()-10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

    # Mostrar status do modo na tela
    status = "VALIDANDO" if validando else "OFF"
    cv2.putText(frame, status, (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)

    cv2.imshow("Reconhecimento Facial", frame)
    k = cv2.waitKey(1) & 0xFF

    # [S] = sair
    if k == ord('s'):
        break

    # [V] = alternar modo de validação
    if k == ord('v'):
        validando = not validando
        print("Validação via API:", "ON" if validando else "OFF")
        if not validando:
            nome_identificado = "Pressione V" # Limpa o nome ao desligar

    # --- [C] = CADASTRAR NOVO ROSTO ---
    # (Não muda - continua usando API_URL_CADASTRAR)
    if k == ord('c'):
        if len(rects) == 1:
            nome = input("Nome: ").strip()
            if nome:
                print(f"Preparando para cadastrar {nome}...")
                try:
                    _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
                    img_base64 = base64.b64encode(buffer).decode('utf-8')
                    payload = {'nome_usuario': nome,'imagem_base64': img_base64}
                    print(f"Enviando dados para a API em {API_URL_CADASTRAR}...")
                    response = requests.post(API_URL_CADASTRAR, json=payload, timeout=10.0)

                    if response.status_code == 201:
                        print(f"SUCESSO! API retornou: {response.json().get('mensagem')}")
                        # Atualização db local opcional
                        shape = sp(rgb, rects[0])
                        chip = dlib.get_face_chip(rgb, shape) # Linha corrigida
                        vec_local = np.array(rec.compute_face_descriptor(chip), dtype=np.float32)
                        db[nome] = vec_local.tolist() # Salva como lista no pkl local
                        pickle.dump(db, open(DB_FILE, "wb"))
                        print(f"Salvo também no 'db.pkl' local.")
                    else:
                        print(f"ERRO DA API: {response.status_code} - {response.text}")
                except requests.RequestException as e:
                    print(f"ERRO DE CONEXÃO: Não foi possível conectar à API. {e}")
        elif len(rects) == 0: print("Nenhum rosto detectado!")
        else: print("Muitos rostos detectados!")

    # [L] = listar cadastrados (Mostra o DB local)
    if k == ord('l'):
        print("Usuários cadastrados (local 'db.pkl'):", list(db.keys()) if db else "Nenhum.")

    # [X] = excluir usuário (Só apaga do DB local)
    if k == ord('x'):
        # ... (código original de exclusão local) ...
         if not db: print("Nenhum usuário local para excluir.")
         else:
             print("Usuários locais:", list(db.keys()))
             nome = input("Digite o nome do usuário local para excluir: ").strip()
             if nome in db:
                 del db[nome]; pickle.dump(db, open(DB_FILE, "wb"))
                 print(f"Usuário {nome} removido do 'db.pkl' local.")
             else: print(f"Usuário {nome} não encontrado no 'db.pkl' local.")

cap.release()
cv2.destroyAllWindows()