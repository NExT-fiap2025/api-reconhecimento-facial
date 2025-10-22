from flask import Flask, request, jsonify
from flask_cors import CORS
import dlib
import numpy as np
import os
import cv2
import base64
import pickle

# --- Configuração Inicial ---
# (Carregamento dos modelos .dat continua igual)
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
# (Funções carregar_db e salvar_db continuam iguais)
DB_FILE_PATH = os.path.join(APP_ROOT, "usuarios_cadastrados.pkl")

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

def salvar_db(db_obj):
    print(f"Salvando banco de dados em {DB_FILE_PATH}...")
    try:
        with open(DB_FILE_PATH, "wb") as f:
            pickle.dump(db_obj, f)
    except Exception as e:
        print(f"Erro ao salvar {DB_FILE_PATH}: {e}")

db_usuarios = carregar_db()
print(f"DB carregado. Usuários existentes: {list(db_usuarios.keys())}")

# --- Constante de Similaridade ---
# (Igual ao seu script original)
THRESH = 0.6

# Cria a nossa aplicação Flask
app = Flask(__name__)
CORS(app)

# --- Funções Auxiliares ---
# (base64_para_imagem e extrair_vetor_facial continuam iguais)
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
        # IMPORTANTE: Retornar como array numpy para facilitar o cálculo da distância
        return np.array(vec, dtype=np.float32)
    except Exception as e:
        print(f"Erro ao extrair vetor: {e}")
        return None

# --- Endpoint de Cadastro ---
# (Continua igual, mas agora chama salvar_db)
@app.route('/api/cadastrar', methods=['POST'])
def cadastrar_usuario():
    # ... (código igual)
    print("\n--- Recebida requisição em /api/cadastrar ---")
    dados = request.get_json()

    if not dados or 'nome_usuario' not in dados or 'imagem_base64' not in dados:
        return jsonify({'erro': 'Dados incompletos.'}), 400

    nome = dados['nome_usuario']
    img_b64 = dados['imagem_base64']

    if nome in db_usuarios:
        return jsonify({'erro': f'Usuario {nome} ja existe.'}), 409

    print(f"Processando imagem para: {nome}")
    imagem = base64_para_imagem(img_b64)

    if imagem is None and "," in img_b64:
        try:
            # Tenta decodificar de novo, pulando o prefixo
            img_b64_sem_prefixo = img_b64.split(',', 1)[1]
            imagem = base64_para_imagem(img_b64_sem_prefixo)
        except Exception as e:
            print(f"Erro ao tentar splitar o base64: {e}")
            pass # Deixa o 'if' de baixo tratar como erro
    
    if imagem is None:
        return jsonify({'erro': 'Formato de imagem Base64 invalido.'}), 400

    # Extrai o vetor como lista para salvar
    vetor_facial_lista = extrair_vetor_facial(imagem)
    if vetor_facial_lista is None:
        return jsonify({'erro': 'Nao foi possivel detectar um (e apenas um) rosto na imagem.'}), 400
    
    # Converte para lista antes de salvar
    db_usuarios[nome] = vetor_facial_lista.tolist()
    salvar_db(db_usuarios)
    
    print(f"Sucesso! Usuario {nome} cadastrado.")
    print(f"Vetor (primeiros 5): {vetor_facial_lista[:5]}...")
    print(f"Total de usuários no DB: {len(db_usuarios)}")
    
    return jsonify({
        'status': 'sucesso',
        'mensagem': f'Usuario {nome} cadastrado com sucesso.'
    }), 201


