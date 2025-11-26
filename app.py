import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Título
st.title("Exemplo de Histograma com Streamlit")

# Gerando dados aleatórios
dados = np.random.randn(500)  # 500 valores de uma distribuição normal

# Slider para escolher número de bins
bins = st.slider("Número de bins:", min_value=5, max_value=50, value=20)

# Criando o histograma com matplotlib
fig, ax = plt.subplots()
ax.hist(dados, bins=bins, color="skyblue", edgecolor="black")
ax.set_title("Histograma - Matplotlib")
ax.set_xlabel("Valores")
ax.set_ylabel("Frequência")

# Exibindo no Streamlit
st.pyplot(fig)

# Também podemos usar seaborn
st.subheader("Histograma com Seaborn")
fig2, ax2 = plt.subplots()
sns.histplot(dados, bins=bins, kde=True, color="orange", ax=ax2)
ax2.set_title("Histograma - Seaborn")
st.pyplot(fig2)
