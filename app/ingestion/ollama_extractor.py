import json
import logging
from pathlib import Path

import httpx

from app.ingestion.pdf_utils import extract_text_from_pdf
from app.schemas.extraction import ExtractionResult

logger = logging.getLogger("samavoie.ingestion.ollama_extractor")

_OLLAMA_BASE_URL = "http://localhost:11434"
_OLLAMA_MODEL    = "gemma4:e4b"
_TIMEOUT         = 1800.0  # 30 min — gemma4 sur CPU pur (~10-20 min par PDF)

_SYSTEM_PROMPT = """\
Tu es un expert en orientation académique et professionnelle sénégalaise.
Analyse le document fourni et extrais toutes les informations disponibles sur les filières, les métiers et les établissements.

Ta réponse doit être UNIQUEMENT un objet JSON valide — aucune explication, aucun texte autour, aucune balise markdown.
Schéma attendu :
{
  "filieres": [{"nom":"","niveau":"","description":"","matieres":[],"debouches":[],"duree":"","etablissements":[],"metiers":[]}],
  "metiers": [{"nom":"","description":"","competences":[],"salaire_moyen":null,"salaire_debutant":null,"salaire_experimente":null,"secteur":""}],
  "etablissements": [{"nom":"","type":"","localisation":"","formations":[],"conditions_admission":null,"contact":null}],
  "chunks_texte": []
}

RÈGLES STRICTES pour les salaires (valeurs en FCFA/mois) :
- salaire_moyen       : moyenne des postes du métier présents dans le document (entier ou null)
- salaire_debutant    : salaire du poste junior/assistant/agent (entier ou null)
- salaire_experimente : salaire du poste responsable/directeur/senior (entier ou null)
- Plage plausible : 150 000 – 6 000 000 FCFA/mois
- Ne JAMAIS confondre un pourcentage (ex : 43 %) avec un salaire
- Ne JAMAIS inventer une valeur absente — utiliser null si incertain
- Pour les documents SAARA (données par poste), agréger les postes par famille de métier

Les champs "etablissements" et "metiers" dans une filière sont des listes de noms (strings).
Si une information est absente, utilise null pour les scalaires et [] pour les listes.\
"""


async def _check_ollama() -> None:
    """Vérifie qu'Ollama est joignable avant d'envoyer le document."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.get(f"{_OLLAMA_BASE_URL}/api/tags")
            r.raise_for_status()
    except Exception as exc:
        raise RuntimeError(
            f"Ollama inaccessible sur {_OLLAMA_BASE_URL} — "
            "vérifiez que le service est démarré (`ollama serve`)."
        ) from exc


async def extract_from_pdf(pdf_path: Path) -> ExtractionResult:
    """
    Extraction structurée d'un PDF via Ollama (modèle local gemma4).

    Le texte est extrait par pdfplumber puis envoyé à l'API native Ollama
    (/api/chat). Aucun appel externe — zéro quota.
    """
    source = pdf_path.name

    try:
        await _check_ollama()

        raw_text = extract_text_from_pdf(pdf_path)
        if not raw_text.strip():
            logger.warning("Texte vide extrait de %s — extraction abandonnée.", source)
            return ExtractionResult(source=source)

        logger.info(
            "Envoi vers Ollama (%s) : %s (%d caractères)",
            _OLLAMA_MODEL, source, len(raw_text),
        )

        payload = {
            "model": _OLLAMA_MODEL,
            "messages": [
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": f"Voici le contenu du document :\n\n{raw_text}"},
            ],
            "format": "json",
            "stream": False,
            "options": {
                "temperature": 0.1,
                "num_gpu": 0,  # force CPU — BGE-M3 occupe déjà le GPU (4 GB VRAM)
            },
        }

        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_OLLAMA_BASE_URL}/api/chat",
                json=payload,
            )
            if response.status_code != 200:
                logger.error("Ollama HTTP %d — réponse brute : %s", response.status_code, response.text)
            response.raise_for_status()

        content = response.json()["message"]["content"]
        data = json.loads(content)
        data["source"] = source
        data["chunks_texte"] = []  # rempli par le pipeline après chunking pdfplumber
        result = ExtractionResult.model_validate(data)

        logger.info(
            "Extraction Ollama réussie (source=%s) : %d filières, %d métiers, %d établissements",
            source, len(result.filieres), len(result.metiers), len(result.etablissements),
        )
        return result

    except Exception as exc:
        logger.error("Échec extraction Ollama pour %s : %s", source, exc)
        return ExtractionResult(source=source)
