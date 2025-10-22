# 🧑‍💻 Sistema de Autenticação Facial (API + Web Interface)

## 📌 Integrantes (Exemplo)

- [Seu Nome Aqui] - [Sua Matrícula/ID]
- [Nome Outro Integrante] - [Matrícula/ID]
- ...

*(Substitua pelos nomes e IDs reais)*

## ▶️ Vídeo Explicativo (Opcional)

- [Link para o vídeo, se houver](https://...)

## 📌 Objetivo

Este projeto implementa um sistema de **autenticação facial** utilizando **Flask**, **OpenCV** e **Dlib**. Ele é dividido em duas partes principais:

1.  **Backend (API Rest):**
    * Construído com Flask, rodando na porta `5000`.
    * Responsável por:
        * Receber imagens (em Base64) do frontend.
        * Processar imagens usando Dlib/OpenCV para extrair características faciais.
        * **Cadastrar** novos usuários (salvando as características em `usuarios_cadastrados.pkl`).
        * **Validar** rostos comparando com os cadastrados.
        * Oferecer endpoints administrativos para **listar** e **excluir** usuários.

2.  **Frontend (Web Application):**
    * Construído com Flask, rodando na porta `5001`.
    * Responsável por:
        * Servir a interface web para o navegador do usuário.
        * Acessar a webcam do usuário via JavaScript.
        * Capturar frames da webcam.
        * Enviar as imagens capturadas (em Base64) para a API Backend.
        * Exibir os resultados (sucesso/falha no cadastro/login, mensagens de erro).
        * Oferecer uma página de **administração** (`/admin`) para gerenciar usuários (listar/excluir).

O banco de dados de características faciais (`usuarios_cadastrados.pkl`) é gerenciado exclusivamente pelo backend.

---

## ⚙️ Dependências

O projeto possui dois ambientes virtuais separados. Você precisará instalar as dependências em cada um deles.

**1. Dependências do Backend:**

Navegue até a pasta `backend_api`, ative o ambiente virtual e instale:

```bash
cd backend_api
source venv/bin/activate
# pip install Flask Flask-Cors dlib opencv-python numpy
deactivate
cd ..
```

**2. Dependências do Frontend:**

Navegue até a pasta frontend, ative o ambiente virtual e instale:

```bash
cd frontend
source venv/bin/activate
# Se não tiver o requirements.txt, use:
# pip install Flask
deactivate
cd ..
```

**Modelos Necessários (Dlib)**



    Para detecção de landmarks:

        Baixe: shape_predictor_5_face_landmarks.dat.bz2

    Para reconhecimento facial (gerar embeddings):

        Baixe: dlib_face_recognition_resnet_model_v1.dat.bz2

## 🔹 Modelos necessários

O backend utiliza modelos pré-treinados do dlib para detecção e reconhecimento facial. Eles não estão incluídos no repositório devido ao tamanho.

Você precisa baixar manualmente os seguintes arquivos e colocá-los na pasta backend_api/models/:

projeto**.

-   [shape_predictor_5\_face_landmarks.dat.bz2](http://dlib.net/files/shape_predictor_5_face_landmarks.dat.bz2)\
-   [dlib_face_recognition_resnet_model_v1.dat.bz2](http://dlib.net/files/dlib_face_recognition_resnet_model_v1.dat.bz2)\

Após o download, descompacte os arquivos:

``` bash
bzip2 -d nome_do_arquivo.bz2
```
E mova os arquivos .dat resultantes para a pasta backend_api/models/.

## ▶️ Execução

Para rodar o projeto:

**Terminal 1: Iniciar o Backend (API)**

```bash
cd backend_api
source venv/bin/activate
python app.py
# O backend estará rodando em [http://127.0.0.1:5000](http://127.0.0.1:5000)
```

**Terminal 2: Iniciar o Frontend (Web App)**

```bash
cd frontend
source venv/bin/activate
python web_frontend.py
# O frontend estará rodando em [http://127.0.0.1:5001](http://127.0.0.1:5001)
```

**Acessando a Aplicação:**

    Abra seu navegador.

    Acesse http://127.0.0.1:5001/ para a página de Login/Cadastro.

    Acesse http://127.0.0.1:5001/admin para o Painel de Administração.



⚡ Parâmetros Importantes (no backend_api/app.py)

  -THRESH = 0.6:

    -Define a tolerância de similaridade (distância Euclidiana) entre os vetores faciais.

        Valores menores tornam o sistema mais rigoroso (exige rostos mais parecidos).

        Valores maiores tornam o sistema mais permissivo.

        O valor 0.6 é um padrão comum, ajuste conforme necessário.
        
