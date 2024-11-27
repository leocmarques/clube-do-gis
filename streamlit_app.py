import streamlit as st
from hotmart_python import Hotmart
import logging


import hmac
import streamlit as st


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

# Título do aplicativo
st.title('Consulta de Compras na Hotmart por E-mail')

# Entrada de e-mail pelo usuário
email = st.text_input('Digite o e-mail do comprador:')

# Botão para iniciar a busca
if st.button('Buscar Compras'):
    if email:
        # Chamada à API para obter o histórico de vendas
        try:
            vendas = hotmart.get_sales_history(buyer_email=email)
            if vendas:
                st.success(f'Foram encontradas {len(vendas)} compras para o e-mail {email}.')
                for venda in vendas:
                    st.write(f"ID da Venda: {venda.get('transaction')}")
                    st.write(f"Produto: {venda.get('product', {}).get('name')}")
                    st.write(f"Data da Compra: {venda.get('purchase_date')}")
                    st.write(f"Status: {venda.get('status')}")
                    st.write("---")
            else:
                st.warning('Nenhuma compra encontrada para este e-mail.')
        except Exception as e:
            st.error(f'Ocorreu um erro ao buscar as compras: {e}')
    else:
        st.warning('Por favor, insira um e-mail válido.')
