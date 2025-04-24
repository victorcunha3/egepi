import os
import pandas as pd
import google.generativeai as genai
from dotenv import load_dotenv
import streamlit as st
import time
import warnings

# Suprimir avisos específicos
warnings.filterwarnings('ignore', category=UserWarning, message='.*value \d+\.\d+ is outside the limits for dates.*')

# Configuração inicial
load_dotenv()

GOOGLE_API_KEY = 'AIzaSyBh3w-eU2MMjVX8cUOkl1UQhd01Ehsa-Ew'
if not GOOGLE_API_KEY:
    raise ValueError("Por favor, defina a variável de ambiente GOOGLE_API_KEY")

genai.configure(api_key=GOOGLE_API_KEY)

# Configuração do modelo
generation_config = {
    "temperature": 0.5,
    "top_p": 1,
    "top_k": 1,
    "max_output_tokens": 1000000,
}

safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
]

def load_model():
    return genai.GenerativeModel(
        model_name="gemini-2.5-pro-exp-03-25",
        generation_config=generation_config,
        safety_settings=safety_settings
    )

model = load_model()
# Função para carregar dados com tratamento de erros
st.cache_data()
def carregar_dados(caminho_arquivo):
    try:
        # Configurar pandas para ignorar avisos de datas
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=UserWarning)

            # Tentar ler o arquivo com engine openpyxl que lida melhor com formatos
            try:
                todas_planilhas = pd.read_excel(caminho_arquivo, sheet_name=None, engine='openpyxl')
            except:
                # Se falhar, tentar com engine padrão
                todas_planilhas = pd.read_excel(caminho_arquivo, sheet_name=None)

            dados_processados = {}

            for nome_planilha, dados in todas_planilhas.items():
                # Corrigir codificação
                dados.columns = dados.columns.str.replace('Ã§', 'ç')
                dados.columns = dados.columns.str.replace('Ã£', 'ã')
                dados.columns = dados.columns.str.replace('Ã¡', 'á')
                dados.columns = dados.columns.str.replace('Ã©', 'é')
                dados.columns = dados.columns.str.replace('Ãº', 'ú')
                dados.columns = dados.columns.str.replace('Ã', 'í')
                dados.columns = dados.columns.str.replace('Â', '')

                # Converter colunas de data se necessário
                for col in dados.columns:
                    if 'data' in col.lower() or 'date' in col.lower():
                        try:
                            dados[col] = pd.to_datetime(dados[col], errors='coerce')
                        except:
                            pass

                dados_processados[nome_planilha] = dados

            return dados_processados
    except Exception as e:
        st.error(f"Erro ao carregar o arquivo: {str(e)}")
        return None

rota_arquivo = r"C:\Users\victo\Downloads\Base de Dados Agente IA EGEPI (1).xlsx"
# [Mantenha todas as importações e configurações iniciais como estão...]

# Inicialização do Streamlit
st.set_page_config(page_title="Agente I.A de Consultas em Cursos", page_icon=":books:")
senha_usuario = 'egepi1@1'

