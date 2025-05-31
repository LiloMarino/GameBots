import logging

__all__ = ["logger"]


def setup_logger(nome_log: str = "BOT", log_file: str = "bot.log") -> logging.Logger:
    logger = logging.getLogger(nome_log)
    logger.setLevel(logging.INFO)
    logger.propagate = False  # Evita mensagens duplicadas

    if not logger.handlers:
        formatter = logging.Formatter("[%(name)s] [%(levelname)s] %(message)s")

        # Handler para console
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        # Handler para arquivo
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


logger = setup_logger()
