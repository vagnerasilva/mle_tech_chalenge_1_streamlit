import streamlit as st

# Título da aplicação
st.title("Meu Primeiro App com Streamlit")

# Texto simples
st.write("Olá! Este é um exemplo básico de aplicação em Streamlit.")

# Entrada de texto
nome = st.text_input("Digite seu nome:")

# Botão
if st.button("Enviar"):
    st.success(f"Seja bem-vindo(a), {nome}!")

# Slider
idade = st.slider("Selecione sua idade:", 0, 100, 25)
st.write(f"Sua idade é: {idade}")
