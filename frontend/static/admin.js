// Em frontend_teste/static/admin.js

// URLs da nossa API (backend rodando na porta 5000)
const API_URL_LISTAR = "http://127.0.0.1:5000/api/admin/usuarios";
const API_URL_EXCLUIR_BASE = "http://127.0.0.1:5000/api/admin/excluir"; // O nome será adicionado no final

// Espera a página carregar
document.addEventListener('DOMContentLoaded', () => {

    // Pega os elementos da página
    const btnAtualizar = document.getElementById('btn-atualizar');
    const listaUsuarios = document.getElementById('lista-usuarios');
    const statusAdmin = document.getElementById('status-admin');

    // --- 1. Função para atualizar o Status ---
    function setStatus(type, message) {
        statusAdmin.textContent = message;
        statusAdmin.className = 'status'; 
        statusAdmin.classList.add(type);
    }

    // --- 2. Função para Excluir Usuário ---
    async function excluirUsuario(event) {
        // Pega o nome que foi salvo no atributo 'data-nome' do botão
        const nomeParaExcluir = event.target.dataset.nome;

        if (!nomeParaExcluir) return;

        // Pede confirmação
        if (!confirm(`Tem certeza que deseja excluir o usuário: ${nomeParaExcluir}?`)) {
            return;
        }
        
        setStatus('loading', `Excluindo ${nomeParaExcluir}...`);

        try {
            const response = await fetch(`${API_URL_EXCLUIR_BASE}/${nomeParaExcluir}`, {
                method: 'DELETE'
            });

            const data = await response.json();

            if (response.status === 200) {
                setStatus('success', data.mensagem);
                // Após excluir, atualiza a lista automaticamente
                carregarUsuarios(); 
            } else {
                setStatus('error', `Erro: ${data.erro}`);
            }

        } catch (err) {
            console.error("Erro na requisição de exclusão: ", err);
            setStatus('error', 'Erro de conexão com a API.');
        }
    }

    // --- 3. Função Principal: Carregar e Listar Usuários ---
    async function carregarUsuarios() {
        setStatus('loading', 'Carregando usuários...');
        listaUsuarios.innerHTML = ''; // Limpa a lista antiga

        try {
            const response = await fetch(API_URL_LISTAR);
            const data = await response.json();

            if (response.status !== 200 || data.status !== 'sucesso') {
                setStatus('error', data.erro || 'Falha ao carregar lista.');
                return;
            }

            if (data.usuarios.length === 0) {
                setStatus('info', 'Nenhum usuário cadastrado no momento.');
                return;
            }

            // Para cada usuário na lista, cria um item <li>
            data.usuarios.forEach(nome => {
                const li = document.createElement('li');
                
                const spanNome = document.createElement('span');
                spanNome.textContent = nome;
                
                const btnExcluir = document.createElement('button');
                btnExcluir.textContent = 'Excluir';
                // IMPORTANTE: Guarda o nome do usuário no próprio botão
                btnExcluir.dataset.nome = nome; 
                
                // Adiciona o evento de clique para este botão específico
                btnExcluir.addEventListener('click', excluirUsuario);
                
                li.appendChild(spanNome);
                li.appendChild(btnExcluir);
                listaUsuarios.appendChild(li);
            });

            setStatus('success', `Carregados ${data.usuarios.length} usuários.`);

        } catch (err) {
            console.error("Erro na requisição de listar: ", err);
            setStatus('error', 'Erro de conexão com a API. Verifique o console.');
        }
    }

    // --- 4. Conectar Eventos ---
    btnAtualizar.addEventListener('click', carregarUsuarios);
    
    // Carrega a lista assim que a página abre
    carregarUsuarios();
});