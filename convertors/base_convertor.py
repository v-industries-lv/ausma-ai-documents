from abc import ABC, abstractmethod

class Convertor(ABC):

    @abstractmethod
    def image_to_text(self, input_data):
        pass