# --- NOVO ENDPOINT DE VALIDAÇÃO ---
@app.route('/api/validar', methods=['POST'])
def validar_usuario():
    print("\n--- Recebida requisição em /api/validar ---")
    dados = request.get_json()

    # 1. Validação básica: Só precisa da imagem
    if not dados or 'imagem_base64' not in dados:
        return jsonify({'erro': 'Dados incompletos. Faltando imagem_base64'}), 400

    img_b64 = dados['imagem_base64']

    # 2. Processa a imagem e extrai o vetor
    print("Processando imagem para validação...")
    imagem = base64_para_imagem(img_b64)

    if imagem is None and "," in img_b64:
        try:
            # Tenta decodificar de novo, pulando o prefixo
            img_b64_sem_prefixo = img_b64.split(',', 1)[1]
            imagem = base64_para_imagem(img_b64_sem_prefixo)
        except Exception as e:
            print(f"Erro ao tentar splitar o base64: {e}")
            pass # Deixa o 'if' de baixo tratar como erro

    if imagem is None:
        return jsonify({'erro': 'Formato de imagem Base64 invalido.'}), 400

    vetor_atual = extrair_vetor_facial(imagem) # Retorna numpy array
    if vetor_atual is None:
        return jsonify({'erro': 'Nao foi possivel detectar um (e apenas um) rosto na imagem.'}), 400

    # 3. Compara com o banco de dados
    nome_identificado = "Desconhecido"
    menor_distancia = 999.0

    # Recarrega o DB caso tenha sido atualizado por outro processo (pouco provável aqui, mas boa prática)
    db_atualizado = carregar_db()

    for nome_db, vetor_db_lista in db_atualizado.items():
        # Converte o vetor do DB (lista) de volta para numpy array
        vetor_db = np.array(vetor_db_lista, dtype=np.float32)

        # Calcula a distância Euclidiana
        dist = np.linalg.norm(vetor_atual - vetor_db)
        
        print(f"Comparando com {nome_db}. Distância: {dist:.4f}")

        if dist < menor_distancia:
            menor_distancia = dist
            if dist < THRESH: # Se a menor distância encontrada ATÉ AGORA já é boa...
                nome_identificado = nome_db

    # 4. Retorna o resultado
    if nome_identificado != "Desconhecido":
        print(f"Usuário identificado: {nome_identificado} (Distância: {menor_distancia:.4f})")
        return jsonify({
            'status': 'sucesso',
            'identificado': True,
            'usuario': nome_identificado,
            'distancia': float(menor_distancia)
        }), 200 # 200 OK
    else:
        print(f"Usuário não identificado. Menor distância encontrada: {menor_distancia:.4f}")
        return jsonify({
            'status': 'nao_encontrado',
            'identificado': False,
            'usuario': None,
            'distancia': float(menor_distancia)
        }), 404 # 404 Not Found

@app.route('/api/admin/usuarios', methods=['GET'])
def listar_usuarios():
    """ Retorna uma lista com os nomes de todos os usuários cadastrados. """
    print("--- Recebida requisição em /api/admin/usuarios ---")
    
    # db_usuarios é o seu dicionário carregado no início do script
    lista_nomes = list(db_usuarios.keys())
    
    print(f"Retornando {len(lista_nomes)} usuários.")
    return jsonify({'status': 'sucesso', 'usuarios': lista_nomes}), 200

@app.route('/api/admin/excluir/<string:nome_usuario>', methods=['DELETE'])
def excluir_usuario(nome_usuario):
    """ Exclui um usuário específico do banco de dados. """
    print(f"--- Recebida requisição DELETE para /api/admin/excluir/{nome_usuario} ---")
    
    if nome_usuario in db_usuarios:
        # Exclui o usuário do dicionário
        del db_usuarios[nome_usuario]
        
        # Salva as mudanças no arquivo .pkl
        salvar_db(db_usuarios)
        
        print(f"Usuário {nome_usuario} excluído com sucesso.")
        return jsonify({
            'status': 'sucesso',
            'mensagem': f'Usuario {nome_usuario} foi excluido.'
        }), 200
    else:
        # Se o usuário não existe
        print(f"Usuário {nome_usuario} não encontrado para exclusão.")
        return jsonify({
            'erro': 'Usuario nao encontrado.'
        }), 404


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)