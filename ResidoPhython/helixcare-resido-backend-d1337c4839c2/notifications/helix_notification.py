from abc import ABC, abstractmethod


class HelixNotification(ABC):
    @abstractmethod
    def send(self, entry):
        pass
