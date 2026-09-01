import sqlite3
from Bio import Entrez

# Configuración de Entrez
Entrez.email = "acolinaarismendi@gmail.com"

# Parámetros de búsqueda
QUERY = "cardiovascular disease AND hypertension"
RETMAX = 200
DB_NAME = "cardioresearch.db"


def buscar_articulos(query, retmax=200):
    """Busca IDs de artículos en PubMed según una consulta."""
    print(f"Buscando artículos con la query: '{query}'...")
    handle = Entrez.esearch(db="pubmed", term=query, retmax=retmax)
    resultado = Entrez.read(handle)
    handle.close()
    return resultado["IdList"]


def obtener_detalles_articulos(id_list):
    """Obtiene el contenido XML completo de una lista de IDs de PubMed."""
    if not id_list:
        print("No se encontraron artículos para procesar.")
        return []

    print(f"Descargando detalles de {len(id_list)} artículos...")
    handle = Entrez.efetch(
        db="pubmed", id=id_list, rettype="abstract", retmode="xml"
    )
    articulos = Entrez.read(handle)
    handle.close()
    return articulos.get("PubmedArticle", [])


def extraer_datos(articulo):
    """Extrae campos clave de un artículo individual de PubMed."""
    cita = articulo.get("MedlineCitation", {})
    art = cita.get("Article", {})

    pmid = str(cita.get("PMID", ""))
    titulo = str(art.get("ArticleTitle", ""))

    try:
        abstract = " ".join(str(p) for p in art["Abstract"]["AbstractText"])
    except KeyError:
        abstract = None

    try:
        revista = str(art["Journal"]["Title"])
    except KeyError:
        revista = None

    return {
        "pmid": pmid,
        "title": titulo,
        "abstract": abstract,
        "journal": revista,
    }


def guardar_en_bd(lista_articulos, db_path=DB_NAME):
    """Guarda la lista de artículos en la base de datos SQLite."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS articles (
            pmid TEXT PRIMARY KEY,
            title TEXT,
            abstract TEXT,
            journal TEXT
        )
    """
    )
    conn.commit()

    for articulo in lista_articulos:
        cursor.execute(
            """
            INSERT OR REPLACE INTO articles (pmid, title, abstract, journal)
            VALUES (:pmid, :title, :abstract, :journal)
        """,
            articulo,
        )

    conn.commit()
    conn.close()
    print(f"¡Éxito! {len(lista_articulos)} artículos guardados en '{db_path}'.")


def main():
    id_list = buscar_articulos(QUERY, RETMAX)
    if id_list:
        articulos_xml = obtener_detalles_articulos(id_list)
        lista_articulos = [extraer_datos(art) for art in articulos_xml]
        guardar_en_bd(lista_articulos)


if __name__ == "__main__":
    main()