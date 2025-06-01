from logger_config import logger

KEY = "F8"
bot_ativo = True  # Global control flag


def toggle_bot():
    global bot_ativo
    bot_ativo = not bot_ativo
    estado = "ATIVADO" if bot_ativo else "PAUSADO"
    logger.info(f"{estado}")
