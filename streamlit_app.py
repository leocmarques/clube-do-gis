import streamlit as st
from hotmart_python import Hotmart
import logging
from datetime import datetime
import hmac
import pandas as pd
import requests


def check_password():
    """Returns `True` if the user had the correct password."""

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if hmac.compare_digest(st.session_state["password"], st.secrets["password"]):
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Don't store the password.
        else:
            st.session_state["password_correct"] = False

    # Return True if the password is validated.
    if st.session_state.get("password_correct", False):
        return True

    # Show input for password.
    st.text_input(
        "Password", type="password", on_change=password_entered, key="password"
    )
    if "password_correct" in st.session_state:
        st.error("😕 Password incorrect")
    return False


if not check_password():
    st.stop()  # Do not continue if check_password is not True.

# Main Streamlit app starts here

# Obtém credenciais da API do Streamlit Secrets
CLIENT_ID = st.secrets["CLIENT_ID"]
CLIENT_SECRET = st.secrets["CLIENT_SECRET"]
BASIC_TOKEN = st.secrets["BASIC_TOKEN"]

# Inicialização do cliente Hotmart com nível de log INFO
hotmart = Hotmart(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    basic=BASIC_TOKEN,
    log_level=logging.INFO
)

# Função para converter timestamp
def converter_timestamp(timestamp_ms):
    try:
        timestamp_s = timestamp_ms / 1000
        return datetime.fromtimestamp(int(timestamp_s)).strftime("%d/%m/%Y-%H:%M")
    except (TypeError, ValueError):
        return "Data não disponível"

# Função para buscar informações do comprador
def buscar_informacoes_comprador(email, participantes):
    try:
        # Percorre os participantes para buscar o comprador (BUYER)
        for participante in participantes:
            users = participante.get("users", [])
            for user_data in users:
                if user_data.get("role") == "BUYER" and user_data["user"]["email"] == email:
                    return user_data["user"]
        return None
    except Exception as e:
        st.error(f"Erro ao processar informações do comprador: {e}")
        return None


# Título do aplicativo
st.title("Dashboard Geral")

# Abas do aplicativo
tabs = st.tabs(["Hotmart", "Curseduca", "Google Sheets"])

# Conteúdo da aba "Hotmart"
with tabs[0]:
    st.header("Consulta de Compras na Hotmart")
    # Entrada de e-mail pelo usuário
    email = st.text_input("Digite o e-mail do comprador:", key="hotmart_email")

    # Botão para iniciar a busca
    if st.button("Buscar Compras", key="buscar_compras"):
        if email:
            try:
                # Chamada à API para obter os participantes
                participantes = hotmart.get_sales_participants(buyer_email=email)
                comprador = buscar_informacoes_comprador(email, participantes)
                if comprador:
                    st.subheader("Informações do Comprador:")
                    st.write(f"Nome: {comprador.get('name', 'Não disponível')}")
                    st.write(f"Telefone: {comprador.get('phone', 'Não disponível')}")
                    st.write(f"Endereço: {comprador.get('address', {}).get('address', 'Não disponível')}, "
                             f"{comprador.get('address', {}).get('city', 'Não disponível')} - "
                             f"{comprador.get('address', {}).get('state', 'Não disponível')}")
                    st.write(f"CEP: {comprador.get('address', {}).get('zip_code', 'Não disponível')}")
                    st.write(f"CPF/CNPJ: {[doc['value'] for doc in comprador.get('documents', [])]}")
                else:
                    st.warning("Nenhuma informação do comprador encontrada.")

                # Chamada à API para obter o histórico de vendas
                vendas = hotmart.get_sales_history(buyer_email=email)
                if vendas:
                    st.success(f"Foram encontradas {len(vendas)} compras para o e-mail {email}.")

                    # Criando uma lista para armazenar as informações de vendas
                    vendas_data = []
                    for venda in vendas:
                        data_compra = converter_timestamp(venda.get('purchase', {}).get('order_date'))
                        vendas_data.append({
                            "ID da Venda": venda.get('purchase', {}).get('transaction'),
                            "Produto": venda.get('product', {}).get('name'),
                            "Data da Compra": data_compra,
                            "Valor": venda.get('purchase', {}).get('hotmart_fee', {}).get('base', 'Não disponível'),
                            "Status": venda.get('purchase', {}).get('status', 'Não disponível'),
                        })

                    # Convertendo a lista de vendas em um DataFrame
                    df_vendas = pd.DataFrame(vendas_data)

                    # Exibindo os dados como uma tabela interativa
                    st.dataframe(df_vendas)

                else:
                    st.warning("Nenhuma compra encontrada para este e-mail.")

            except Exception as e:
                st.error(f"Ocorreu um erro ao buscar as informações: {e}")
        else:
            st.warning("Por favor, insira um e-mail válido.")

# Conteúdo da aba "Curseduca"
with tabs[1]:
    st.header("Aba Curseduca")
    import requests
import pandas as pd
import streamlit as st

# Função para fazer requisição à API da Curseduca
def fetch_progress_report(api_url, token, email):
    try:
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        payload = {"email": email}  # Filtro por e-mail
        response = requests.post(api_url, headers=headers, json=payload)

        # Verifica se a resposta foi bem-sucedida
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Erro ao obter dados da API: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        st.error(f"Erro na requisição à API: {e}")
        return None

# Aba "Curseduca"
with tabs[1]:
    st.header("Relatório de Progresso - Curseduca")
    st.write("Visualize o progresso dos alunos filtrando pelo e-mail.")

    # Obter o endpoint e o token dos secrets
    api_key = st.secrets["CURSEDUCA_API"]
    token = st.secrets["CURSEDUCA_TOKEN"]

    # Entrada de e-mail
    email = st.text_input("Digite o e-mail do aluno:")

    if st.button("Gerar Relatório", key="curseduca_report"):
        if email:
            data = fetch_progress_report(api_key, token, email)
            if data:
                # Converta os dados retornados em um DataFrame para exibição
                if isinstance(data, list):  # Se a resposta for uma lista de objetos
                    df = pd.DataFrame(data)
                else:  # Se for um único objeto, transforme em lista
                    df = pd.DataFrame([data])

                # Exiba os dados em formato de tabela
                st.dataframe(df)
            else:
                st.warning("Nenhum dado encontrado para o e-mail informado.")
        else:
            st.warning("Por favor, insira um e-mail válido.")


# Conteúdo da aba "Google Sheets"
with tabs[2]:
    st.header("Aba Google Sheets")
    st.write("Conteúdo relacionado ao Google Sheets será exibido aqui.")
    # Adicione a lógica e elementos visuais necessários para a aba Google Sheets.
