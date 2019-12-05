import logging


def getLogger(name='', level=logging.DEBUG):
    # Gets or creates a logger
    logger = logging.getLogger(name)

    # set log level
    logger.setLevel(level)

    # define file handler and set formatter
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        '[%(asctime)s %(levelname)s - %(name)s.%(message)s', datefmt='%H:%M:%S'
    )
    handler.setFormatter(formatter)

    # add file handler to logger
    logger.addHandler(handler)
    return logger

    # Logs
    # logger.debug('A debug message')
    # logger.info('An info message')
    # logger.warning('Something is not right.')
    # logger.error('A Major error has happened.')
    # logger.critical('Fatal error. Cannot continue')
