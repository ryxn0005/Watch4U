DEFINE TABLE IF NOT EXISTS resident SCHEMAFULL;
DEFINE FIELD IF NOT EXISTS name ON resident TYPE string;
DEFINE FIELD IF NOT EXISTS room ON resident TYPE option<string>;
DEFINE FIELD IF NOT EXISTS notes ON resident TYPE option<string>;
DEFINE FIELD IF NOT EXISTS created_at ON resident TYPE datetime DEFAULT time::now();
DEFINE FIELD IF NOT EXISTS updated_at ON resident TYPE datetime DEFAULT time::now();

DEFINE TABLE IF NOT EXISTS caretaker SCHEMAFULL;
DEFINE FIELD IF NOT EXISTS name ON caretaker TYPE string;
DEFINE FIELD IF NOT EXISTS email ON caretaker TYPE option<string>;
DEFINE FIELD IF NOT EXISTS phone ON caretaker TYPE option<string>;
DEFINE FIELD IF NOT EXISTS created_at ON caretaker TYPE datetime DEFAULT time::now();

DEFINE TABLE IF NOT EXISTS cares_for TYPE RELATION FROM caretaker TO resident;
DEFINE FIELD IF NOT EXISTS created_at ON cares_for TYPE datetime DEFAULT time::now();

DEFINE TABLE IF NOT EXISTS device SCHEMAFULL;
DEFINE FIELD IF NOT EXISTS resident ON device TYPE record<resident>;
DEFINE FIELD IF NOT EXISTS label ON device TYPE string;
DEFINE FIELD IF NOT EXISTS external_id ON device TYPE option<string>;
DEFINE FIELD IF NOT EXISTS created_at ON device TYPE datetime DEFAULT time::now();

DEFINE TABLE IF NOT EXISTS fall_event SCHEMAFULL;
DEFINE FIELD IF NOT EXISTS resident ON fall_event TYPE record<resident>;
DEFINE FIELD IF NOT EXISTS detected_at ON fall_event TYPE datetime DEFAULT time::now();
DEFINE FIELD IF NOT EXISTS confidence ON fall_event TYPE option<float>;
DEFINE FIELD IF NOT EXISTS severity_label ON fall_event TYPE option<string>;
DEFINE FIELD IF NOT EXISTS source ON fall_event TYPE string DEFAULT 'camera';
DEFINE FIELD IF NOT EXISTS false_alarm ON fall_event TYPE bool DEFAULT false;
DEFINE FIELD IF NOT EXISTS acknowledged_at ON fall_event TYPE option<datetime>;
DEFINE FIELD IF NOT EXISTS acknowledged_by ON fall_event TYPE option<record<caretaker>>;
DEFINE FIELD IF NOT EXISTS clip_uri ON fall_event TYPE option<string>;
DEFINE FIELD IF NOT EXISTS payload ON fall_event TYPE option<object>;

DEFINE INDEX IF NOT EXISTS idx_fall_resident_time ON fall_event FIELDS resident, detected_at;

-- RAG Document Storage
DEFINE TABLE IF NOT EXISTS document SCHEMAFULL;
DEFINE FIELD IF NOT EXISTS content ON document TYPE string;
DEFINE FIELD IF NOT EXISTS embedding ON document TYPE option<array<float>>;
DEFINE FIELD IF NOT EXISTS source ON document TYPE string;
DEFINE FIELD IF NOT EXISTS language ON document TYPE string DEFAULT 'en';
DEFINE FIELD IF NOT EXISTS metadata ON document TYPE option<object>;
DEFINE FIELD IF NOT EXISTS created_at ON document TYPE datetime DEFAULT time::now();
DEFINE FIELD IF NOT EXISTS updated_at ON document TYPE datetime DEFAULT time::now();

-- HNSW index for vector similarity search (768 dims for PhoBERT)
DEFINE INDEX IF NOT EXISTS hnsw_document_embedding ON document FIELDS embedding
  HNSW DIMENSION 768
  DIST COSINE
  EFC 150
  M 12;

-- Index for language-based filtering
DEFINE INDEX IF NOT EXISTS idx_document_language ON document FIELDS language;
