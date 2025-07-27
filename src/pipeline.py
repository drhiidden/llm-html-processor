"""
Pipeline de procesamiento de HTML con LLMs.
"""

import time
import traceback
from typing import List, Dict, Any, Optional, Tuple
from .models import ProcessingOptions, ProcessingResult, TextChunk
from .core.extractor import extract_text_nodes
from .core.injector import inject_text
from .core.errors import HTMLProcessingError, MalformedHTMLError, EmptyHTMLError
from .llm.factory import create_llm_client, LLMProvider
from .llm.base import ChatMessage
from .llm.errors import LLMError, RateLimitError, AuthenticationError
from .utils.logging import get_logger

logger = get_logger("pipeline")

# Límites y constantes
MAX_RETRY_ATTEMPTS = 3
CHUNK_BATCH_SIZE = 10  # Procesar chunks en lotes para evitar problemas de memoria

class PipelineError(Exception):
    """Excepción base para errores en el pipeline."""
    pass

def _create_prompt_for_task(
    chunk: TextChunk, 
    options: ProcessingOptions
) -> List[ChatMessage]:
    """
    Crea un prompt para el LLM según la tarea.
    
    Args:
        chunk: Fragmento de texto a procesar
        options: Opciones de procesamiento
        
    Returns:
        List[ChatMessage]: Lista de mensajes para el LLM
    """
    messages = []
    
    # Instrucciones base según la tarea
    if options.task == "paraphrase":
        system_prompt = (
            f"Eres un asistente experto en reescritura de texto en {options.language}. "
            f"Reescribe el texto manteniendo su significado original pero con palabras diferentes. "
            f"Mantén el mismo tono y nivel de formalidad. "
            f"Si el texto contiene HTML o código, presérvalo exactamente."
        )
        user_prompt = f"Reescribe este texto: {chunk.text}"
    
    elif options.task == "summarize":
        system_prompt = (
            f"Eres un asistente experto en resumir texto en {options.language}. "
            f"Resume el texto manteniendo los puntos clave y el significado esencial. "
            f"Si el texto contiene HTML o código, presérvalo en la medida de lo posible."
        )
        user_prompt = f"Resume este texto: {chunk.text}"
    
    elif options.task == "custom":
        system_prompt = (
            f"Eres un asistente experto en procesamiento de texto en {options.language}. "
            f"Sigue las instrucciones exactamente."
        )
        user_prompt = f"{options.extra_prompt or 'Procesa este texto:'} {chunk.text}"
    
    else:
        raise ValueError(f"Tarea no soportada: {options.task}")
    
    # Añadir instrucciones RTL si es necesario
    if chunk.is_rtl:
        system_prompt += " El texto está en un idioma de derecha a izquierda (RTL), asegúrate de preservar esta característica."
    
    messages.append(ChatMessage("system", system_prompt))
    messages.append(ChatMessage("user", user_prompt))
    
    return messages

def _process_chunk_batch(
    llm, 
    chunks: List[TextChunk], 
    options: ProcessingOptions,
    stats: Dict[str, Any]
) -> List[TextChunk]:
    """
    Procesa un lote de chunks.
    
    Args:
        llm: Cliente LLM
        chunks: Lista de chunks a procesar
        options: Opciones de procesamiento
        stats: Diccionario de estadísticas
        
    Returns:
        List[TextChunk]: Chunks procesados
    """
    processed_chunks = []
    
    for i, chunk in enumerate(chunks):
        if not chunk.text.strip():
            processed_chunks.append(chunk)
            continue
            
        retry_count = 0
        success = False
        
        while retry_count < MAX_RETRY_ATTEMPTS and not success:
            try:
                logger.debug(f"Procesando chunk {i+1}/{len(chunks)}: {chunk.text[:50]}...")
                
                # Crear prompt
                messages = _create_prompt_for_task(chunk, options)
                
                # Estimar tokens de entrada
                tokens_in = sum(llm.get_token_count(msg.content) for msg in messages)
                stats["total_tokens_in"] += tokens_in
                
                # Llamar al LLM
                response = llm.chat(
                    messages,
                    use_cache=options.use_cache,
                    temperature=options.temperature,
                    max_tokens=options.max_tokens
                )
                
                # Estimar tokens de salida
                tokens_out = llm.get_token_count(response)
                stats["total_tokens_out"] += tokens_out
                
                # Crear chunk procesado
                processed_chunk = TextChunk(
                    text=response,
                    path=chunk.path,
                    is_rtl=chunk.is_rtl
                )
                processed_chunks.append(processed_chunk)
                
                stats["chunks_processed"] += 1
                logger.debug(f"Chunk {i+1} procesado: {tokens_in} tokens in, {tokens_out} tokens out")
                success = True
                
            except RateLimitError as e:
                retry_count += 1
                wait_time = 2 ** retry_count  # Backoff exponencial
                logger.warning(f"Límite de tasa excedido, reintentando en {wait_time}s: {e}")
                time.sleep(wait_time)
                
            except (AuthenticationError, LLMError) as e:
                logger.error(f"Error procesando chunk {i+1}: {e}")
                # En caso de error, mantener el texto original
                processed_chunks.append(chunk)
                stats["errors"] += 1
                break
                
            except Exception as e:
                logger.error(f"Error inesperado procesando chunk {i+1}: {e}")
                logger.debug(traceback.format_exc())
                # En caso de error, mantener el texto original
                processed_chunks.append(chunk)
                stats["errors"] += 1
                break
        
        # Si agotamos los reintentos
        if not success:
            logger.error(f"Agotados reintentos para chunk {i+1}")
            processed_chunks.append(chunk)
            stats["errors"] += 1
    
    return processed_chunks

