import logging
from typing import List

from langchain_text_splitters import RecursiveCharacterTextSplitter

logger = logging.getLogger("samavoie.ingestion.chunker")

# 1500 chars ≈ 512 tokens pour du texte français (3 chars/token en moyenne)
# 150 chars ≈ 50 tokens de chevauchement
_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1500,
    chunk_overlap=150,
    length_function=len,
    separators=["\n\n", "\n", ". ", " ", ""],
)


def split_text(text: str) -> List[str]:
    chunks = _splitter.split_text(text)
    logger.debug("Texte divisé en %d chunks", len(chunks))
    return chunks
