"""
Interfaz de línea de comandos para el procesador HTML.
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional

from . import process_html
from .models import ProcessingOptions
from .utils.logging import configure_from_env, get_logger, LogConfig, setup_logging

def parse_args() -> argparse.Namespace:
    """
    Parsea los argumentos de línea de comandos.
    
    Returns:
        argparse.Namespace: Argumentos parseados
    """
    parser = argparse.ArgumentParser(
        description="Procesador de HTML multilingüe con LLMs",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    # Argumentos de entrada/salida
    parser.add_argument(
        "input", 
        help="Archivo HTML de entrada o directorio"
    )
    parser.add_argument(
        "-o", "--output", 
        help="Archivo HTML de salida o directorio (por defecto: sobreescribe entrada)"
    )
    
    # Opciones de procesamiento
    parser.add_argument(
        "-t", "--task",
        choices=["paraphrase", "summarize", "custom"],
        default="paraphrase",
        help="Tarea a realizar"
    )
    parser.add_argument(
        "-l", "--language",
        default="he",
        help="Idioma principal del texto"
    )
    parser.add_argument(
        "-m", "--model",
        default="gpt-4o-mini",
        help="Modelo LLM a utilizar"
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.7,
        help="Temperatura para generación"
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=2048,
        help="Máximo de tokens de salida"
    )
    parser.add_argument(
        "--prompt",
        help="Prompt personalizado para tarea 'custom'"
    )
    
    # Opciones de caché
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Desactivar caché"
    )
    parser.add_argument(
        "--clear-cache",
        action="store_true",
        help="Limpiar caché antes de procesar"
    )
    
    # Opciones de logging
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        help="Nivel de logging"
    )
    parser.add_argument(
        "--log-file",
        help="Archivo de log"
    )
    
    # Opciones avanzadas
    parser.add_argument(
        "--min-text-length",
        type=int,
        default=2,
        help="Longitud mínima de texto para procesar"
    )
    parser.add_argument(
        "--recursive",
        action="store_true",
        help="Procesar archivos HTML en subdirectorios"
    )
    parser.add_argument(
        "--stats-file",
        help="Archivo JSON para guardar estadísticas"
    )
    
    return parser.parse_args()

def setup_logging_from_args(args: argparse.Namespace) -> None:
    """
    Configura el logging según los argumentos.
    
    Args:
        args: Argumentos de línea de comandos
    """
    config = LogConfig(
        level=args.log_level,
        log_file=args.log_file,
        console=True
    )
    setup_logging(config=config)

def process_file(
    input_file: str, 
    output_file: Optional[str], 
    options: ProcessingOptions,
    stats: Dict[str, Any]
) -> bool:
    """
    Procesa un archivo HTML.
    
    Args:
        input_file: Ruta del archivo de entrada
        output_file: Ruta del archivo de salida (o None para sobreescribir)
        options: Opciones de procesamiento
        stats: Diccionario de estadísticas
        
    Returns:
        bool: True si se procesó correctamente, False en caso contrario
    """
    logger = get_logger()
    
    try:
        # Leer archivo
        logger.info(f"Procesando archivo: {input_file}")
        with open(input_file, 'r', encoding='utf-8') as f:
            html = f.read()
        
        # Procesar HTML
        result = process_html(html, options)
        
        # Actualizar estadísticas
        file_stats = {
            "file": input_file,
            "status": "success" if result.stats.get("errors", 0) == 0 else "partial",
            "stats": result.stats
        }
        stats["files"].append(file_stats)
        stats["total_tokens_in"] += result.stats.get("total_tokens_in", 0)
        stats["total_tokens_out"] += result.stats.get("total_tokens_out", 0)
        stats["total_time"] += result.stats.get("processing_time", 0)
        stats["errors"] += result.stats.get("errors", 0)
        
        # Guardar resultado
        out_file = output_file or input_file
        with open(out_file, 'w', encoding='utf-8') as f:
            f.write(result.html)
            
        logger.info(f"Archivo guardado: {out_file}")
        return True
        
    except Exception as e:
        logger.error(f"Error procesando archivo {input_file}: {e}")
        stats["files"].append({
            "file": input_file,
            "status": "error",
            "error": str(e)
        })
        stats["errors"] += 1
        return False

def process_directory(
    input_dir: str, 
    output_dir: Optional[str], 
    options: ProcessingOptions,
    stats: Dict[str, Any],
    recursive: bool = False
) -> None:
    """
    Procesa todos los archivos HTML en un directorio.
    
    Args:
        input_dir: Directorio de entrada
        output_dir: Directorio de salida (o None para sobreescribir)
        options: Opciones de procesamiento
        stats: Diccionario de estadísticas
        recursive: Si se deben procesar subdirectorios
    """
    logger = get_logger()
    logger.info(f"Procesando directorio: {input_dir}")
    
    # Crear directorio de salida si no existe
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Obtener archivos HTML
    input_path = Path(input_dir)
    pattern = "**/*.html" if recursive else "*.html"
    
    for html_file in input_path.glob(pattern):
        rel_path = html_file.relative_to(input_dir)
        
        # Determinar archivo de salida
        if output_dir:
            out_file = os.path.join(output_dir, str(rel_path))
            # Crear directorio si no existe
            os.makedirs(os.path.dirname(out_file), exist_ok=True)
        else:
            out_file = str(html_file)
            
        # Procesar archivo
        process_file(str(html_file), out_file, options, stats)

def save_stats(stats: Dict[str, Any], filename: str) -> None:
    """
    Guarda estadísticas en un archivo JSON.
    
    Args:
        stats: Estadísticas a guardar
        filename: Nombre del archivo
    """
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2)
    except Exception as e:
        logger = get_logger()
        logger.error(f"Error al guardar estadísticas: {e}")

def main() -> int:
    """
    Función principal de la CLI.
    
    Returns:
        int: Código de salida
    """
    # Parsear argumentos
    args = parse_args()
    
    # Configurar logging
    setup_logging_from_args(args)
    logger = get_logger()
    
    # Limpiar caché si se solicita
    if args.clear_cache:
        from .llm.cache import global_cache
        global_cache.clear()
        logger.info("Caché limpiada")
    
    # Crear opciones de procesamiento
    options = ProcessingOptions(
        task=args.task,
        language=args.language,
        model=args.model,
        temperature=args.temperature,
        max_tokens=args.max_tokens,
        extra_prompt=args.prompt,
        use_cache=not args.no_cache,
        min_text_length=args.min_text_length
    )
    
    # Estadísticas globales
    stats = {
        "files": [],
        "total_tokens_in": 0,
        "total_tokens_out": 0,
        "total_time": 0,
        "errors": 0
    }
    
    # Procesar entrada
    try:
        if os.path.isdir(args.input):
            process_directory(
                args.input, 
                args.output, 
                options, 
                stats,
                recursive=args.recursive
            )
        else:
            process_file(args.input, args.output, options, stats)
            
        # Guardar estadísticas
        if args.stats_file:
            save_stats(stats, args.stats_file)
            logger.info(f"Estadísticas guardadas en: {args.stats_file}")
            
        # Mostrar resumen
        logger.info("Procesamiento completado:")
        logger.info(f"- Archivos: {len(stats['files'])}")
        logger.info(f"- Tokens entrada: {stats['total_tokens_in']}")
        logger.info(f"- Tokens salida: {stats['total_tokens_out']}")
        logger.info(f"- Tiempo total: {stats['total_time']:.2f}s")
        logger.info(f"- Errores: {stats['errors']}")
        
        return 0 if stats["errors"] == 0 else 1
        
    except KeyboardInterrupt:
        logger.info("Procesamiento interrumpido por el usuario")
        return 130
    except Exception as e:
        logger.error(f"Error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 