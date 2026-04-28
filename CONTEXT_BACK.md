# CONTEXT_BACK.md — Backend Repository Context
## Plateforme d'Orientation Académique au Sénégal (RAG + LLM)
**ESP — Diplôme d'Ingénieur Technologue (DIT) | 2026**

---

## 1. Problématique

Les élèves de Terminale et les étudiants sénégalais manquent d'outils personnalisés pour choisir
leur filière ou leur métier. Les informations sur les formations, les débouchés et les salaires sont
dispersées et inaccessibles. Ce projet construit une plateforme intelligente capable de répondre
en langage naturel aux questions d'orientation, en s'appuyant sur une base de connaissances
sénégalaise indexée via une architecture RAG.

**Question centrale :** Comment concevoir et mettre en place une plateforme web intelligente
capable de fournir une orientation académique personnalisée en exploitant une architecture RAG
et des modèles de langage ?

---

## 2. Stack Technique Backend

| Couche | Technologie | Rôle |
|---|---|---|
| API REST | **FastAPI** (Python 3.11+) | Endpoints, auth, routage, historique |
| Extraction structurée | **Gemini 1.5 Pro API** | Parsing intelligent PDF → JSON structuré |
| Modèle d'embedding | **BAAI/BGE-M3** (local, Sentence-Transformers) | Génération des embeddings |
| Moteur RAG | **LangChain** | Chunking, retrieval, construction du prompt |
| Validation | **Pydantic v2** | Vérification des types avant insertion |
| Base vectorielle | **ChromaDB** | Stockage et recherche sémantique (cosine) |
| Base relationnelle | **PostgreSQL** | Utilisateurs, profils, entités structurées |
| LLM (réponse finale) | **GPT-4o / Mistral 7B / Llama 3** | Génération des réponses contextualisées |
| Conteneurisation | **Docker + Docker Compose** | Déploiement unifié et portable |

**Principe de symétrie BGE-M3 :** le même modèle local BAAI/BGE-M3 est utilisé à la fois
pour l'indexation des chunks (ingestion) et pour la vectorisation des requêtes utilisateurs
(retrieval). Cela garantit un alignement sémantique optimal et élimine toute dépendance à une
API externe pour la recherche.

---

## 3. Structure des Répertoires Backend

```
backend/
├── app/
│   ├── main.py                  # Point d'entrée FastAPI, montage des routers
│   ├── config.py                # Variables d'environnement (Pydantic Settings)
│   ├── dependencies.py          # Dépendances partagées (DB session, auth)
│   │
│   ├── api/                     # Routers FastAPI
│   │   ├── auth.py              # /auth/register, /auth/login
│   │   ├── chat.py              # /chat — pipeline RAG complet
│   │   ├── filieres.py          # /filieres, /filieres/{id}
│   │   ├── metiers.py           # /metiers, /metiers/{id}
│   │   ├── etablissements.py    # /etablissements, /etablissements/{id}
│   │   ├── history.py           # /history/{user_id}
│   │   └── admin.py             # /admin/import, /admin/stats
│   │
│   ├── core/                    # Logique métier centrale
│   │   ├── security.py          # JWT, bcrypt, token utils
│   │   ├── rag_engine.py        # Pipeline RAG : retrieval + prompt + LLM
│   │   └── llm_client.py        # Abstraction du client LLM (GPT-4o / Mistral)
│   │
│   ├── ingestion/               # Pipeline d'ingestion des données
│   │   ├── gemini_extractor.py  # Flux 1 : PDF → Gemini → JSON → PostgreSQL
│   │   ├── bge_indexer.py       # Flux 2 : texte → BGE-M3 → ChromaDB
│   │   ├── chunker.py           # Découpage en chunks (512 tokens, overlap 50)
│   │   └── pipeline.py          # Orchestrateur des deux flux
│   │
│   ├── models/                  # Modèles SQLAlchemy (ORM)
│   │   ├── user.py
│   │   ├── filiere.py
│   │   ├── metier.py
│   │   ├── etablissement.py
│   │   └── conversation.py
│   │
│   ├── schemas/                 # Schémas Pydantic (validation + sérialisation)
│   │   ├── auth.py
│   │   ├── filiere.py
│   │   ├── metier.py
│   │   ├── etablissement.py
│   │   ├── chat.py
│   │   └── extraction.py        # Schémas Gemini extraction
│   │
│   └── db/
│       ├── postgres.py          # Session SQLAlchemy, engine
│       └── chroma.py            # Client ChromaDB, collection
│
├── data/
│   ├── raw/                 # Dossiers sources structurés
│   │   ├── etablissements/  # Annuaires, brochures d'écoles
│   │   ├── filieres/        # Programmes, catalogues universitaires
│   │   ├── metiers/         # Guide GSA, fiches descriptives, rapports SAARA
│   │   ├── salaires/        # Rapports ONUDI, Banque Mondiale, stats
│   │   └── guides/          # Documents transversaux (ex: Guide BAC-S)
│   └── processed/           # Données nettoyées (JSON) prêtes pour indexation
│
├── tests/
│   ├── unit/
│   └── integration/
│
├── .env.example                 # Template variables d'environnement
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── README.md
```

