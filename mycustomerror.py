"""Вызов собственного исключения."""


class MyCustomError(Exception):
    """Класс собственного исключения."""

    def __init__(self, *args):
        if args:
            self.message = args[0]
        else:
            self.message = None

    def __str__(self):
        """Вызов метода str в MyCustomError."""
        if self.message:
            return f'MyCustomError: "{self.message}".'
        else:
            return 'MyCustomError была вызвана.'
