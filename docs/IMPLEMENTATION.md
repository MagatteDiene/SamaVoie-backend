# Guide d'Implémentation - SamaVoie Backend

Ce document récapitule l'état actuel du projet, l'architecture choisie et les instructions pour faire évoluer le système. À mettre à jour après chaque modification majeure.

---

## 1. Architecture Globale

L'application est construite selon une architecture modulaire et asynchrone :
- Framework Web : FastAPI (Python 3.11+) pour sa rapidité et son support natif de l'asynchrone.
- Base Relationnelle : PostgreSQL + SQLAlchemy 2.0 (syntaxe Mapped).
- Base Vectorielle : ChromaDB pour le stockage sémantique (RAG).
- Validation : Pydantic v2 pour assurer l'intégrité des données entre l'API, le LLM et la DB.

---

## 2. Structure du Projet & Guide de Modification

Si vous devez modifier un élément, voici où aller :

| Composant | Répertoire / Fichier | Rôle | Quand le modifier ? |
| :--- | :--- | :--- | :--- |
| Configuration | app/config.py | Variables d'env & Settings | Ajouter une clé API, changer de DB. |
| Base de Données | app/db/ | Connexions Postgres/Chroma | Modifier la logique de session. |
| Modèles (DB) | app/models/ | Tables SQLAlchemy | Ajouter un champ en base de données. |
| Schémas (API) | app/schemas/ | Validation Pydantic | Modifier le format de réponse d'un endpoint. |
| Points d'entrée | app/main.py | Init FastAPI & Routers | Enregistrer un nouveau module API. |
| Données RAG | data/raw/ | Sources PDF/JSON | Ajouter de nouveaux documents à indexer. |

---

## 3. Étapes Réalisées

### Phase 1 : Initialisation (Terminé)
- Structure de dossiers conforme au CDC.
- Configuration type-safe avec pydantic-settings.
- Connexion asynchrone à PostgreSQL via asyncpg.
- Client ChromaDB persistant configuré.
- Point d'entrée app/main.py avec healthcheck.

### Phase 2 : Modèles & Schémas (Terminé)
- Tables d'association : filiere_etablissement et filiere_metier.
- Modèles SQL : User, Filiere, Metier, Etablissement, Conversation.
- Schémas Pydantic : Séparation Create / Read pour chaque entité.
- Relations : Support Many-to-Many fonctionnel pour l'orientation.

---

## 4. Guide Technique

### Travailler avec SQLAlchemy 2.0 (Asynchrone)
Toutes les interactions avec la base de données doivent être asynchrones.
- Utilisez select(Model) au lieu de query(Model).
- Utilisez session.execute() ou session.scalars().
- Utilisez la dépendance get_db dans vos endpoints FastAPI.

### Travailler avec Pydantic v2
- Les schémas de lecture utilisent model_config = ConfigDict(from_attributes=True) pour transformer les objets SQLAlchemy en JSON.
- Les champs sensibles (mots de passe) ne doivent exister que dans les schémas Create.

---

## 5. Roadmap

1. Phase 3 : Sécurité
   - Implémentation du hachage (Passlib/Bcrypt).
   - Génération et validation des tokens JWT (Jose).
   - Middleware pour protéger les routes.

2. Phase 4 : Ingestion de Données
   - Extracteur Gemini (PDF -> JSON).
   - Chunker de texte et Indexeur BGE-M3 (Texte -> ChromaDB).

3. Phase 5 : Moteur RAG
   - Pipeline LangChain complet intégrant Gemma 4.
   - Intégration du profil utilisateur dans le prompt.
