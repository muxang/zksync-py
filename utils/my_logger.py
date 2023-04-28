import logging

def get_logger(logger_name, log_file):
    # 创建logger
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.DEBUG)

    # 创建文件handler
    fh = logging.FileHandler(log_file)
    fh.setLevel(logging.DEBUG)

    # 创建控制台handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)

    # 创建日志格式
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)

    # 添加handler到logger
    logger.addHandler(fh)
    logger.addHandler(ch)

    # 返回logger
    return logger
