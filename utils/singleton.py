class SingletonMeta(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            print(f"Tworzenie instancji {cls.__name__}")
            cls._instances[cls] = super().__call__(*args, **kwargs)
        else:
            print(f"Zwracam istniejącą instancję {cls.__name__}")
        return cls._instances[cls]