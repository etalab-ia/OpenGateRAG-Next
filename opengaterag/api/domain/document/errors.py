from dataclasses import dataclass


@dataclass
class DocumentNotFoundError:
    pass


@dataclass
class UnsupportedFileTypeError:
    pass
