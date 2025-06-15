"""
Ejemplo básico de uso del procesador HTML con diferentes clientes LLM.
"""

import os
from dotenv import load_dotenv
from src.llm.factory import create_llm_client
from src.models import ProcessingOptions, TextChunk
from src.core.extractor import extract_text_nodes
from src.core.injector import inject_text

# Cargar variables de entorno
load_dotenv()

def process_with_llm(html: str, provider: str, model: str | None = None) -> str:
    """
    Procesa HTML usando el proveedor LLM especificado.
    
    Args:
        html: HTML a procesar
        provider: Proveedor LLM ("openai", "gemini", "local")
        model: Modelo específico a usar (opcional)
        
    Returns:
        str: HTML procesado
    """
    # Extraer nodos de texto
    chunks = extract_text_nodes(html)
    
    # Crear cliente LLM
    llm = create_llm_client(provider, model)
    
    # Procesar cada chunk
    for chunk in chunks:
        messages = [
            ChatMessage("system", "Eres un asistente que reescribe texto preservando su significado."),
            ChatMessage("user", f"Reescribe este texto: {chunk.text}")
        ]
        
        response = llm.chat(messages, temperature=0.7)
        chunk.text = response
    
    # Reinyectar texto procesado
    return inject_text(html, chunks)

if __name__ == "__main__":
    # HTML de ejemplo
    html = """
    <html>
        <body>
            <p>שלום עולם</p>
            <p>Hello World</p>
        </body>
    </html>
    """
    
    # Procesar con diferentes proveedores
    providers = ["openai", "gemini", "local"]
    
    for provider in providers:
        try:
            print(f"\nProcesando con {provider}...")
            result = process_with_llm(html, provider)
            print(f"Resultado ({provider}):\n{result}")
        except Exception as e:
            print(f"Error con {provider}: {e}") 