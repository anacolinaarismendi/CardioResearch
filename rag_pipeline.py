import sqlite3
import pandas as pd
from pathlib import Path
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_ollama import OllamaEmbeddings, ChatOllama
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate

# 1. Extracción de datos desde SQLite
db_path = Path("../cardioresearch.db")  # ajusta según tu estructura de carpetas
assert db_path.exists(), f"No se encontró la base de datos en: {db_path.resolve()}"

conn = sqlite3.connect(db_path)
query = """
    SELECT a.pmid, a.title, a.journal, c.clean_abstract 
    FROM articles a
    JOIN clean_articles c ON a.pmid = c.pmid
    WHERE c.clean_abstract IS NOT NULL AND LENGTH(c.clean_abstract) > 50
"""
df = pd.read_sql(query, conn)
conn.close()

assert not df.empty, "La consulta no devolvió filas: revisa que 'clean_articles' esté poblada."
print(f"Documentos extraídos: {len(df)}")

# 2. Creación de Documentos y Chunking
docs = [
    Document(
        page_content=row["clean_abstract"],
        metadata={
            "pmid": str(row["pmid"]),
            "title": row["title"] if pd.notna(row["title"]) else "Sin título",
            "journal": row["journal"] if pd.notna(row["journal"]) else "Sin revista"
        }
    )
    for _, row in df.iterrows()
]

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=700,
    chunk_overlap=100,
    separators=["\n\n", "\n", ". ", " ", ""]
)
chunks = text_splitter.split_documents(docs)
print(f"Chunks generados: {len(chunks)}")

# 3. Vectorización con embeddinggemma:latest
# Requiere: ollama pull embeddinggemma
embeddings = OllamaEmbeddings(model="embeddinggemma:latest")
vectorstore = FAISS.from_documents(chunks, embeddings)
vectorstore.save_local("faiss_index_cardio")

# 4. Configuración del Retriever
retriever = vectorstore.as_retriever(
    search_type="similarity",
    search_kwargs={"k": 3}
)

# 5. Configuración del LLM qwen3.5:2b-mlx (Temperatura 0)
# Requiere: ollama pull qwen3.5:2b-mlx
llm = ChatOllama(model="qwen3.5:2b-mlx", temperature=0)

# 6. Prompt estricto basado en evidencia
prompt = ChatPromptTemplate.from_messages([
    ("system", 
     "Eres un asistente científico biomédico. Responde únicamente con la información "
     "contenida en el contexto adjunto. No inventes hechos ni extrapolaciones. "
     "Si la información no aparece en el contexto, declara explícitamente que no está disponible.\n\n"
     "Contexto:\n{context}"),
    ("human", "{input}")
])

# 7. Cadena RAG moderna
question_answer_chain = create_stuff_documents_chain(llm, prompt)
rag_chain = create_retrieval_chain(retriever, question_answer_chain)

# 8. Prueba de inferencia
pregunta = "¿Qué relación existe entre la hipertensión y el deterioro cognitivo o demencia según los estudios?"
resultado = rag_chain.invoke({"input": pregunta})

print("--- RESPUESTA GENERADA ---")
print(resultado["answer"])
print("\n--- EVIDENCIA UTILIZADA ---")
for i, doc in enumerate(resultado["context"], 1):
    print(f"[{i}] PMID: {doc.metadata['pmid']} | Revista: {doc.metadata['journal']}")
    print(f"    Título: {doc.metadata['title']}\n")