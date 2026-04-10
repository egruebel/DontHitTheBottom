from abc import ABC, abstractmethod

class IODevice(ABC):
    acquiring = False

    @property
    @abstractmethod
    def acquiring(self):
        pass

    #@abstractmethod
    #def callback(self):
    #    pass

    @abstractmethod
    def begin_receive(self):
        pass
