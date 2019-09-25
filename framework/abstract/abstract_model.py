# TODO: Delete

from bson import ObjectId


class AbstractModel:
    data = {}

    def __init__(self):
        self.data = {}
        self.data['_id'] = None

    def __getitem__(self, key):
        return self.data[key]

    def __setitem__(self, key, item):
        self.data[key] = item

    def __str__(self):
        result = ''
        for key, value in self.data.items():
            result += '%s: %s \n' % (key, str(value))

        return result

    def set_data(self, data):
        for key, value in data.items():
            if key == '_id' and type(value) == str:
                value = ObjectId(value)

            self[key] = value

    def get_data(self):
        return self.data

    def get_id(self):
        return self.data['_id']
