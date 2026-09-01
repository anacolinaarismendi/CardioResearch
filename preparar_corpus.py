import re
import sqlite3

DB_NAME = "cardioresearch.db"


def limpiar_texto(texto):
    """Limpia el texto: pasa a minúsculas, elimina caracteres especiales y espacios extra."""
    if not texto:
        return ""

    # Convertir a minúsculas
    texto = texto.lower()

    # Eliminar posibles etiquetas HTML
    texto = re.sub(r"<.*?>", "", texto)

    # Conservar letras (incluyendo tildes y eñes) y espacios, eliminando puntuación y números
    texto = re.sub(r"[^a-záéíóúüñ\s]", "", texto)

    # Normalizar espacios múltiples a un solo espacio
    texto = re.sub(r"\s+", " ", texto).strip()

    return texto


def preparar_corpus():
    """Lee los artículos de la BD, los limpia y los guarda en una nueva tabla procesada."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Crear tabla para el corpus limpio
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS clean_articles (
            pmid TEXT PRIMARY KEY,
            clean_title TEXT,
            clean_abstract TEXT,
            combined_text TEXT
        )
    """
    )
    conn.commit()

    # Leer artículos originales
    cursor.execute("SELECT pmid, title, abstract FROM articles")
    articulos = cursor.fetchall()

    print(f"Procesando y limpiando {len(articulos)} artículos...")

    for pmid, title, abstract in articulos:
        clean_title = limpiar_texto(title)
        clean_abstract = limpiar_texto(abstract)

        # Combinar título y resumen para futuros análisis de texto (NLP / TF-IDF / Embeddings)
        combined = f"{clean_title} {clean_abstract}".strip()

        cursor.execute(
            """
            INSERT OR REPLACE INTO clean_articles (pmid, clean_title, clean_abstract, combined_text)
            VALUES (?, ?, ?, ?)
        """,
            (pmid, clean_title, clean_abstract, combined),
        )

    conn.commit()
    conn.close()
    print("¡Corpus preparado y guardado con éxito en la base de datos!")


if __name__ == "__main__":
    preparar_corpus()