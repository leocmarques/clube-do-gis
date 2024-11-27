import streamlit as st
from hotmart_python import Hotmart
import logging

# Configuração das credenciais da Hotmart
CLIENT_ID = 'seu_client_id'
CLIENT_SECRET = 'seu_client_secret'
BASIC_TOKEN = 'seu_basic_token'

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
