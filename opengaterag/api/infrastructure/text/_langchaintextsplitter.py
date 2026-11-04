from langchain_text_splitters import Language, RecursiveCharacterTextSplitter

from opengaterag.api.domain.document import TextSplitter


class LangChainTextSplitter(TextSplitter):
    def __init__(self, chunk_max_characters: int):
        self.splitter = RecursiveCharacterTextSplitter.from_language(Language.MARKDOWN, chunk_size=chunk_max_characters, chunk_overlap=0)

    def split(self, text: str) -> list[str]:
        return self.splitter.split_text(text)
