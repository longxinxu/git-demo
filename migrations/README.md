# Migrations

- `001_content_refactor.sql`: 创建新实体（users/content_items/content_versions/reviews/reports/tags/content_tag_rel/favorites）并将旧 `contents` 数据回填到新模型。
- 运行方式（SQLite）：

```bash
sqlite3 data.db < migrations/001_content_refactor.sql
```

应用启动时 `app.db.init_db()` 也会执行同等迁移与回填逻辑，避免遗漏历史数据。
