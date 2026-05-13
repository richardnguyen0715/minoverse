# Issue 004 — SQLAlchemy Reserved Attribute: `metadata` on DeclarativeBase

**Category:** Backend / ORM  
**Fixed in:** early Phase 0 (initial fix)  
**Files changed:** `apps/api/src/knowledge/entities/resource.py`

---

## Symptom

Alembic or application startup raises:

```
sqlalchemy.exc.InvalidRequestError: Attribute name 'metadata' is reserved
when using the Declarative API.
```

The stack trace points to the ORM model class definition.

---

## Root Cause

SQLAlchemy's `DeclarativeBase` uses `metadata` internally as a class attribute (it holds the `MetaData` object for schema introspection). Defining a column named `metadata` on any model class shadows this reserved attribute:

```python
# ❌ Broken
class Resource(Base):
    metadata: Mapped[dict] = mapped_column(JSONB)  # shadows Base.metadata!
```

---

## Fix

Use a different Python attribute name and map it explicitly to the `"metadata"` database column name via `mapped_column`:

```python
# ✅ Fixed
class Resource(Base):
    extra_metadata: Mapped[dict | None] = mapped_column("metadata", JSONB)
    #               ^^^^^^^^^^^^^^^^^                    ^^^^^^^^^^^
    #               Python attr name                     DB column name
```

**Critical follow-on:** Any `INSERT ... ON CONFLICT DO UPDATE SET` statement that uses raw column names must use the **DB column name** (`"metadata"`), not the Python attribute name (`"extra_metadata"`):

```python
# ✅ Correct — use DB column name in on_conflict_do_update
stmt = insert(Resource).on_conflict_do_update(
    set_={"metadata": values["extra_metadata"]}  # DB name, not Python name
)
```

---

## Prevention Checklist

- [ ] Never name an ORM column `metadata`, `registry`, `__tablename__`, or any other SQLAlchemy reserved name.
- [ ] Other reserved names to avoid: `_sa_class_manager`, `_sa_registry`, `__mapper__`.
- [ ] When renaming a Python attr from the DB column name, always update raw SQL / `on_conflict_do_update` `set_=` dicts to use the DB column name.
- [ ] Pattern to remember: `mapped_column("db_col_name", Type)` maps `python_attr` → `"db_col_name"` in SQL.
