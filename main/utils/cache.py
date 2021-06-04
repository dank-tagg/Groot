from datetime import datetime

class CacheManager(dict):

    def __init__(self):
        # Initialize the dict with the items listed
        self.log = ""

    @property
    def length(self):
        return len(self)

    @staticmethod
    def do_log(message:str):
        now = datetime.utcnow().strftime("%d-%b %H-%M-%S")
        template = f"[{now}] {message}\n"
        return template


    def __setitem__(self, key, value):
        self.log += self.do_log(f"SET `{key}` with value `{value}`")
        return super().__setitem__(key, value)
    
    def __getitem__(self, key):
        self.log += self.do_log(f"GET `{key}` with value `{super().__getitem__(key)}`")
        return super().__getitem__(key)

    def get(self, key, default=None):
        self.log += self.do_log(f"GET `{key}` with value `{super().__getitem__(key)}`")
        return super().get(key, default)