import traceback

import wrapt


def ExceptHandler(logger):
    @wrapt.decorator
    def wrapper(wrapped, instance, args, kwargs):
        # noinspection PyBroadException
        try:
            if instance:
                return wrapped(*args[:-1], **kwargs)
            else:
                return wrapped(*args, **kwargs)
        except Exception:
            logger.error('Error found, please send logs to @icyblade.')
            logger.error(traceback.format_exc())
    return wrapper
