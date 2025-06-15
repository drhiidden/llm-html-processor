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
    <h1>שלום עולם</h1>
    <p>זהו מסמך לדוגמה</p>
  </body>
</html>
"""

# Configurar opciones
options = ProcessingOptions(
    task="translate",  # translate, paraphrase, summarize
    source_language="he",
    target_language="en",
    model="gpt-4",  # gpt-4, gemini-pro, local
    preserve_formatting=True
)

# Procesar HTML
result = process_html(html, options)
print(result.html)
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
```

2. Archivo `.env`:
```env
OPENAI_API_KEY=your-key-here
GOOGLE_API_KEY=your-key-here
LOCAL_LLM_URL=http://localhost:11434
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