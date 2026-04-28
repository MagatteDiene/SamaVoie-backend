<p align="center">
  <img src="Logo-SamaVoie.jpeg" alt="SamaVoie Logo" width="600">
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.11-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54" alt="Python 3.11">
  <img src="https://img.shields.io/badge/FastAPI-0.128-005571?style=for-the-badge&logo=fastapi" alt="FastAPI">
  <img src="https://img.shields.io/badge/Pydantic_v2-e92063?style=for-the-badge&logo=pydantic&logoColor=white" alt="Pydantic v2">
  <img src="https://img.shields.io/badge/postgres-%23316192.svg?style=for-the-badge&logo=postgresql&logoColor=white" alt="PostgreSQL">
</p>

<p align="center">
  <img src="https://img.shields.io/badge/sqlalchemy-2.0-D71F00?style=for-the-badge&logo=sqlalchemy&logoColor=white" alt="SQLAlchemy">
  <img src="https://img.shields.io/badge/LangChain-1C3C3C?style=for-the-badge&logo=langchain&logoColor=white" alt="LangChain">
  <img src="https://img.shields.io/badge/ChromaDB-1.5-orange?style=for-the-badge" alt="ChromaDB">
  <img src="https://img.shields.io/badge/docker-%230db7ed.svg?style=for-the-badge&logo=docker&logoColor=white" alt="Docker">
</p>

---

# SamaVoie — API Backend

SamaVoie est une plateforme intelligente d'orientation académique dédiée aux élèves et étudiants sénégalais. Elle intègre **Kali AI**, un moteur de réponse basé sur une architecture RAG (Retrieval-Augmented Generation), capable de fournir des conseils personnalisés en s'appuyant sur une base de connaissances locale et officielle.

## Technologies Utilisées

| Couche | Technologie |
|:---|:---|
| Framework Web | FastAPI 0.128 (async) |
| LLM (Kali AI) | Gemma 4 |
| Embeddings | BAAI/BGE-M3 (local, symétrie indexation/retrieval) |
| Orchestration RAG | LangChain 1.2 |
| Base vectorielle | ChromaDB 1.5 |
| Base relationnelle | PostgreSQL + SQLAlchemy 2.0 |
| Migrations | Alembic 1.18 |
| Ingestion PDF | Gemini 1.5 Pro |
| Auth | JWT (python-jose) + bcrypt (passlib) |

## Prérequis

- **Python 3.11.x** — Python 3.14 est **incompatible** avec ChromaDB
- PostgreSQL (local ou Docker)
- Une clé API Gemini (extraction PDF)

## Installation

### 1. Créer l'environnement virtuel Python 3.11

```bash
# Windows
"C:/Users/DELL/AppData/Local/Programs/Python/Python311/python.exe" -m venv .venv
.venv\Scripts\activate

# macOS / Linux
python3.11 -m venv .venv
source .venv/bin/activate
```

### 2. Installer les dépendances

```bash
pip install -r requirements.txt
```

### 3. Configurer les variables d'environnement

```bash
cp .env.example .env
```

Éditer `.env` et remplir au minimum :

```env
GEMINI_API_KEY=your_gemini_api_key
JWT_SECRET_KEY=your_secret_key   # générer : openssl rand -hex 32
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/orientation_db
```

### 4. Appliquer les migrations de base de données

```bash
# S'assurer que PostgreSQL tourne et que la base existe
alembic upgrade head
```

### 5. Lancer le serveur

```bash
uvicorn app.main:app --reload
```

Le serveur démarre sur `http://localhost:8000`.
Documentation interactive : `http://localhost:8000/docs`

## Kali AI

Kali AI utilise une approche hybride :

- **Extraction structurée** — les PDF officiels (Guide GSA 2025, rapports SAARA) sont analysés par Gemini 1.5 Pro et les informations extraites sont stockées dans PostgreSQL.
- **Indexation sémantique** — les textes sont découpés en chunks (512 tokens, overlap 50) et indexés via BGE-M3 dans ChromaDB.
- **Retrieval symétrique** — la même instance BGE-M3 vectorise les questions utilisateur, garantissant l'alignement sémantique.
- **Contextualisation** — le profil étudiant (niveau, série, ville, intérêts) est intégré au prompt LLM.

## Structure du Projet

```
app/
├── main.py            # Lifespan, middlewares, exception handlers, routers
├── config.py          # Settings Pydantic depuis .env
├── dependencies.py    # get_current_user, get_current_admin (JWT)
├── api/               # Routers FastAPI (auth, chat, filieres, metiers…)
├── core/              # Logique métier (security, rag_engine, llm_client)
├── db/
│   ├── postgres.py    # Engine async + pool (pool_pre_ping, pool_size=10)
│   └── chroma.py      # Singleton ChromaDB
├── models/            # ORM SQLAlchemy (User, Filiere, Metier, Etablissement…)
├── schemas/           # Pydantic v2 (Create / Read par entité)
└── ingestion/         # Pipeline d'ingestion (chunker, bge_indexer, gemini_extractor)
migrations/            # Alembic — historique des migrations
data/
├── raw/               # Sources PDF/JSON (établissements, filières, métiers…)
└── processed/         # JSON nettoyés prêts pour l'indexation
```

## Migrations

Après chaque modification d'un modèle ORM :

```bash
alembic revision --autogenerate -m "description"
alembic upgrade head
```
