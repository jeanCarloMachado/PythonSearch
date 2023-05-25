
class BaseDataTask:
    def prompt(self):
        raise NotImplementedError()

    def build_dataset(self):
        raise NotImplementedError()
