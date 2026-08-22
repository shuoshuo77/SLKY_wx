from logging.config import fileConfig

from alembic import context
from alembic.operations import ops
from sqlalchemy import engine_from_config, pool

from app.config import get_settings
from app.database import Base
from app import models  # noqa: F401

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

config.set_main_option("sqlalchemy.url", get_settings().DATABASE_URL.replace("%", "%%"))
target_metadata = Base.metadata


def _ignore_legacy_comment_drift(context, revision, directives) -> None:
    """Ignore comments managed by the original SQL schema, not ORM metadata."""
    def clean(container) -> None:
        filtered = []
        for operation in container.ops:
            if isinstance(operation, ops.ModifyTableOps):
                clean(operation)
                if operation.ops:
                    filtered.append(operation)
                continue
            if isinstance(operation, (ops.CreateTableCommentOp, ops.DropTableCommentOp)):
                continue
            if isinstance(operation, ops.AlterColumnOp):
                operation.modify_comment = False
                has_change = any((
                    operation.modify_type is not None,
                    operation.modify_nullable is not None,
                    operation.modify_server_default is not False,
                    operation.modify_name is not None,
                ))
                if not has_change:
                    continue
            filtered.append(operation)
        container.ops = filtered

    for directive in directives:
        clean(directive.upgrade_ops)


def run_migrations_offline() -> None:
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_comments=False,
        process_revision_directives=_ignore_legacy_comment_drift,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_comments=False,
            process_revision_directives=_ignore_legacy_comment_drift,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
