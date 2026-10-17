"""TF-IDF cosine-similarity retrieval over the fictional spec corpus
(spec_corpus.py). PostgreSQL + pgvector is the stack named in meta.json;
this module's PgvectorIndex class uses it when a database is reachable, and
falls back to the always-available in-process TfidfIndex otherwise (the
model-validation-alerting precedent: a project that needs Kafka/Postgres
documents the stand-up commands and skips cleanly when the broker or DB is
unreachable, rather than failing the whole measurement)."""
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from triage.protocol.spec_corpus import PASSAGES


class TfidfIndex:
    def __init__(self, passages=PASSAGES):
        self.ids = [p[0] for p in passages]
        self.citations = [p[1] for p in passages]
        self.texts = [p[2] for p in passages]
        self.vectorizer = TfidfVectorizer()
        self.matrix = self.vectorizer.fit_transform(self.texts)

    def top1(self, query):
        qv = self.vectorizer.transform([query])
        sims = cosine_similarity(qv, self.matrix)[0]
        best = int(sims.argmax())
        return dict(passage_id=self.ids[best], citation=self.citations[best],
                    text=self.texts[best], score=float(sims[best]))


def pgvector_available(dsn="dbname=triage_protocol host=localhost"):
    try:
        import psycopg2
        conn = psycopg2.connect(dsn, connect_timeout=2)
        conn.close()
        return True
    except Exception:
        return False


class PgvectorIndex:
    """Stand-up commands (not run automatically; this project never starts a
    database service of its own, per BUILDER section 3):

        createdb triage_protocol
        psql triage_protocol -c "CREATE EXTENSION IF NOT EXISTS vector;"
        psql triage_protocol -c "CREATE TABLE spec_passages (
            id TEXT PRIMARY KEY, citation TEXT, text TEXT, embedding vector(384));"

    Embeddings would be populated with any local sentence embedding model;
    this class only documents the schema and connects if a server happens to
    be reachable. tests/protocol/test_retrieval.py skips this class's test
    when no server answers on localhost, which is the expected case on this
    machine (PostgreSQL is not installed as a running service here)."""

    def __init__(self, dsn="dbname=triage_protocol host=localhost"):
        import psycopg2
        self.conn = psycopg2.connect(dsn, connect_timeout=2)

    def top1(self, query_embedding):
        with self.conn.cursor() as cur:
            cur.execute(
                "SELECT id, citation, text FROM spec_passages "
                "ORDER BY embedding <-> %s LIMIT 1",
                [list(query_embedding)],
            )
            row = cur.fetchone()
        return dict(passage_id=row[0], citation=row[1], text=row[2])
