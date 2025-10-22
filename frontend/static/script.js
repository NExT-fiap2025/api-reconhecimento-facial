// Em static/script.js

// URLs da nossa API (backend rodando na porta 5000)
const API_URL_CADASTRAR = "http://127.0.0.1:5000/api/cadastrar";
const API_URL_VALIDAR = "http://127.0.0.1:5000/api/validar";

// Espera a página carregar completamente
document.addEventListener('DOMContentLoaded', () => {

    // Pega os elementos da página (HTML)
    const video = document.getElementById('video-feed');
    const canvas = document.getElementById('snapshot-canvas');
    const inputNome = document.getElementById('input-nome');
    const btnCadastrar = document.getElementById('btn-cadastrar');
    const btnValidar = document.getElementById('btn-validar');
    const statusMessage = document.getElementById('status-message');

    // --- 1. Inicializar a Webcam ---
    async function setupWebcam() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ 
                video: { width: 640, height: 480 },
                audio: false 
            });
            video.srcObject = stream;
            video.play();
            setStatus('info', 'Webcam iniciada. Pronto para ação.');
        } catch (err) {
            console.error("Erro ao acessar a webcam: ", err);
            setStatus('error', 'Não foi possível acessar a webcam.');
        }
    }

    // --- 2. Função para "Tirar Foto" (Capturar Frame) ---
    function capturarFrame() {
        // Ajusta o tamanho do canvas para o tamanho do vídeo
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        
        // "Desenha" o frame atual do vídeo no canvas
        const context = canvas.getContext('2d');
        
        // Espelha o canvas horizontalmente para corresponder à visualização do vídeo
        context.translate(canvas.width, 0);
        context.scale(-1, 1);
        
        context.drawImage(video, 0, 0, canvas.width, canvas.height);
        
        // Pega a imagem do canvas como Base64 no formato JPEG
        // O prefixo 'data:image/jpeg;base64,' já está incluído
        const dataUrl = canvas.toDataURL('image/jpeg', 0.8); // Qualidade de 80%
        
        // Remove o prefixo (apesar do seu backend já saber lidar, é boa prática)
        // return dataUrl.split(',')[1]; 
        
        // Vamos manter o prefixo, pois seu backend 'base64_para_imagem' modificado já trata isso
        return dataUrl;
    }

    // --- 3. Função para atualizar o Status ---
    function setStatus(type, message) {
        statusMessage.textContent = message;
        // Remove classes antigas e adiciona a nova
        statusMessage.className = 'status'; 
        statusMessage.classList.add(type);
    }

    // --- 4. Ação: Cadastrar Usuário ---
    async function cadastrarUsuario() {
        const nome = inputNome.value.trim();
        if (!nome) {
            setStatus('error', 'Por favor, digite um nome para cadastrar.');
            return;
        }

        setStatus('loading', `Cadastrando ${nome}...`);
        const imagemBase64 = capturarFrame();

        try {
            const response = await fetch(API_URL_CADASTRAR, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    nome_usuario: nome,
                    imagem_base64: imagemBase64
                })
            });

            const data = await response.json();

            if (response.status === 201) { // 201 Created
                setStatus('success', data.mensagem);
                inputNome.value = ''; // Limpa o campo
            } else {
                setStatus('error', `Erro: ${data.erro}`);
            }

        } catch (err) {
            console.error("Erro na requisição de cadastro: ", err);
            setStatus('error', 'Erro de conexão com a API. Verifique o console.');
        }
    }

    // --- 5. Ação: Validar Usuário (Login) ---
    async function validarUsuario() {
        setStatus('loading', 'Validando rosto...');
        const imagemBase64 = capturarFrame();

        try {
            const response = await fetch(API_URL_VALIDAR, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    imagem_base64: imagemBase64
                })
            });

            const data = await response.json();

            if (response.status === 200) { // 200 OK
                setStatus('success', `Bem-vindo, ${data.usuario}! (Dist: ${data.distancia.toFixed(4)})`);
            } else if (response.status === 404) { // 404 Not Found
                setStatus('error', `Usuário não reconhecido. (Dist: ${data.distancia.toFixed(4)})`);
            } else {
                setStatus('error', `Erro: ${data.erro}`);
            }

        } catch (err) {
            console.error("Erro na requisição de validação: ", err);
            setStatus('error', 'Erro de conexão com a API. Verifique o console.');
        }
    }

    // --- 6. Conectar Eventos aos Botões ---
    btnCadastrar.addEventListener('click', cadastrarUsuario);
    btnValidar.addEventListener('click', validarUsuario);

    // --- Iniciar tudo ---
    setupWebcam();
});