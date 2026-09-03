"""
Genera el índice vectorial FAISS a partir de los artículos guardados en
cardioresearch.db. El resultado se guarda en la carpeta faiss_index_cardio/,
que es la que espera app.py para cargar el asistente RAG.

Esta versión procesa los embeddings en lotes pequeños (en vez de mandar
todos los chunks de golpe) para evitar que el proceso de Ollama se sature
o se caiga con datasets grandes.

Ejecutar UNA sola vez (o cada vez que cambie el contenido de la base de datos):
    python3 generar_faiss_index.py

Requisitos previos:
    - Ollama corriendo (`ollama serve`)
    - Modelo de embeddings descargado: `ollama pull embeddinggemma:latest`
"""

import sqlite3
import time
from pathlib import Path

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings
from langchain_community.vectorstores import FAISS

DB_NAME = "cardioresearch.db"
FAISS_INDEX_PATH = Path(__file__).parent / "faiss_index_cardio"
EMBEDDING_MODEL = "embeddinggemma:latest"
BATCH_SIZE = 16          # cuántos chunks se envían a Ollama por petición
MAX_REINTENTOS = 3       # reintentos por lote si Ollama falla o se cae


def cargar_articulos():
    """Lee todos los artículos originales (sin limpiar) desde la tabla 'articles'."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM articles")
    filas = cursor.fetchall()
    conn.close()
    return [dict(fila) for fila in filas]


def construir_documentos(articulos):
    """Convierte cada fila de la BD en un Document de LangChain con metadatos."""
    documentos = []
    for art in articulos:
        title = art.get("title", "") or ""
        abstract = art.get("abstract", "") or ""
        texto = f"{title}\n\n{abstract}".strip()

        if not texto:
            continue

        metadata = {
            "pmid": art.get("pmid", "Desconocido"),
            "journal": art.get("journal", "Revista Desconocida"),
            "title": title or "Sin título",
        }
        documentos.append(Document(page_content=texto, metadata=metadata))

    return documentos


def construir_indice_por_lotes(chunks, embeddings):
    """Genera el índice FAISS agregando los chunks en lotes pequeños,
    con reintentos si Ollama falla en algún lote."""
    vectorstore = None
    total = len(chunks)
    num_lotes = (total + BATCH_SIZE - 1) // BATCH_SIZE

    for i in range(0, total, BATCH_SIZE):
        lote = chunks[i:i + BATCH_SIZE]
        num_lote_actual = i // BATCH_SIZE + 1

        for intento in range(1, MAX_REINTENTOS + 1):
            try:
                if vectorstore is None:
                    vectorstore = FAISS.from_documents(lote, embeddings)
                else:
                    vectorstore.add_documents(lote)

                print(f"  Lote {num_lote_actual}/{num_lotes} OK ({len(lote)} chunks)")
                break

            except Exception as e:
                print(f"  ⚠️ Lote {num_lote_actual}/{num_lotes} falló (intento {intento}/{MAX_REINTENTOS}): {e}")
                if intento == MAX_REINTENTOS:
                    raise
                time.sleep(3)  # le da tiempo a Ollama de recuperarse antes de reintentar

    return vectorstore


def main():
    print("Cargando artículos desde la base de datos...")
    articulos = cargar_articulos()
    print(f"{len(articulos)} artículos encontrados en '{DB_NAME}'.")

    documentos = construir_documentos(articulos)
    print(f"{len(documentos)} documentos válidos construidos.")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=150,
    )
    chunks = splitter.split_documents(documentos)
    print(f"{len(chunks)} fragmentos (chunks) generados tras el split.")

    print(f"Generando embeddings con Ollama ('{EMBEDDING_MODEL}') en lotes de {BATCH_SIZE}...")
    embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL)

    vectorstore = construir_indice_por_lotes(chunks, embeddings)

    vectorstore.save_local(str(FAISS_INDEX_PATH))
    print(f"✅ Índice FAISS guardado en: {FAISS_INDEX_PATH}")


if __name__ == "__main__":
    main()