---

## 4. Modèles Pydantic de Référence

### 4.1 Extraction Gemini (ingestion)

```python
from pydantic import BaseModel
from typing import List, Optional

class MetierSchema(BaseModel):
    nom: str
    description: str
    competences: List[str]
    salaire_moyen: Optional[int] = None       # En FCFA/mois
    salaire_debutant: Optional[int] = None
    salaire_experimente: Optional[int] = None
    secteur: str

class FiliereSchema(BaseModel):
    nom: str
    niveau: str                               # Licence, Master, BTS, DUT, Doctorat
    description: str
    matieres: List[str]
    debouches: List[str]
    duree: str

class EtablissementSchema(BaseModel):
    nom: str
    type: str                                 # Université, École, Institut, Centre
    localisation: str
    formations: List[str]
    conditions_admission: Optional[str] = None
    contact: Optional[str] = None

class ExtractionResult(BaseModel):
    metiers: List[MetierSchema] = []
    filieres: List[FiliereSchema] = []
    etablissements: List[EtablissementSchema] = []
```

### 4.2 Chat & RAG

```python
class ChatRequest(BaseModel):
    user_id: int
    message: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    answer: str
    sources: List[str]           # Références aux chunks utilisés
    session_id: str

class UserProfile(BaseModel):
    niveau_scolaire: Optional[str] = None    # Terminale, Licence, Master...
    serie: Optional[str] = None              # S, L, STEG...
    ville: Optional[str] = None
    domaines_interet: List[str] = []
    matieres_preferees: List[str] = []
    type_etablissement: Optional[str] = None # public, privé
    metier_envisage: Optional[str] = None
```

### 4.3 Auth

```python
class UserRegister(BaseModel):
    email: EmailStr
    password: str                # Min 8 caractères
    nom: str
    prenom: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
```

---

## 5. Endpoints API

| Endpoint | Méthode | Auth | Description |
|---|---|---|---|
| `/auth/register` | POST | Non | Inscription d'un utilisateur |
| `/auth/login` | POST | Non | Authentification → token JWT |
| `/chat` | POST | JWT | Question → RAG → réponse LLM |
| `/filieres` | GET | Non | Liste des filières (filtres: niveau, mot-clé) |
| `/filieres/{id}` | GET | Non | Fiche détaillée d'une filière |
| `/metiers` | GET | Non | Liste des métiers (filtres: secteur, salaire) |
| `/metiers/{id}` | GET | Non | Fiche détaillée d'un métier |
| `/etablissements` | GET | Non | Liste des établissements (filtres: ville, type) |
| `/etablissements/{id}` | GET | Non | Fiche détaillée d'un établissement |
| `/history/{user_id}` | GET | JWT | Historique des conversations |
| `/profile/{user_id}` | GET/PUT | JWT | Profil utilisateur |
| `/admin/import` | POST | Admin | Import de documents dans la base RAG |
| `/admin/stats` | GET | Admin | Statistiques d'utilisation |

