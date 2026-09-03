# CardioResearch

Proyecto de análisis de datos que extrae, procesa y visualiza resúmenes cardiovasculares usando modelos de IA locales (Qwen) y Python.

## Descripción

CardioResearch facilita el procesamiento de información cardiovascular mediante un flujo de trabajo reproducible para extraer datos, analizarlos y generar visualizaciones. El uso de modelos locales permite trabajar con los datos sin depender de servicios externos.

## Características

- Extracción y procesamiento de resúmenes cardiovasculares.
- Análisis de datos con Python.
- Visualización de resultados.
- Integración con modelos de IA locales, como Qwen.

## Requisitos

- Python 3.10 o superior.
- Dependencias definidas en `requirements.txt` (si está disponible).
- Un entorno local compatible con el modelo Qwen utilizado.

## Instalación

```bash
git clone <URL_DEL_REPOSITORIO>
cd CardioResearch
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

En Windows, activa el entorno virtual con:

```powershell
.venv\Scripts\activate
```

## Uso

Ejecuta el script o notebook principal del proyecto:

```bash
python <script_principal>.py
```

Consulta la documentación y los comentarios del código para configurar las rutas de entrada, el modelo y la ubicación de los resultados.

## Estructura sugerida

```text
CardioResearch/
├── data/           # Datos de entrada y resultados procesados
├── notebooks/      # Exploración y análisis
├── src/            # Código fuente
├── requirements.txt
└── README.md
```

## Privacidad y uso responsable

No incluyas información personal identificable ni datos clínicos sensibles en el repositorio. Los resultados son de apoyo al análisis y no sustituyen la evaluación de profesionales sanitarios.

## Contribuciones

Las contribuciones son bienvenidas. Abre una incidencia para proponer cambios o envía un pull request con una descripción clara de la modificación.

## Licencia

Este proyecto no incluye una licencia definida actualmente.
