# Diccionario de Datos — CardioResearch

## Tabla: `articles`
Datos crudos extraídos de PubMed vía NCBI E-utilities.

| Columna | Tipo | Descripción |
|---|---|---|
| pmid | TEXT/INTEGER | Identificador único de PubMed (clave primaria) |
| title | TEXT | Título original del artículo |
| journal | TEXT | Revista donde fue publicado |
| abstract | TEXT | Resumen original en inglés |
| publication_year | INTEGER | Año de publicación *(pendiente de agregar al schema)* |

## Tabla: `clean_articles`
Versión procesada/limpia de los textos, generada en la fase de preparación del corpus.

| Columna | Tipo | Descripción |
|---|---|---|
| pmid | TEXT/INTEGER | Referencia a `articles.pmid` (clave foránea) |
| clean_title | TEXT | Título tras limpieza de texto |
| clean_abstract | TEXT | Abstract tras limpieza (usado para chunking y embeddings) |
| combined_text | TEXT | Concatenación de título + abstract limpios |