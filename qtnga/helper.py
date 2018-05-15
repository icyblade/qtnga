import traceback


class ExceptHandler(object):
    def __init__(self, logger):
        self.logger = logger

    def __call__(self, func):
        def generate_errcode(*args, **kwargs):
            # noinspection PyBroadException
            try:
                return func(*args[:-1], **kwargs)  # TODO
            except Exception:
                self.logger.error('Error found, please send logs to @icyblade.')
                self.logger.error(traceback.format_exc())

        return generate_errcode
