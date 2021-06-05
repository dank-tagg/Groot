from datetime import datetime

class CacheManager(dict):

    def __init__(self):
        pass

    @property
    def length(self):
        return len(self)

    @staticmethod
    def do_log(message:str):
        now = datetime.utcnow().strftime("%d-%b %H-%M-%S")
        template = f"[{now}] {message}\n"
        return template


    def __setitem__(self, key, value):
        return super().__setitem__(key, value)
    
    def __getitem__(self, key):
        return super().__getitem__(key)

    def get(self, key, default=None):
        return super().get(key, default)