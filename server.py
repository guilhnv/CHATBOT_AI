import os
import re
from pathlib import Path

import streamlit as st
from langchain_community.document_loaders import TextLoader
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnablePassthrough
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_text_splitters import RecursiveCharacterTextSplitter

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None


APP_TITLE = "Assistente do Site"
APP_CAPTION = "Olá! Estou aqui para ajudar. Faz-me qualquer pergunta."
CONTENT_FILE = Path(os.getenv("CHATBOT_CONTENT_FILE", "informação.txt"))
if not CONTENT_FILE.is_absolute():
    CONTENT_FILE = Path(__file__).parent / CONTENT_FILE
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

if load_dotenv:
    load_dotenv()


def get_google_api_key() -> str | None:
    try:
        secret_key = st.secrets.get("GOOGLE_API_KEY")
    except Exception:
        secret_key = None

    key = os.getenv("GOOGLE_API_KEY") or secret_key
    if not key or key == "A_TUA_CHAVE_AQUI":
        return None

    return key


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
def load_context(content_file: str, last_modified: float) -> str:
    loader = TextLoader(content_file, encoding="utf-8")
    documents = loader.load()

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1200, chunk_overlap=160)
    texts = text_splitter.split_documents(documents)

    return "\n\n".join(doc.page_content for doc in texts)


@st.cache_resource(show_spinner=False)
def get_llm() -> ChatGoogleGenerativeAI:
    google_api_key = get_google_api_key()

    if not google_api_key:
        raise RuntimeError("GOOGLE_API_KEY não configurada.")

    return ChatGoogleGenerativeAI(
        model=GEMINI_MODEL,
        temperature=0.1,
        google_api_key=google_api_key,
    )


try:
    context = load_context(str(CONTENT_FILE), CONTENT_FILE.stat().st_mtime)
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


def normalize_text(text: str) -> list[str]:
    return re.findall(r"[a-zA-ZÀ-ÿ0-9]+", text.lower())


def split_context_sections(text: str) -> list[str]:
    sections = [section.strip() for section in re.split(r"\n\s*\n", text) if section.strip()]
    if sections:
        return sections

    return [sentence.strip() for sentence in re.split(r"(?<=[.!?])\s+", text) if sentence.strip()]


def answer_from_content(question: str, text: str) -> str:
    question_words = set(normalize_text(question))
    stop_words = {
        "a", "o", "os", "as", "um", "uma", "uns", "umas", "de", "da", "do", "das", "dos",
        "em", "no", "na", "nos", "nas", "por", "para", "com", "sem", "que", "qual", "quais",
        "como", "onde", "quando", "porque", "é", "sao", "são", "e", "ou", "me", "diz",
        "sobre", "informacao", "informação", "podes", "pode",
    }
    keywords = {word for word in question_words if len(word) > 2 and word not in stop_words}

    if not keywords:
        return "Pergunta-me sobre caminhos académicos, saídas profissionais, apoios, bolsas ou voluntariado."

    scored_sections = []
    for section in split_context_sections(text):
        section_words = set(normalize_text(section))
        score = len(keywords & section_words)
        if score:
            scored_sections.append((score, len(section), section))

    if not scored_sections:
        return "Não tenho informação sobre isso, mas podes contactar-nos diretamente."

    scored_sections.sort(key=lambda item: (-item[0], item[1]))
    answer = "\n\n".join(section for _, _, section in scored_sections[:2])

    if len(answer) > 900:
        answer = answer[:900].rsplit(" ", 1)[0] + "..."

    return answer


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

            try:
                chain = get_chain()
                resposta = chain.invoke(
                    {
                        "context": context,
                        "chat_history": chat_history,
                        "question": pergunta,
                    }
                )
            except Exception:
                resposta = answer_from_content(pergunta, context)

            st.markdown(resposta)

    st.session_state.messages.append({"role": "assistant", "content": resposta})