**Format de réponse standard :**
```json
{
  "success": true,
  "data": { ... },
  "message": "OK"
}
```

**Format d'erreur standard :**
```json
{
  "success": false,
  "error": "NOT_FOUND",
  "message": "Filière introuvable"
}
```

---

## 6. Logique du Pipeline RAG

### 6.1 Vue d'ensemble — Architecture Hybride Bifurquée

Le pipeline d'ingestion est divisé en deux flux complémentaires qui alimentent tous deux le moteur RAG.

```
FLUX 1 — Extraction Structurée         FLUX 2 — Indexation Sémantique
Sources : PDF complexes                Sources : Texte brut (CSV, JSON, TXT)
         (GSA 2025, SAARA, brochures)
              ↓                                      ↓
      Gemini 1.5 Pro API                         Chunking
      Parsing intelligent → JSON           512 tokens, overlap 50 tokens
              ↓                                      ↓
      Validation Pydantic                   BAAI/BGE-M3 (local)
      Vérification des types              Sentence-Transformers
              ↓                                      ↓
          PostgreSQL                           ChromaDB
      Données structurées               Embeddings + métadonnées

              ↓ Les deux flux alimentent le Moteur RAG ↓

RETRIEVAL SYMÉTRIQUE — BGE-M3
Question → BGE-M3 (local) → Vecteur → ChromaDB (cosine) → Top-k chunks → LLM → Réponse
```

### 6.2 Flux 1 — Extraction Structurée via Gemini

**Sources traitées :** Guide GSA 2025, rapports SAARA, brochures universitaires PDF.

```python
# gemini_extractor.py (logique de référence)
import google.generativeai as genai

EXTRACTION_PROMPT = """
Analyse ce document PDF et extrais les informations suivantes en JSON :
{
  "metiers": [{"nom": str, "description": str, "competences": [str],
               "salaire_moyen": int, "salaire_debutant": int,
               "salaire_experimente": int, "secteur": str}],
  "filieres": [{"nom": str, "niveau": str, "description": str,
                "matieres": [str], "debouches": [str], "duree": str}]
}
Retourne uniquement le JSON, sans texte supplémentaire.
"""

def extract_from_pdf(pdf_path: str) -> ExtractionResult:
    model = genai.GenerativeModel("gemini-1.5-pro")
    # Upload du PDF + appel API
    response = model.generate_content([EXTRACTION_PROMPT, pdf_file])
    raw_json = response.text
    return ExtractionResult.model_validate_json(raw_json)
    # Si validation échoue → log erreur + skip (jamais d'insertion invalide)
```

**Règle absolue :** la validation Pydantic est obligatoire avant toute insertion en PostgreSQL.
Un champ obligatoire manquant ou un type incorrect entraîne un rejet et un log d'erreur.

### 6.3 Flux 2 — Indexation Sémantique via BGE-M3

```python
# bge_indexer.py (logique de référence)
from sentence_transformers import SentenceTransformer
import chromadb

model = SentenceTransformer("BAAI/bge-m3")
client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_or_create_collection("orientation_senegal")

def index_documents(chunks: list[str], metadatas: list[dict]):
    embeddings = model.encode(chunks, normalize_embeddings=True)
    collection.add(
        documents=chunks,
        embeddings=embeddings.tolist(),
        ids=[f"chunk_{i}" for i in range(len(chunks))],
        metadatas=metadatas
        # métadonnées : source, type, filiere_id, metier_id, date_import
    )
```

**Paramètres de chunking :** 512 tokens par chunk, chevauchement (overlap) de 50 tokens
(sliding window). Les métadonnées sont indispensables pour la traçabilité des sources dans les réponses.

