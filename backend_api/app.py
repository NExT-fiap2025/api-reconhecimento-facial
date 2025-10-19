from flask import Flask, request, jsonify
import dlib
import numpy as np
import os # Já deve estar aqui
import cv2
import base64
import pickle # <-- Adicionar esta importação

# --- Configuração Inicial ---
print("Carregando modelos do dlib...")
APP_ROOT = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(APP_ROOT, 'models')
PREDICTOR_PATH = os.path.join(MODELS_DIR, "shape_predictor_5_face_landmarks.dat")
RECOG_PATH = os.path.join(MODELS_DIR, "dlib_face_recognition_resnet_model_v1.dat")
detector = dlib.get_frontal_face_detector()
sp = dlib.shape_predictor(PREDICTOR_PATH)
rec = dlib.face_recognition_model_v1(RECOG_PATH)
print("Modelos carregados.")

# --- Banco de Dados com Arquivo ---
DB_FILE_PATH = os.path.join(APP_ROOT, "usuarios_cadastrados.pkl") # Nome do arquivo

# Função para carregar o banco de dados do arquivo
def carregar_db():
    if os.path.exists(DB_FILE_PATH):
        print(f"Carregando banco de dados de {DB_FILE_PATH}...")
        try:
            with open(DB_FILE_PATH, "rb") as f:
                return pickle.load(f)
        except Exception as e:
            print(f"Erro ao carregar {DB_FILE_PATH}: {e}. Criando um novo DB.")
            return {}
    else:
        print("Arquivo de banco de dados não encontrado. Criando um novo.")
        return {}

# Função para salvar o banco de dados no arquivo
def salvar_db(db_obj):
    print(f"Salvando banco de dados em {DB_FILE_PATH}...")
    try:
        with open(DB_FILE_PATH, "wb") as f:
            pickle.dump(db_obj, f)
    except Exception as e:
        print(f"Erro ao salvar {DB_FILE_PATH}: {e}")

# Carrega o DB ao iniciar a aplicação
db_usuarios = carregar_db()
print(f"DB carregado. Usuários existentes: {list(db_usuarios.keys())}")

# Cria a nossa aplicação Flask
app = Flask(__name__)

# --- Funções Auxiliares (base64_para_imagem, extrair_vetor_facial) ---
# (NÃO MUDAM - Mantenha as funções como estavam)
def base64_para_imagem(string_base64):
    # ... (código igual)
    try:
        if "," in string_base64:
            cabecalho, dados_img = string_base64.split(',', 1)
        else:
            dados_img = string_base64
        bytes_decodificados = base64.b64decode(dados_img)
        array_np = np.frombuffer(bytes_decodificados, np.uint8)
        img = cv2.imdecode(array_np, cv2.IMREAD_COLOR)
        return img
    except Exception as e:
        print(f"Erro ao decodificar imagem: {e}")
        return None

def extrair_vetor_facial(img):
     # ... (código igual)
    try:
        rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        rects = detector(rgb, 1)
        if len(rects) != 1:
            print(f"Erro: Encontrados {len(rects)} rostos. Esperado 1.")
            return None
        shape = sp(rgb, rects[0])
        chip = dlib.get_face_chip(rgb, shape)
        vec = rec.compute_face_descriptor(chip)
        return np.array(vec, dtype=np.float32).tolist()
    except Exception as e:
        print(f"Erro ao extrair vetor: {e}")
        return None


# --- ENDPOINT DE CADASTRO (MODIFICADO PARA SALVAR) ---
@app.route('/api/cadastrar', methods=['POST'])
def cadastrar_usuario():
    print("\n--- Recebida requisição em /api/cadastrar ---")
    dados = request.get_json()

    if not dados or 'nome_usuario' not in dados or 'imagem_base64' not in dados:
        return jsonify({'erro': 'Dados incompletos.'}), 400

    nome = dados['nome_usuario']
    img_b64 = dados['imagem_base64']

    # Usa o 'db_usuarios' global que foi carregado
    if nome in db_usuarios:
        return jsonify({'erro': f'Usuario {nome} ja existe.'}), 409

    print(f"Processando imagem para: {nome}")
    imagem = base64_para_imagem(img_b64)
    if imagem is None:
        return jsonify({'erro': 'Formato de imagem Base64 invalido.'}), 400

    vetor_facial = extrair_vetor_facial(imagem)
    if vetor_facial is None:
        return jsonify({'erro': 'Nao foi possivel detectar um (e apenas um) rosto na imagem.'}), 400

    # 1. Atualiza o dicionário em memória
    db_usuarios[nome] = vetor_facial
    
    # 2. Salva o dicionário ATUALIZADO no arquivo!
    salvar_db(db_usuarios) 
    
    print(f"Sucesso! Usuario {nome} cadastrado.")
    print(f"Vetor (primeiros 5): {vetor_facial[:5]}...")
    print(f"Total de usuários no DB: {len(db_usuarios)}")
    
    return jsonify({
        'status': 'sucesso',
        'mensagem': f'Usuario {nome} cadastrado com sucesso.'
    }), 201


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)