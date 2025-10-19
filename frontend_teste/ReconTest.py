# Certifique-se que estas importações estão no topo
import requests
import base64
import cv2, dlib, numpy as np, pickle, os, time

# --- Defina a URL da sua API ---
API_URL = "http://127.0.0.1:5000/api/cadastrar"

# Modelos necessários (precisam estar na pasta do projeto)
PREDICTOR = "shape_predictor_5_face_landmarks.dat"
RECOG = "dlib_face_recognition_resnet_model_v1.dat"
DB_FILE = "db.pkl"
THRESH = 0.6  # Limite de similaridade

# Carrega banco de dados local
db = pickle.load(open(DB_FILE, "rb")) if os.path.exists(DB_FILE) else {}

# Inicializa detector e modelos
detector = dlib.get_frontal_face_detector()
sp = dlib.shape_predictor(PREDICTOR)
rec = dlib.face_recognition_model_v1(RECOG)

# Captura da webcam
cap = cv2.VideoCapture(0)
validando = False

print("[C]=Cadastrar  [V]=Validar ON/OFF  [L]=Listar cadastrados  [X]=Excluir usuário  [S]=Sair")

# Variável global para o frame RGB
rgb = None

while True:
    ok, frame = cap.read() # 'frame' é a imagem que vamos enviar
    if not ok:
        break

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB) # Atualiza o frame RGB
    rects = detector(rgb, 1)

    for r in rects:
        # --- Validação --- (Seu código original de validação)
        if validando and db:
            shape = sp(rgb, r)
            chip = dlib.get_face_chip(rgb, shape)
            vec = np.array(rec.compute_face_descriptor(chip), dtype=np.float32)
            
            nome, dist = "Desconhecido", 999
            for n, v in db.items():
                d = np.linalg.norm(vec - v)
                if d < dist:
                    nome, dist = n, d
            if dist > THRESH:
                nome = "Desconhecido"

            # Caixa e texto
            color = (0, 255, 0) if nome != "Desconhecido" else (0, 0, 255)
            cv2.rectangle(frame, (r.left(), r.top()), (r.right(), r.bottom()), color, 2)
            cv2.putText(frame, nome, (r.left(), r.top()-10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
        else:
             # Apenas desenha o retângulo se não estiver validando
            cv2.rectangle(frame, (r.left(), r.top()), (r.right(), r.bottom()), (255, 0, 0), 2)

    # Mostrar status do modo na tela
    status = "ON" if validando else "OFF"
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
        print("Validação:", "ON" if validando else "OFF")

    # --- [C] = CADASTRAR NOVO ROSTO (ESTE É O BLOCO NOVO) ---
    if k == ord('c'):
        # Só cadastra se tiver UM rosto detectado
        if len(rects) == 1: 
            nome = input("Nome: ").strip()
            if nome:
                
                print(f"Preparando para cadastrar {nome}...")
                
                try:
                    # 1. Converte a imagem (frame) para o formato JPEG em memória
                    _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
                    
                    # 2. Codifica a imagem JPEG para Base64
                    img_base64 = base64.b64encode(buffer).decode('utf-8')
                    
                    # 3. Monta o payload (o JSON que a API espera)
                    payload = {
                        'nome_usuario': nome,
                        'imagem_base64': img_base64
                    }

                    # 4. Envia a requisição POST para a API
                    print(f"Enviando dados para a API em {API_URL}...")
                    response = requests.post(API_URL, json=payload, timeout=10.0)

                    # 5. Processa a resposta da API
                    if response.status_code == 201: # 201 = Created
                        print(f"SUCESSO! API retornou: {response.json().get('mensagem')}")
                        
                        # --- ATUALIZAÇÃO OPCIONAL DO DB LOCAL ---
                        # (Opcional, mas bom para a tecla [V] funcionar)
                        shape = sp(rgb, rects[0])
                        chip = dlib.get_face_chip(rgb, shape)
                        vec_local = np.array(rec.compute_face_descriptor(chip), dtype=np.float32)
                        
                        db[nome] = vec_local
                        pickle.dump(db, open(DB_FILE, "wb"))
                        print(f"Salvo também no 'db.pkl' local para validação.")
                        # --- FIM DA ATUALIZAÇÃO ---

                    else:
                        # Mostra erros que a API retornou (ex: "rosto não detectado", "usuário já existe")
                        print(f"ERRO DA API: {response.status_code} - {response.text}")
                
                except requests.RequestException as e:
                    # Mostra erros de conexão (ex: API desligada)
                    print(f"ERRO DE CONEXÃO: Não foi possível conectar à API. {e}")

        elif len(rects) == 0:
            print("Nenhum rosto detectado para cadastrar!")
        else:
            print("Muitos rostos detectados! Posicione apenas UM rosto para cadastrar.")
    # --- FIM DO BLOCO [C] ---

    # [L] = listar cadastrados
    if k == ord('l'):
        print("Usuários cadastrados (local 'db.pkl'):", list(db.keys()) if db else "Nenhum usuário cadastrado.")

    # [X] = excluir usuário
    if k == ord('x'):
        if not db:
            print("Nenhum usuário cadastrado para excluir.")
        else:
            print("Usuários cadastrados:", list(db.keys()))
            nome = input("Digite o nome do usuário para excluir: ").strip()
            if nome in db:
                del db[nome]
                pickle.dump(db, open(DB_FILE, "wb"))
                print(f"Usuário {nome} removido do 'db.pkl' local.")
            else:
                print(f"Usuário {nome} não encontrado no 'db.pkl' local.")
                
cap.release()
cv2.destroyAllWindows()