import tiktoken

from opengaterag.api.domain.document import Tokenizer


class TiktokenTokenizer(Tokenizer):
    def __init__(self, encoding_name: str):
        self.encoding = tiktoken.get_encoding(encoding_name)

    def count_tokens(self, text: str) -> int:
        # A document may contain special tokens such as `<|endoftext|>`: count them as plain text instead of raising.
        return len(self.encoding.encode(text, disallowed_special=()))