### 6.4 Pipeline RAG — Requête Utilisateur

```python
# rag_engine.py (logique de référence)

def answer_question(question: str, user_profile: UserProfile) -> ChatResponse:
    # 1. Vectorisation de la question (même modèle BGE-M3 → symétrie)
    query_embedding = model.encode([question], normalize_embeddings=True)

    # 2. Recherche sémantique dans ChromaDB (top-k = 5 chunks)
    results = collection.query(
        query_embeddings=query_embedding.tolist(),
        n_results=5
    )
    context_chunks = results["documents"][0]
    sources = results["metadatas"][0]

    # 3. Construction du prompt enrichi
    system_prompt = """Tu es un conseiller d'orientation académique expert du système
    éducatif sénégalais. Réponds uniquement à partir du contexte fourni.
    Si l'information est absente, indique-le honnêtement. Cite tes sources."""

    user_prompt = f"""
    Profil étudiant : {user_profile.model_dump()}
    
    Contexte (base de connaissances) :
    {chr(10).join(context_chunks)}
    
    Question : {question}
    """

    # 4. Appel LLM
    response = llm_client.complete(system_prompt, user_prompt)

    return ChatResponse(
        answer=response,
        sources=[s.get("source", "") for s in sources],
        session_id=...
    )
```

### 6.5 Seuils de Qualité RAG (métriques RAGAS)

| Métrique | Description | Seuil cible |
|---|---|---|
| Faithfulness | Fidélité des réponses aux documents sources | > 0.85 |
| Answer Relevancy | Pertinence de la réponse par rapport à la question | > 0.80 |
| Context Precision | Pertinence des chunks récupérés par BGE-M3 | > 0.75 |
| Latence | Temps de génération d'une réponse complète | < 5 s |

---

## 7. Sécurité

- **JWT** : tokens avec expiration, stockés côté client (Authorization header)
- **Bcrypt** : hachage des mots de passe (jamais de clair en base)
- **Pydantic** : validation stricte de toutes les entrées API
- **Variables d'environnement** : clé API Gemini, clé secrète JWT, DSN PostgreSQL — jamais dans le code source
- **HTTPS** obligatoire en production
- **Protection XSS/injection** : utiliser les ORM et éviter les requêtes SQL brutes

```bash
# .env.example
GEMINI_API_KEY=your_gemini_api_key
OPENAI_API_KEY=your_openai_api_key        # Si GPT-4o
JWT_SECRET_KEY=your_jwt_secret
DATABASE_URL=postgresql://user:pass@localhost:5432/orientation_db
CHROMA_PERSIST_PATH=./chroma_db
BGE_MODEL_NAME=BAAI/bge-m3
LLM_PROVIDER=mistral                      # mistral | openai | llama
```

---

## 8. Base de Connaissances — Périmètre Minimum

Le corpus doit couvrir au minimum, pour respecter les contraintes du CDC :
- **20 filières** (Licence, Master, BTS, DUT, Doctorat) du système sénégalais
- **30 métiers** avec compétences, parcours académique et données salariales (FCFA)
- **10 établissements** (UCAD, UGB, ESP, UADB, UIDT, universités privées, grandes écoles)

**Sources officielles prioritaires :** sites universitaires sénégalais, Guide GSA 2025, rapports
SAARA, annuaires MESRI, données ANSD.

---

## 9. Contraintes de Performance

- Temps de réponse chatbot : **< 5 secondes** (end-to-end)
- Charge simultanée : **50 utilisateurs minimum**
- BGE-M3 exécuté **localement** (zéro dépendance API externe pour l'embedding)
- FastAPI async par nature — utiliser `async def` sur tous les endpoints I/O-bound
- Docker Compose pour l'orchestration locale : `app`, `postgres`, `chromadb`

---

*Ce fichier constitue la source de vérité du dépôt backend. Il doit être maintenu à jour à chaque évolution majeure de l'architecture ou des schémas de données.*
