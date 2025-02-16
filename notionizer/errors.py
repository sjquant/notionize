class NotionizerError(Exception):
    pass


class InvalidMarkdownError(NotionizerError):
    pass


class UnknownTokenError(NotionizerError):
    pass


class ConversionError(NotionizerError):
    pass
