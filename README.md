# 📊 API Logs Dashboard - Streamlit

Dashboard interativo para visualizar e analisar logs de requisições da API MLE Tech Challenge.

## 🎯 Funcionalidades

- **📈 Métricas em Tempo Real**: Total de requisições, tempo médio de resposta, requisições OK e erros
- **🔎 Filtros Avançados**: Filtrar por método HTTP, status code e período
- **📊 Visualizações**: 
  - Gráficos de requisições por método
  - Distribuição de status codes
  - Tempo de resposta por endpoint (top 10)
  - Top 10 IPs com mais requisições
- **📋 Tabela Detalhada**: Visualizar todos os logs com ordenação customizável
- **📥 Download**: Exportar dados filtrados em CSV

## 🚀 Como Executar

### 1. Instalar Dependências

```bash
pip install -r requirements.txt
```

### 2. Executar a Aplicação

```bash
streamlit run app.py
```

A aplicação abrirá em `http://localhost:8501`

## 📦 Dependências

- **streamlit**: Framework para aplicações web
- **pandas**: Manipulação de dados
- **requests**: Requisições HTTP
- **matplotlib**: Visualizações
- **seaborn**: Temas e estilos de gráficos
- **numpy**: Computações numéricas

## 🔗 Integração com API

A aplicação consome dados de:
```
GET https://mle-tech-chalenge-1.onrender.com/api_logs
```

**Características:**
- ✅ Sem autenticação necessária
- ✅ Cache de 5 minutos
- ✅ Atualização manual via botão "Atualizar Dados"

## 📊 Estrutura de Dados

Cada log contém:
- `id`: ID único
- `method`: Método HTTP (GET, POST, etc)
- `path`: Path do endpoint
- `status_code`: HTTP Status Code
- `process_time`: Tempo de processamento (segundos)
- `ip_address`: IP do cliente
- `created_at`: Timestamp

## 🎨 Customizações Possíveis

Para adicionar novas visualizações, edite `app.py` e adicione:

```python
st.subheader("Seu Título")
# Seu código de visualização
```

## 💡 Dicas

- Use o botão **"Atualizar Dados"** para limpar o cache e buscar novos logs
- Filtros são aplicados em tempo real
- Dados podem ser baixados em CSV para análise posterior
- A sidebar permite ajustar controles rapidamente

## 📝 Notas

- A aplicação atualiza dados em cache a cada 5 minutos
- Para ambientes de produção, configure timeout e rate limiting
- Considere adicionar autenticação se os logs contiverem dados sensíveis

---

**Desenvolvido com ❤️ usando Streamlit**
