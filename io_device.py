from abc import ABC, abstractmethod

class IODevice(ABC):
    acquiring = False

    @abstractmethod
    def acquiring(self):
        pass

    @abstractmethod
    def set_defaults(self):
        pass

    @abstractmethod
    def kill(self):
        pass

    @abstractmethod
    def begin_receive(self):
        pass
