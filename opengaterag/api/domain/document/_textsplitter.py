from abc import ABC, abstractmethod


class TextSplitter(ABC):
    @abstractmethod
    def split(self, text: str) -> list[str]:
        """Return the contents of the chunks of the text, in order."""
        pass
