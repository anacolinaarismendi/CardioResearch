import streamlit as st
import os
from pathlib import Path
from langchain_community.vectorstores import FAISS
from langchain_ollama import OllamaEmbeddings, ChatOllama
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate

# 1. Configuración de la página
st.set_page_config(page_title="CardioResearch RAG", page_icon="🫀", layout="wide")
st.title("🫀 CardioResearch Asistente Médico (RAG)")
st.markdown("Consulta la base de datos de 200 artículos cardiovasculares. Respuestas basadas **estrictamente** en evidencia.")

# Ruta absoluta anclada a la ubicación de app.py, sin importar desde dónde se lance streamlit
FAISS_INDEX_PATH = Path(__file__).parent / "faiss_index_cardio"

# 2. Carga del pipeline RAG (Caché para no recargar en cada interacción)
@st.cache_resource
def init_rag():
    if not FAISS_INDEX_PATH.exists():
        return None, None  # (chain, error)

    try:
        embeddings = OllamaEmbeddings(model="embeddinggemma:latest")
        vectorstore = FAISS.load_local(
            str(FAISS_INDEX_PATH), embeddings, allow_dangerous_deserialization=True
        )
        retriever = vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 3})

        llm = ChatOllama(model="qwen3.5:2b-mlx", temperature=0)

        prompt = ChatPromptTemplate.from_messages([
            ("system",
             "Eres un asistente científico biomédico. Responde únicamente con la información "
             "contenida en el contexto adjunto. No inventes hechos, estadísticas ni extrapolaciones. "
             "Si la información no aparece en el contexto, declara explícitamente que no está disponible en los documentos.\n\n"
             "Contexto:\n{context}"),
            ("human", "{input}")
        ])

        question_answer_chain = create_stuff_documents_chain(llm, prompt)
        rag_chain = create_retrieval_chain(retriever, question_answer_chain)

        return rag_chain, None

    except Exception as e:
        return None, str(e)

chain, init_error = init_rag()

if chain is None:
    if init_error:
        st.error(f"⚠️ No se pudo inicializar el RAG. ¿Está Ollama corriendo? Detalle: {init_error}")
    else:
        st.error("⚠️ No se encontró la base de datos vectorial 'faiss_index_cardio'. Ejecuta primero el script de generación del RAG.")
    st.stop()

# 3. Inicializar el historial de chat en session_state
if "messages" not in st.session_state:
    st.session_state.messages = []

# Mostrar historial de mensajes
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 4. Input del usuario y ejecución
if prompt_text := st.chat_input("Escribe tu pregunta médica (ej. ¿Qué factores aumentan el riesgo de ACV en diabéticos?)"):
    st.session_state.messages.append({"role": "user", "content": prompt_text})
    with st.chat_message("user"):
        st.markdown(prompt_text)

    with st.chat_message("assistant"):
        with st.spinner("Buscando evidencia y generando respuesta..."):
            try:
                response = chain.invoke({"input": prompt_text})
                answer = response["answer"]
                source_docs = response["context"]

                full_response = f"{answer}\n\n**📚 Fuentes utilizadas:**\n"
                for i, doc in enumerate(source_docs, 1):
                    pmid = doc.metadata.get('pmid', 'Desconocido')
                    journal = doc.metadata.get('journal', 'Revista Desconocida')
                    title = doc.metadata.get('title', 'Sin título')
                    full_response += f"- **[{i}] PMID {pmid}** ({journal}): *{title}*\n"

                st.markdown(full_response)
                st.session_state.messages.append({"role": "assistant", "content": full_response})

            except Exception as e:
                st.error(f"Error al procesar la consulta: {e}")