import streamlit as st
from hotmart_python import Hotmart
import logging
from datetime import datetime
import hmac
import panda as pd


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
st.title('Consulta de Compras na Hotmart por E-mail')

# Entrada de e-mail pelo usuário
email = st.text_input('Digite o e-mail do comprador:')

# Botão para iniciar a busca
if st.button('Buscar Compras'):
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
                st.success(f'Foram encontradas {len(vendas)} compras para o e-mail {email}.')
                for venda in vendas:
                    st.write(f"ID da Venda: {venda.get('purchase', {}).get('transaction')}")
                    st.write(f"Produto: {venda.get('product', {}).get('name')}")
                    data_compra = converter_timestamp(venda.get('purchase', {}).get('order_date'))
                    st.write(f"Data da Compra: {data_compra}")
                    st.write(f"Valor: {venda.get('purchase', {}).get('hotmart_fee', {}).get('base')}")
                    st.write(f"Status: {venda.get('purchase', {}).get('status')}")
                    st.write("---")
            else:
                st.warning('Nenhuma compra encontrada para este e-mail.')
           
        except Exception as e:
            st.error(f"Ocorreu um erro ao buscar as informações: {e}")
    else:
        st.warning('Por favor, insira um e-mail válido.')
