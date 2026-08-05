import logging
import sys
import traceback
import os
from datetime import datetime

class MillisecondFormatter(logging.Formatter):
    """Formatteur avec millisecondes exactes (.fff) pour l'encadrant."""
    def formatTime(self, record, datefmt=None):
        ct = datetime.fromtimestamp(record.created)
        s = ct.strftime("%Y-%m-%d %H:%M:%S")
        return f"{s}.{int(record.msecs):03d}"

def setup_logger(log_file="reception.log"):
    # S'assurer que le dossier logs existe dans le conteneur (/app/logs)
    log_dir = "/app/logs"
    os.makedirs(log_dir, exist_ok=True)
    full_path = os.path.join(log_dir, log_file)

    logger = logging.getLogger("RAG_SYSTEM")
    logger.setLevel(logging.DEBUG)
    
    if logger.handlers:
        return logger

    log_format = "[%(asctime)s] [%(levelname)s] [%(filename)s:%(lineno)d -> %(funcName)s()] : %(message)s"
    formatter = MillisecondFormatter(log_format)

    # Output Fichier + Console
    file_handler = logging.FileHandler(full_path, encoding="utf-8")
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger

logger = setup_logger()

def log_exception_with_traceback(e: Exception, context_message: str = "Erreur"):
    """Formatage complet de l'erreur (Traceback / Trustbag)."""
    tb_details = traceback.format_exc()
    error_payload = (
        f"🚨 {context_message} !\n"
        f"TYPE ERREUR  : {type(e).__name__}\n"
        f"DETAILS      : {str(e)}\n"
        f"STACK TRACE  :\n{tb_details}"
    )
    logger.error(error_payload)
    return error_payload