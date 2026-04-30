# Chatbot para site

Este projeto é uma app Streamlit com um chatbot baseado no conteúdo do ficheiro `informação.txt`.

A IA agora usa a API gratuita do Google Gemini, por isso o chatbot não depende do teu PC estar ligado.

## 1. Criar a chave gratuita da IA

1. Vai a https://aistudio.google.com/app/apikey
2. Entra com a tua conta Google.
3. Cria uma API key.
4. Guarda a chave em privado. Nunca a coloques dentro do HTML do site.

Segundo a documentação oficial da Google, o Gemini API tem uma camada gratuita para pequenos projetos e testes, com limites de utilização.

## 2. Testar localmente

Dentro desta pasta, instala as dependências:

```powershell
pip install -r requirements.txt
```

Depois define a tua chave e abre a app:

```powershell
$env:GOOGLE_API_KEY="A_TUA_CHAVE_AQUI"
python -m streamlit run server.py
```

Abre o endereço que aparecer no terminal, normalmente:

```text
http://localhost:8501
```

## 3. Publicar sem depender do teu PC

A opção grátis mais simples é publicar no Streamlit Community Cloud:

1. Cria uma conta em https://streamlit.io/cloud
2. Coloca estes ficheiros num repositório GitHub.
3. Cria uma nova app no Streamlit Cloud apontando para `server.py`.
4. Em `Settings > Secrets`, adiciona:

```toml
GOOGLE_API_KEY = "A_TUA_CHAVE_AQUI"
```

Depois disso, a app fica online e não precisa do teu computador ligado.

## 4. Colocar noutro site

Quando tiveres o link público da app, coloca este bloco HTML no outro site:

```html
<iframe
  src="https://TEU-LINK-DO-CHATBOT?embed=true"
  width="100%"
  height="650"
  style="border:0; border-radius:8px;"
  loading="lazy">
</iframe>
```

Troca `https://TEU-LINK-DO-CHATBOT` pelo link real da app publicada.

## Personalizar

- Para mudar as respostas do chatbot, edita `informação.txt`.
- O modelo padrão é `gemini-2.5-flash`.
- Para usar outro modelo Gemini, define a variável `GEMINI_MODEL`.
- Para usar outro ficheiro de conteúdo, define a variável `CHATBOT_CONTENT_FILE`.
