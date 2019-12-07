from logging import (
    getLogger as _getLogger,
    StreamHandler,
    Formatter,
    basicConfig,
    debug,
    error,
    exception,
    info,
    ERROR,
    DEBUG,
    INFO,
    root,
)


def setup_logger(name='root', logfile='', level=DEBUG):
    root.name = name or 'root'

    basicConfig(
        filename=f'log/{logfile or name}.log',
        filemode='w',
        level=level,
        format='%(asctime)+1s %(levelname)-9s- %(name)+10s: \'%(funcName)s\' %(message)s',
        datefmt='%H:%M:%S',
    )


def getLogger(name='', level=DEBUG):
    # Gets or creates a logger
    logger = _getLogger(name)

    # set log level
    logger.setLevel(level)

    # define file handler and set formatter
    handler = StreamHandler()
    formatter = Formatter(
        fmt='%(asctime)-1s %(levelname)-9s- %(name)+10s: %(message)s',
        datefmt='%H:%M:%S',
    )
    handler.setFormatter(formatter)

    logger.addHandler(handler)
    return logger
