import logging
from pathlib import Path
from typing import List

import pdfplumber

logger = logging.getLogger("samavoie.ingestion.pdf_utils")

# Stratégie "lines" : pour les tableaux avec bordures visibles (ex : SAARA, rapports PDF)
_TABLE_SETTINGS_LINES = {
    "vertical_strategy": "lines",
    "horizontal_strategy": "lines",
    "snap_tolerance": 3,
    "join_tolerance": 3,
    "edge_min_length": 3,
    "min_words_vertical": 1,
    "min_words_horizontal": 1,
    "intersection_tolerance": 3,
    "text_x_tolerance": 3,
    "text_y_tolerance": 3,
}

# Stratégie "text" : fallback pour les tableaux alignés par colonnes sans bordures
_TABLE_SETTINGS_TEXT = {
    "vertical_strategy": "text",
    "horizontal_strategy": "text",
    "snap_tolerance": 3,
    "join_tolerance": 3,
    "min_words_vertical": 3,
    "min_words_horizontal": 1,
    "intersection_tolerance": 3,
    "text_x_tolerance": 3,
    "text_y_tolerance": 3,
}


def _format_table(table_data: List[List]) -> str:
    """Formate une table pdfplumber en texte pipe-séparé, en supprimant les lignes vides."""
    rows = []
    for row in table_data:
        cells = [str(cell or "").strip().replace("\n", " ") for cell in row]
        if any(c for c in cells):
            rows.append(" | ".join(cells))
    return "\n".join(rows)


def _words_to_lines(words: list) -> str:
    """Regroupe des mots en lignes selon leur position verticale, ordonnés horizontalement."""
    if not words:
        return ""
    buckets: dict[int, list] = {}
    for w in words:
        # Arrondi à 5 pts pour absorber les légers décalages de rendu slide
        bucket = round(w["top"] / 5) * 5
        buckets.setdefault(bucket, []).append(w)

    lines = [
        " ".join(w["text"] for w in sorted(ws, key=lambda w: w["x0"]))
        for ws in (buckets[y] for y in sorted(buckets))
    ]
    return "\n".join(lines)


def extract_text_from_pdf(pdf_path: Path) -> str:
    """
    Extrait le texte propre d'un PDF en gérant les tableaux et les slide decks.

    Stratégie par page :
    1. Détection des tableaux via bordures (strategy=lines) — fiable pour SAARA/rapports.
    2. Fallback détection par alignement texte si aucune bordure (strategy=text).
    3. Texte hors-tableaux extrait mot par mot, réordonné par position Y/X.
    4. Les régions tableau sont exclues du texte hors-tableau pour éviter les doublons.

    Retourne un texte concaténé page par page, séparé par "---".
    """
    pages_text = []

    with pdfplumber.open(str(pdf_path)) as pdf:
        for page_num, page in enumerate(pdf.pages, 1):
            page_parts: List[str] = []

            # --- Étape 1 : détection des tableaux ---
            found_tables = page.find_tables(table_settings=_TABLE_SETTINGS_LINES)
            if not found_tables:
                found_tables = page.find_tables(table_settings=_TABLE_SETTINGS_TEXT)

            table_bboxes = []
            for tbl in found_tables:
                data = tbl.extract()
                if not data:
                    continue
                formatted = _format_table(data)
                if formatted.strip():
                    page_parts.append(formatted)
                    table_bboxes.append(tbl.bbox)  # (x0, top, x1, bottom)

            # --- Étape 2 : texte hors des régions tableau ---
            all_words = page.extract_words(
                x_tolerance=3,
                y_tolerance=3,
                keep_blank_chars=False,
                use_text_flow=True,
            )

            if table_bboxes:
                non_table_words = []
                for w in all_words:
                    cx = (w["x0"] + w["x1"]) / 2
                    cy = (w["top"] + w["bottom"]) / 2
                    # Marge de 2 pts pour absorber les imprécisions de coordonnées
                    in_table = any(
                        (bbox[0] - 2) <= cx <= (bbox[2] + 2)
                        and (bbox[1] - 2) <= cy <= (bbox[3] + 2)
                        for bbox in table_bboxes
                    )
                    if not in_table:
                        non_table_words.append(w)
            else:
                non_table_words = all_words

            text_block = _words_to_lines(non_table_words)
            if text_block.strip():
                page_parts.append(text_block)

            if page_parts:
                pages_text.append("\n\n".join(page_parts))

            logger.debug(
                "Page %d : %d tableau(x), %d mots non-tableau",
                page_num, len(found_tables), len(non_table_words),
            )

    full_text = "\n\n---\n\n".join(p for p in pages_text if p.strip())
    logger.info(
        "PDF extrait : %d pages, %d caractères (source=%s)",
        len(pages_text), len(full_text), pdf_path.name,
    )
    return full_text
