"""
Ejemplo básico de uso del procesador HTML con diferentes clientes LLM.
"""

import os
from dotenv import load_dotenv
from src.models import ProcessingOptions
from src.pipeline import process_html
from src.utils.logging import get_logger, LogConfig, setup_logging

# Configurar logging más detallado para ejemplos
logger = setup_logging(
    "examples",
    LogConfig(level="DEBUG", console=True)
)

# Cargar variables de entorno
load_dotenv()

def main():
    """Función principal del ejemplo."""
    # HTML de ejemplo con texto en hebreo y en inglés
    html = """
    <html>
        <head>
            <title>דף לדוגמה | Example Page</title>
        </head>
        <body>
            <h1 dir="rtl">שלום עולם</h1>
            <p dir="rtl">זהו מסמך לדוגמה עם טקסט בעברית</p>
            <div class="english-section">
                <h2>Hello World</h2>
                <p>This is an example document with text in English</p>
            </div>
        </body>
    </html>
    """
    
    logger.info("Iniciando ejemplo de procesamiento HTML")
    
    # Procesar con diferentes proveedores y tareas
    providers = [
        ("openai", "gpt-4o-mini"),
        ("gemini", "gemini-pro"),
        ("local", "llama2")
    ]
    
    tasks = ["paraphrase", "summarize"]
    
    for provider_name, model_name in providers:
        for task in tasks:
            try:
                logger.info(f"Procesando con {provider_name}/{model_name} - Tarea: {task}")
                
                # Configurar opciones
                options = ProcessingOptions(
                    task=task,
                    language="he",  # Idioma principal
                    model=model_name,
                    temperature=0.7,
                    preserve_html=True,
                    use_cache=True  # Usar caché para evitar llamadas repetidas
                )
                
                # Procesar HTML
                result = process_html(html, options)
                
                # Mostrar resultado y estadísticas
                logger.info(f"Resultado ({provider_name}/{task}):")
                logger.info(f"Tokens entrada: {result.stats.get('total_tokens_in', 0)}")
                logger.info(f"Tokens salida: {result.stats.get('total_tokens_out', 0)}")
                logger.info(f"Tiempo: {result.stats.get('processing_time', 0):.2f}s")
                logger.info(f"HTML resultante:\n{result.html[:500]}...")
                
            except Exception as e:
                logger.error(f"Error con {provider_name}/{task}: {e}")
                
    logger.info("Ejemplo completado")

if __name__ == "__main__":
    main() 