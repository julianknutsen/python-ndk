# Copyright 2023 Julian Knutsen
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the “Software”), to deal in
# the Software without restriction, including without limitation the rights to use,
# copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the
# Software, and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
# OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.

import logging

import sqlalchemy
from sqlalchemy.dialects.postgresql import insert as pq_insert
from sqlalchemy.ext import asyncio as pq_asyncio

from ndk import serialize
from ndk.event import event
from relay.event_repo import event_repo

logger = logging.getLogger(__name__)

METADATA = sqlalchemy.MetaData()
EVENTS_TABLE = sqlalchemy.Table(
    "events",
    METADATA,
    sqlalchemy.Column("id", sqlalchemy.String, primary_key=True),
    sqlalchemy.Column("pubkey", sqlalchemy.String),
    sqlalchemy.Column("created_at", sqlalchemy.Integer),
    sqlalchemy.Column("kind", sqlalchemy.Integer),
    sqlalchemy.Column("tags", sqlalchemy.ARRAY(sqlalchemy.String)),
    sqlalchemy.Column("content", sqlalchemy.String),
    sqlalchemy.Column("sig", sqlalchemy.String),
    sqlalchemy.Column("encoded_tags", sqlalchemy.String),
)


class PostgresEventRepo(event_repo.EventRepo):
    _engine: pq_asyncio.AsyncEngine

    def __init__(self, engine: pq_asyncio.AsyncEngine):
        self._engine = engine

    @classmethod
    async def create(cls, host, port, user, password, database):
        engine = pq_asyncio.create_async_engine(
            f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{database}"
        )

        async with engine.begin() as conn:  # transaction
            await conn.run_sync(METADATA.drop_all)
            await conn.run_sync(METADATA.create_all)

        logger.info("Database initialized")
        return PostgresEventRepo(engine)

    async def add(self, ev: event.SignedEvent) -> event.EventID:
        async with self._engine.connect() as conn:
            insert_stmt = pq_insert(EVENTS_TABLE).values(
                id=ev.id,
                pubkey=ev.pubkey,
                created_at=ev.created_at,
                kind=ev.kind,
                tags=ev.tags,
                content=ev.content,
                sig=ev.sig,
                encoded_tags=serialize.serialize_as_str(ev.tags),
            )
            on_conflict_stmt = insert_stmt.on_conflict_do_nothing()

            await conn.execute(on_conflict_stmt)
            await conn.commit()
            return event.EventID(ev.id)

    async def get(self, fltrs: list[dict]) -> list[event.SignedEvent]:
        query = sqlalchemy.select(EVENTS_TABLE)

        queries = []
        limit = float("inf")
        for f in fltrs:
            conditions = []
            if "ids" in f:
                conditions.append(EVENTS_TABLE.c.id.in_(f["ids"]))

            if "authors" in f:
                conditions.append(EVENTS_TABLE.c.pubkey.in_(f["authors"]))

            if "kinds" in f:
                conditions.append(EVENTS_TABLE.c.kind.in_(f["kinds"]))

            if "#e" in f:
                conditions.append(EVENTS_TABLE.c.tags.any("{#e}").in_(f["#e"]))

            if "#p" in f:
                conditions.append(EVENTS_TABLE.c.tags.any("{#p}").in_(f["#p"]))

            if "since" in f:
                conditions.append(EVENTS_TABLE.c.created_at >= f["since"])

            if "until" in f:
                conditions.append(EVENTS_TABLE.c.created_at < f["until"])

            if "limit" in f:
                limit = max(limit, f["limit"])

            assert len(conditions) > 0, f
            queries.append(sqlalchemy.and_(*conditions))

        assert len(queries) > 0
        final = query.where(sqlalchemy.or_(*queries)).order_by(
            sqlalchemy.desc(EVENTS_TABLE.c.created_at)
        )
        if limit != float("inf"):
            final = final.limit(int(limit))
        logger.debug(final.compile(dialect=self._engine.dialect).string)

        async with self._engine.connect() as conn:
            result = (await conn.execute(final)).fetchall()

            return [
                event.SignedEvent(
                    id=row[0],
                    pubkey=row[1],
                    created_at=row[2],
                    kind=row[3],
                    tags=serialize.deserialize(row[7]),
                    content=row[5],
                    sig=row[6],
                )
                for row in result
            ]
