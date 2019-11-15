from flaskr.framework.exception import InvalidMeasurement
from flaskr.database.measurement_models.measurement import Measurement
from flaskr.database.measurement_models.repository import Repository


class Manager:
    buffer = []
    buffer_size = 1000

    def add(self, measurement: Measurement):
        self.buffer.append(measurement)
        if len(self.buffer) >= self.buffer_size:
            self.save()
            self.buffer.clear()

    def save(self):
        counter = 0
        batch = []
        repository = Repository()
        for model in self.buffer:
            if counter > self.buffer_size:
                repository.bulk_save(batch)

            if not model.is_valid():
                raise InvalidMeasurement(
                    'Found invalid measurement in batch: %s' % str(model)
                )
            batch.append(model)
            counter += 1

        repository.bulk_save(batch)
        self.buffer.clear()
