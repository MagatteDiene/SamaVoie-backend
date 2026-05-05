import json
import logging
from pathlib import Path

from google import genai
from google.genai import types

from app.config import settings
from app.schemas.extraction import ExtractionResult

logger = logging.getLogger("samavoie.ingestion.gemini_extractor")

_SYSTEM_PROMPT = """Tu es un expert en orientation académique et professionnelle sénégalaise.
Analyse le document PDF fourni et extrais toutes les informations disponibles sur les filières académiques, les métiers et les établissements.

Réponds UNIQUEMENT avec un JSON valide (sans markdown, sans balises code) respectant exactement ce schéma :
{
  "filieres": [{"nom":"","niveau":"","description":"","matieres":[],"debouches":[],"duree":"","etablissements":[],"metiers":[]}],
  "metiers": [{"nom":"","description":"","competences":[],"salaire_moyen":null,"salaire_debutant":null,"salaire_experimente":null,"secteur":""}],
  "etablissements": [{"nom":"","type":"","localisation":"","formations":[],"conditions_admission":null,"contact":null}],
  "chunks_texte": []
}

RÈGLES STRICTES pour les salaires (valeurs en FCFA/mois) :
- salaire_moyen     : moyenne des postes du métier présents dans le document (entier ou null)
- salaire_debutant  : salaire du poste junior/assistant/agent du métier (entier ou null)
- salaire_experimente : salaire du poste responsable/directeur/senior (entier ou null)
- Plage plausible : entre 150 000 et 6 000 000 FCFA/mois
- Ne JAMAIS confondre un pourcentage (ex: 43%, 78%) avec un salaire
- Ne JAMAIS inventer une valeur absente du document — utiliser null si incertain
- Pour les documents SAARA (données par poste), agréger les postes par famille de métier

Les champs "etablissements" et "metiers" dans une filière sont des listes de noms (strings).
Si une information est absente, utilise null pour les scalaires et [] pour les listes."""


async def extract_from_pdf(pdf_path: Path) -> ExtractionResult:
    """
    Extraction structurée d'un PDF via Gemini Vision (Option B).

    Le PDF est uploadé directement à l'API Gemini Files — Gemini le lit visuellement,
    ce qui contourne les pertes de structure de pypdf sur les slide decks.
    Le fichier uploadé est supprimé après chaque appel (nettoyage garanti par finally).
    """
    source = pdf_path.name
    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    uploaded = None

    try:
        logger.info("Upload PDF vers Gemini Files API : %s", source)
        uploaded = await client.aio.files.upload(
            file=pdf_path,
            config=types.UploadFileConfig(
                mime_type="application/pdf",
                display_name=source,
            ),
        )
        logger.debug("Fichier uploadé : uri=%s", uploaded.uri)

        response = await client.aio.models.generate_content(
            model="gemini-1.5-flash",
            contents=[
                types.Part.from_uri(file_uri=uploaded.uri, mime_type="application/pdf"),
                _SYSTEM_PROMPT,
            ],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.1,
            ),
        )

        data = json.loads(response.text)
        data["source"] = source
        data["chunks_texte"] = []  # rempli par le pipeline après chunking pdfplumber
        result = ExtractionResult.model_validate(data)
        logger.info(
            "Extraction Gemini Vision réussie (source=%s) : %d filières, %d métiers, %d établissements",
            source, len(result.filieres), len(result.metiers), len(result.etablissements),
        )
        return result

    except Exception as exc:
        logger.error("Échec extraction Gemini pour %s : %s", source, exc)
        return ExtractionResult(source=source)

    finally:
        if uploaded is not None:
            try:
                await client.aio.files.delete(name=uploaded.name)
                logger.debug("Fichier Gemini supprimé : %s", uploaded.name)
            except Exception as exc:
                logger.warning("Impossible de supprimer le fichier Gemini (%s) : %s", uploaded.name, exc)
