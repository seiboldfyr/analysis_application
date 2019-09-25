
class AbstractWorkbook:
    data = {}

    def __init__(self):
        self.data = {}

    def __getitem__(self, key):
        return self.data[key]

    def __setitem__(self, key, item):
        self.data[key] = item

    def __str__(self):
        result = ''
        for key, value in self.data.items():
            result += '%s: %s \n' % (key, str(value))
        return result

    def get_data(self):
        return self.data