def process_html(html: str, options: ProcessingOptions) -> ProcessingResult:
    """
    Procesa HTML usando LLMs según las opciones especificadas.
    
    Args:
        html: Contenido HTML como string
        options: Opciones de procesamiento
        
    Returns:
        ProcessingResult: Resultado del procesamiento
        
    Raises:
        PipelineError: Si hay un error en el pipeline
        HTMLProcessingError: Si hay un error procesando el HTML
    """
    logger.info(f"Iniciando procesamiento de HTML con tarea: {options.task}")
    start_time = time.time()
    
    # Estadísticas de procesamiento
    stats = {
        "chunks_processed": 0,
        "total_tokens_in": 0,
        "total_tokens_out": 0,
        "processing_time": 0,
        "errors": 0,
        "warnings": 0
    }
    
    try:
        # Extraer nodos de texto
        logger.debug("Extrayendo nodos de texto")
        try:
            chunks = extract_text_nodes(html, options.min_text_length)
            logger.info(f"Extraídos {len(chunks)} fragmentos de texto")
        except EmptyHTMLError:
            logger.warning("HTML vacío o demasiado pequeño, devolviendo sin cambios")
            stats["warnings"] += 1
            return ProcessingResult(
                html=html,
                stats=stats
            )
        except MalformedHTMLError as e:
            logger.error(f"HTML malformado: {e}")
            if hasattr(e, 'html_fragment') and e.html_fragment:
                logger.debug(f"Fragmento problemático: {e.html_fragment}")
            stats["errors"] += 1
            return ProcessingResult(
                html=html,  # Devolver HTML original
                stats=stats
            )
        
        # Si no hay chunks, devolver el HTML original
        if not chunks:
            logger.info("No se encontraron fragmentos de texto para procesar")
            return ProcessingResult(
                html=html,
                stats=stats
            )
        
        # Determinar proveedor LLM
        provider: LLMProvider
        if options.model.startswith(("gpt-", "text-")):
            provider = "openai"
        elif options.model.startswith("gemini"):
            provider = "gemini"
        else:
            provider = "local"
        
        # Crear cliente LLM
        logger.debug(f"Creando cliente LLM: {provider} / {options.model}")
        try:
            llm = create_llm_client(provider, options.model)
        except Exception as e:
            logger.error(f"Error al crear cliente LLM: {e}")
            raise PipelineError(f"No se pudo crear el cliente LLM: {e}")
        
        # Procesar chunks en lotes para evitar problemas de memoria
        processed_chunks = []
        for i in range(0, len(chunks), CHUNK_BATCH_SIZE):
            batch = chunks[i:i + CHUNK_BATCH_SIZE]
            logger.debug(f"Procesando lote {i//CHUNK_BATCH_SIZE + 1}/{(len(chunks)-1)//CHUNK_BATCH_SIZE + 1}")
            batch_processed = _process_chunk_batch(llm, batch, options, stats)
            processed_chunks.extend(batch_processed)
        
        # Reinyectar texto procesado
        logger.debug("Reinyectando texto procesado")
        try:
            result_html = inject_text(html, processed_chunks, strict=False)
        except HTMLProcessingError as e:
            logger.error(f"Error al inyectar texto: {e}")
            stats["errors"] += 1
            return ProcessingResult(
                html=html,  # Devolver HTML original en caso de error
                stats=stats
            )
        
    except Exception as e:
        logger.error(f"Error en el pipeline: {e}")
        logger.debug(traceback.format_exc())
        stats["errors"] += 1
        raise PipelineError(f"Error en el pipeline: {e}")
    finally:
        # Completar estadísticas
        stats["processing_time"] = time.time() - start_time
        
        logger.info(f"Procesamiento completado en {stats['processing_time']:.2f}s")
        logger.info(
            f"Estadísticas: {len(chunks) if 'chunks' in locals() else 0} chunks, "
            f"{stats['chunks_processed']} procesados, {stats['errors']} errores"
        )
    
    return ProcessingResult(
        html=result_html,
        stats=stats
    ) 