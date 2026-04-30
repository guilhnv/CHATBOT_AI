import os
from pathlib import Path

import streamlit as st
from langchain_community.document_loaders import TextLoader
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnablePassthrough
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_text_splitters import RecursiveCharacterTextSplitter


APP_TITLE = "Assistente do Site"
APP_CAPTION = "Olá! Estou aqui para ajudar. Faz-me qualquer pergunta."
CONTENT_FILE = Path(os.getenv("CHATBOT_CONTENT_FILE", "informação.txt"))
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")


st.set_page_config(
    page_title=APP_TITLE,
    page_icon="💬",
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
    #MainMenu, footer, header {visibility: hidden;}
    .block-container {padding-top: 2rem; padding-bottom: 2rem;}
    </style>
    """,
    unsafe_allow_html=True,
)

st.title(f"💬 {APP_TITLE}")
st.caption(APP_CAPTION)


@st.cache_data(show_spinner=False)
def load_context(content_file: str) -> str:
    loader = TextLoader(content_file, encoding="utf-8")
    documents = loader.load()

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=600, chunk_overlap=80)
    texts = text_splitter.split_documents(documents)

    return "\n\n".join(doc.page_content for doc in texts)


@st.cache_resource(show_spinner=False)
def get_llm() -> ChatGoogleGenerativeAI:
    google_api_key = os.getenv("GOOGLE_API_KEY") or st.secrets.get("GOOGLE_API_KEY")

    if not google_api_key:
        st.error(
            "Falta configurar a variável GOOGLE_API_KEY. "
            "Cria uma chave gratuita no Google AI Studio e coloca-a nos secrets da plataforma onde publicares a app."
        )
        st.stop()

    return ChatGoogleGenerativeAI(
        model=GEMINI_MODEL,
        temperature=0.1,
        google_api_key=google_api_key,
    )


try:
    context = load_context(str(CONTENT_FILE))
except Exception as e:
    st.error(f"Erro ao carregar o ficheiro de conteúdo: {e}")
    st.stop()


template = """És um assistente virtual prestável de um site.
Falas em português de Portugal, de forma natural, simpática, curta e direta.

O teu único trabalho é responder às perguntas dos utilizadores com base no conteúdo abaixo.
Não inventas informação. Se algo não estiver no conteúdo, dizes claramente que não tens essa informação.

IMPORTANTE: As respostas podem estar em listas com bullet points ou separadas em parágrafos diferentes.
Lê TODO o conteúdo antes de concluir que não tens informação. Nunca digas que não sabes se a resposta estiver no conteúdo.

Conteúdo disponível:
{context}

Regras importantes:
- Responde apenas com base no conteúdo fornecido.
- Se não souberes ou a informação não estiver disponível, diz "Não tenho informação sobre isso, mas podes contactar-nos diretamente."
- Mantém as respostas curtas, claras e úteis.
- Nunca respondas perguntas que não tenham relação com o conteúdo do site.

Resposta:"""

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", template),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{question}"),
    ]
)


def get_chain():
    return (
        RunnablePassthrough.assign(chat_history=lambda x: x["chat_history"])
        | prompt
        | get_llm()
        | StrOutputParser()
    )


if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if pergunta := st.chat_input("Como posso ajudar?"):
    st.session_state.messages.append({"role": "user", "content": pergunta})
    with st.chat_message("user"):
        st.markdown(pergunta)

    with st.chat_message("assistant"):
        with st.spinner("A pensar..."):
            chat_history = []
            for msg in st.session_state.messages[:-1]:
                if msg["role"] == "user":
                    chat_history.append(HumanMessage(content=msg["content"]))
                else:
                    chat_history.append(AIMessage(content=msg["content"]))

            chain = get_chain()
            resposta = chain.invoke(
                {
                    "context": context,
                    "chat_history": chat_history,
                    "question": pergunta,
                }
            )

            st.markdown(resposta)

    st.session_state.messages.append({"role": "assistant", "content": resposta})