# Sidebar com configurações
with st.sidebar:
    st.title("Configurações")
    # senha = st.text_input('Digite a senha')

    # if st.button("Carregar Dados") and senha_usuario == senha:
    with st.spinner("Carregando dados..."):
        st.session_state.todas_planilhas = carregar_dados(rota_arquivo)
        if st.session_state.todas_planilhas is not None:
            st.success("Dados carregados com sucesso!")

            # Prepara a string com informações de todas as planilhas
            dados_str = ""
            for nome_planilha, dados in st.session_state.todas_planilhas.items():
                dados_str += f"\n\n=== Dados da planilha '{nome_planilha}' ===\n"
                dados_str += dados.head(1000).to_string()

            # Inicializa o histórico da conversa (para o modelo Gemini)
            st.session_state.historico_gemini = [
                {
                    "role": "user",
                    "parts": [f"""Você é um assistente especializado em responder perguntas sobre inscrições em cursos. 
                    Use apenas as informações da base de dados fornecida. Se não souber a resposta, diga que não tem informações suficientes.

                    Aqui está um exemplo da estrutura dos dados de todas as planilhas:
                    {dados_str}

                    As principais planilhas e suas colunas são:

                    Planilha 1 (Dados dos Cursos):
                    id_curso: Código único do evento.
                    data_inicio: Data de início do curso.
                    data_fim: Data de término do curso.
                    evento: Nome do curso/evento.
                    numero_processo_SEI: Número do processo no SEI.
                    formato: Abordagem pedagógica.
                    eixo: Área temática do curso.
                    local_realizacao: Local físico ou virtual do evento.
                    instrutor: Nome(s) do(s) instrutor(es).
                    valor_instrutor: Valor total pago ao(s) instrutor(es).
                    carga_horaria_instrutor: Horas dedicadas por instrutor (ordem igual à "instrutor") Exemplo: Ex: 8, 12 (Joselito: 8h, Alexandre: 12h).
                    valor_material: Custo de materiais didáticos.
                    turno: Período de realização.
                    carga_horaria: Duração total do curso.
                    gerencia: Gerência responsável.

                    Planilha 2 (Dados dos Participantes):
                    - [lista de colunas importantes]
                    - [outras colunas relevantes...]

                    Planilha 2 (Dados dos Orgãos):
                    - [lista de colunas importantes]
                    - [outras colunas relevantes...]

                    IMPORTANTE: 
                    1. Nunca revele informações pessoais completas como CPF ou e-mail. 
                    2. Consulte os dados de todas as planilhas para responder perguntas.
                    3. Se precisar cruzar informações entre planilhas, faça isso cuidadosamente.
                    4. Se precisar se referir a uma pessoa, use apenas o primeiro nome ou iniciais."""]
                },
                {
                    "role": "model",
                    "parts": [
                        "Entendido! Sou um assistente especializado em consultas sobre inscrições em cursos. Posso ajudar com informações sobre participantes, cursos, status de inscrição e outras informações relevantes da base de dados, sempre protegendo dados pessoais. Como posso ajudar?"]
                }
            ]

            # Inicializa as mensagens do chat (para exibição na interface)
            if "messages" not in st.session_state:
                st.session_state.messages = [
                    {"role": "assistant", "content": "Dados carregados com sucesso! Como posso ajudar você hoje?"}
                ]

# Título da aplicação
st.title("💬 Agente de I.A de Consultas em Cursos")
st.caption("🚀 Um assistente virtual para responder perguntas sobre inscrições em cursos")

# Exibe todas as mensagens do chat (histórico completo)
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Input do usuário
if prompt := st.chat_input("Digite sua pergunta sobre cursos"):
    # Verifica se os dados foram carregados
    if "todas_planilhas" not in st.session_state:
        with st.chat_message("assistant"):
            st.error("Por favor, carregue os dados na barra lateral primeiro.")
        st.stop()

    # Adiciona a mensagem do usuário ao chat
    with st.chat_message("user"):
        st.markdown(prompt)

    # Adiciona a mensagem ao histórico de exibição
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Adiciona a pergunta ao histórico do modelo Gemini
    st.session_state.historico_gemini.append({"role": "user", "parts": [prompt]})

    # Resposta do assistente
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""

        try:
            # Envia o histórico completo para o modelo
            with st.spinner("Pensando..."):
                resposta = model.generate_content(st.session_state.historico_gemini)

            # Adiciona a resposta ao histórico do Gemini
            resposta_texto = resposta.text
            st.session_state.historico_gemini.append({"role": "model", "parts": [resposta_texto]})

            # Simula digitação
            for chunk in resposta_texto.split():
                full_response += chunk + " "
                time.sleep(0.05)
                message_placeholder.markdown(full_response + "▌")
            message_placeholder.markdown(full_response)

        except Exception as e:
            full_response = f"⚠️ Ocorreu um erro ao processar sua pergunta: {str(e)}"
            message_placeholder.markdown(full_response)

    # Adiciona a resposta ao histórico de exibição
    st.session_state.messages.append({"role": "assistant", "content": full_response})