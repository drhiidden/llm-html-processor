# llm-html-processor

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

Procesador de HTML multilingüe con LLMs que permite reescribir, resumir o traducir contenido HTML preservando su estructura. Soporta múltiples modelos de lenguaje como OpenAI GPT, Google Gemini y modelos locales.

## 🚀 Características

- ✨ Procesamiento de HTML multilingüe (enfoque inicial: hebreo, RTL)
- 🔍 Extracción e inyección de texto preservando la estructura HTML
- 🤖 Integración con múltiples LLMs:
  - OpenAI (GPT-4, GPT-3.5)
  - Google Gemini
  - Modelos locales (via API HTTP)
- 📦 Pipeline extensible y testeable
- 🛠️ CLI y API disponibles
- 🔄 Sistema robusto de reintentos y manejo de errores
- 💾 Sistema de caché para reducir costos de API
- 📊 Estadísticas detalladas de procesamiento y uso de tokens
- 📝 Logging configurable

## 📋 Requisitos

- Python 3.11 o superior
- Claves de API para los servicios que desee utilizar:
  - OpenAI API Key
  - Google Gemini API Key
  - URL del servidor local (opcional)

## 🔧 Instalación

```bash
# Usando pip
pip install llm-html-processor

# Usando poetry
poetry add llm-html-processor
```

## 💡 Uso básico

```python
from llm_html_processor import process_html
from llm_html_processor.models import ProcessingOptions

# Ejemplo de HTML
html = """
<html>
  <body>
    <h1 dir="rtl">שלום עולם</h1>
    <p dir="rtl">זהו מסמך לדוגמה</p>
  </body>
</html>
"""

# Configurar opciones
options = ProcessingOptions(
    task="paraphrase",  # paraphrase, summarize, custom
    language="he",
    model="gpt-4o-mini",  # gpt-4o-mini, gemini-pro, llama2
    temperature=0.7,
    preserve_html=True,
    use_cache=True  # Usar caché para reducir costos de API
)

# Procesar HTML
result = process_html(html, options)
print(result.html)

# Acceder a estadísticas
print(f"Tokens de entrada: {result.stats['total_tokens_in']}")
print(f"Tokens de salida: {result.stats['total_tokens_out']}")
print(f"Tiempo de procesamiento: {result.stats['processing_time']:.2f}s")
```

## 🛠️ Desarrollo

1. Clonar el repositorio:
```bash
git clone https://github.com/drhiidden/llm-html-processor.git
cd llm-html-processor
```

2. Crear y activar entorno virtual:
```bash
# Crear entorno
python -m venv venv

# Activar en Windows
.\\venv\\Scripts\\activate

# Activar en Linux/Mac
source venv/bin/activate
```

3. Instalar dependencias de desarrollo:
```bash
poetry install --with dev
```

4. Configurar pre-commit:
```bash
poetry run pre-commit install
```

5. Ejecutar pruebas:
```bash
poetry run pytest
```

## 📝 Configuración

El proyecto soporta varias formas de configuración:

1. Variables de entorno:
```bash
# OpenAI
export OPENAI_API_KEY="your-key-here"

# Google Gemini
export GOOGLE_API_KEY="your-key-here"

# Servidor local
export LOCAL_LLM_URL="http://localhost:11434"

# Logging
export LLM_LOG_LEVEL="DEBUG"
export LLM_LOG_FILE="logs/llm_processor.log"
```

2. Archivo `.env`:
```env
OPENAI_API_KEY=your-key-here
GOOGLE_API_KEY=your-key-here
LOCAL_LLM_URL=http://localhost:11434
LLM_LOG_LEVEL=INFO
```

## 🔍 Características avanzadas

### Sistema de caché

El sistema de caché reduce costos de API evitando llamadas repetidas:

```python
from llm_html_processor.llm.cache import global_cache

# Limpiar caché
global_cache.clear()

# Configurar tiempo de vida de caché (TTL)
global_cache.ttl = 3600  # 1 hora

# Desactivar caché para una llamada específica
result = process_html(html, options, use_cache=False)
```

### Logging personalizado

```python
from llm_html_processor import get_logger
from llm_html_processor.utils.logging import LogConfig, setup_logging

# Obtener logger predeterminado
logger = get_logger()
logger.info("Mensaje informativo")

# Configurar logger personalizado
custom_logger = setup_logging(
    "mi_aplicacion",
    LogConfig(level="DEBUG", log_file="logs/app.log")
)
```

## 🤝 Contribuir

Las contribuciones son bienvenidas. Por favor, sigue estos pasos:

1. Fork el repositorio
2. Crea una rama para tu feature (`git checkout -b feature/amazing-feature`)
3. Haz commit de tus cambios (`git commit -m 'Add amazing feature'`)
4. Push a la rama (`git push origin feature/amazing-feature`)
5. Abre un Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para más detalles.

## 🙏 Agradecimientos

- OpenAI por su API GPT
- Google por Gemini
- Todos los contribuidores y usuarios 