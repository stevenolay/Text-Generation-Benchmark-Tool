import logging


class Logger:
    # Singleton Class
    __instance = None

    @staticmethod
    def getInstance():
        """ Static access method. """
        if Logger.__instance is None:
            Logger()
        return Logger.__instance.LOGGER

    def __init__(self):
        """ Virtually private constructor. """
        if Logger.__instance is not None:
            raise Exception("This class is a singleton!")
        else:
            Logger.__instance = self

            log_format = logging.Formatter(
                "[%(asctime)-15s %(levelname)s] %(message)s")
            logger = logging.getLogger()
            logger.setLevel(logging.INFO)

            LOG_FILENAME = 'allLogs.log'
            file_handler = logging.FileHandler(LOG_FILENAME)
            file_handler.setFormatter(log_format)
            logger.addHandler(file_handler)

            console_handler = logging.StreamHandler()
            console_handler.setFormatter(log_format)
            logger.addHandler(console_handler)

            self.LOGGER = logger
