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
from sqlalchemy.dialects import postgresql
from sqlalchemy.ext import asyncio as pq_asyncio

from ndk import types
from ndk.event import event, event_builder, event_filter
from ndk.relay.event_repo import event_repo

logger = logging.getLogger(__name__)

METADATA = sqlalchemy.MetaData()
EVENTS_TABLE = sqlalchemy.Table(
    "events",
    METADATA,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True, autoincrement=True),
    sqlalchemy.Column("event_id", sqlalchemy.String(64)),
    sqlalchemy.Column("pubkey", sqlalchemy.String(64)),
    sqlalchemy.Column("created_at", sqlalchemy.Integer),
    sqlalchemy.Column("kind", sqlalchemy.Integer),
    sqlalchemy.Column("content", sqlalchemy.TEXT),
    sqlalchemy.Column("sig", sqlalchemy.String(128)),
    sqlalchemy.UniqueConstraint("event_id"),
)

TAGS_TABLE = sqlalchemy.Table(
    "tags",
    METADATA,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True, autoincrement=True),
    sqlalchemy.Column("identifier", sqlalchemy.String),
    sqlalchemy.Column("value", sqlalchemy.String),
    sqlalchemy.Column("additional_data", postgresql.ARRAY(sqlalchemy.String)),
    sqlalchemy.Index("identifier", "value"),
)

# Create the bridge table
EVENT_TAGS_TABLE = sqlalchemy.Table(
    "event_tags",
    METADATA,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True, autoincrement=True),
    sqlalchemy.Column(
        "event_id",
        sqlalchemy.Integer,
        sqlalchemy.ForeignKey("events.id", ondelete="CASCADE"),
    ),
    sqlalchemy.Column("tag_id", sqlalchemy.Integer, sqlalchemy.ForeignKey("tags.id")),
)


class PostgresEventRepo(event_repo.EventRepo):
    _engine: pq_asyncio.AsyncEngine

    def __init__(self, engine: pq_asyncio.AsyncEngine):
        self._engine = engine
        super().__init__()

    @classmethod
    async def create_engine(
        cls, host, port, user, password, database
    ) -> pq_asyncio.AsyncEngine:
        engine = pq_asyncio.create_async_engine(
            f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{database}"
        )
        return engine

    @classmethod
    async def create(cls, host, port, user, password, database):
        engine = await cls.create_engine(host, port, user, password, database)

        async with engine.begin() as conn:  # transaction
            await conn.run_sync(
                METADATA.drop_all,
                tables=[EVENT_TAGS_TABLE, TAGS_TABLE, EVENTS_TABLE],
                checkfirst=True,
            )
            await conn.run_sync(METADATA.create_all)

        logger.info("Database initialized")
        return PostgresEventRepo(engine)

    async def _persist(self, ev: event.Event) -> types.EventID:
        async with self._engine.begin() as conn:
            event_insert_stmt = (
                postgresql.insert(EVENTS_TABLE)
                .values(
                    event_id=ev.id,
                    pubkey=ev.pubkey,
                    created_at=ev.created_at,
                    kind=ev.kind,
                    content=ev.content,
                    sig=ev.sig,
                )
                .on_conflict_do_nothing(index_elements=[EVENTS_TABLE.c.event_id])
                .returning(EVENTS_TABLE.c.id)
            )

            insert_result = await conn.execute(event_insert_stmt)

            # if it is already in the db, do nothing
            if insert_result.rowcount == 0:
                return ev.id

            ev_id = insert_result.scalar()

            for tag in ev.tags:
                if len(tag) == 0:
                    continue

                # Check for existing tag_id
                tag_select_stmt = sqlalchemy.select(TAGS_TABLE.c.id).where(
                    sqlalchemy.and_(
                        TAGS_TABLE.c.identifier == tag[0],
                        TAGS_TABLE.c.value == tag[1],
                        TAGS_TABLE.c.additional_data == tag[2:],
                    )
                )

                tag_select_result = (await conn.execute(tag_select_stmt)).fetchone()
                if tag_select_result is None:
                    # Insert the tag if it doesn't exist
                    tag_insert_stmt = (
                        sqlalchemy.insert(TAGS_TABLE)
                        .values(
                            identifier=tag[0],
                            value=tag[1],
                            additional_data=tag[2:],
                        )
                        .returning(TAGS_TABLE.c.id)
                    )

                    tag_id = (await conn.execute(tag_insert_stmt)).scalar()

                else:
                    tag_id = tag_select_result[0]

                # Always insert tags even if they are a duplicate as we need to include
                # the duplicate in the reconstruction
                tag_event_insert_stmt = sqlalchemy.insert(EVENT_TAGS_TABLE).values(
                    event_id=ev_id,
                    tag_id=tag_id,
                )
                await conn.execute(tag_event_insert_stmt)

            await conn.commit()

            return ev.id

    def tag_query_from(self, identifier: str, tag_list: list[str]):
        tag_id_query = sqlalchemy.select(TAGS_TABLE.c.id).where(
            sqlalchemy.and_(
                TAGS_TABLE.c.identifier == identifier, TAGS_TABLE.c.value.in_(tag_list)
            )
        )

        subquery = (
            sqlalchemy.select(EVENT_TAGS_TABLE.c.event_id)
            .select_from(
                sqlalchemy.join(
                    TAGS_TABLE,
                    EVENT_TAGS_TABLE,
                    TAGS_TABLE.c.id == EVENT_TAGS_TABLE.c.tag_id,
                )
            )
            .where(TAGS_TABLE.c.id.in_(tag_id_query))
        )

        return EVENTS_TABLE.c.id.in_(subquery)

    async def get(self, fltrs: list[event_filter.EventFilter]) -> list[event.Event]:
        query = (
            sqlalchemy.select(
                EVENTS_TABLE.c.event_id,
                EVENTS_TABLE.c.pubkey,
                EVENTS_TABLE.c.created_at,
                EVENTS_TABLE.c.kind,
                EVENTS_TABLE.c.content,
                EVENTS_TABLE.c.sig,
                sqlalchemy.text(
                    "string_agg(CONCAT_WS('__', tags.identifier, tags.value, array_to_string(tags.additional_data, ',')), ',' ORDER BY event_tags.id ASC) as tags_combined"
                ),
            )
            .select_from(
                EVENTS_TABLE.outerjoin(EVENT_TAGS_TABLE).outerjoin(
                    TAGS_TABLE, EVENT_TAGS_TABLE.c.tag_id == TAGS_TABLE.c.id
                )
            )
            .group_by(
                EVENTS_TABLE.c.event_id,
                EVENTS_TABLE.c.pubkey,
                EVENTS_TABLE.c.created_at,
                EVENTS_TABLE.c.kind,
                EVENTS_TABLE.c.content,
                EVENTS_TABLE.c.sig,
            )
        )

        queries = []
        limit = float("-inf")
        for f in fltrs:
            conditions = []
            if f.ids:
                conditions.append(
                    sqlalchemy.or_(
                        EVENTS_TABLE.c.event_id.in_(f.ids),
                        sqlalchemy.or_(
                            *[
                                EVENTS_TABLE.c.event_id.startswith(prefix)
                                for prefix in f.ids
                            ]
                        ),
                    )
                )

            if f.authors:
                conditions.append(
                    sqlalchemy.or_(
                        EVENTS_TABLE.c.pubkey.in_(f.authors),
                        sqlalchemy.or_(
                            *[
                                EVENTS_TABLE.c.pubkey.startswith(prefix)
                                for prefix in f.authors
                            ]
                        ),
                    )
                )

            if f.kinds:
                conditions.append(EVENTS_TABLE.c.kind.in_(f.kinds))

            if f.generic_tags:
                for k, v in f.generic_tags.items():
                    conditions.append(self.tag_query_from(k, v))

            if f.since:
                conditions.append(EVENTS_TABLE.c.created_at > f.since)  # type: ignore[arg-type]

            if f.until:
                conditions.append(EVENTS_TABLE.c.created_at < f.until)  # type: ignore[arg-type]

            if f.limit:
                limit = max(limit, f.limit)

            queries.append(sqlalchemy.and_(*conditions))

        final = query.where(sqlalchemy.or_(*queries)).order_by(
            sqlalchemy.desc(EVENTS_TABLE.c.created_at)
        )
        if limit != float("-inf"):
            final = final.limit(int(limit))
        # query_str = final.compile(dialect=self._engine.dialect).string
        # logger.debug(query_str)

        async with self._engine.connect() as conn:
            result = (await conn.execute(final)).fetchall()

            return [
                event_builder.from_validated_dict(
                    {
                        "id": row[0],
                        "pubkey": row[1],
                        "created_at": row[2],
                        "kind": row[3],
                        "content": row[4],
                        "sig": row[5],
                        "tags": [
                            tag.split("__")[:-1]
                            if tag.endswith("__")
                            else tag.split("__")
                            for tag in row[6].split(",")
                            if row[6]
                        ],
                    }
                )
                for row in result
            ]

    async def remove(self, event_id: types.EventID):
        async with self._engine.begin() as conn:
            select_stmt = sqlalchemy.select(EVENTS_TABLE).where(
                EVENTS_TABLE.c.event_id == event_id
            )

            existing_ev = (await conn.execute(select_stmt)).fetchone()

            if not existing_ev:
                raise ValueError(f"Event {event_id} does not exist")

            delete_stmt = EVENTS_TABLE.delete().where(
                EVENTS_TABLE.c.event_id == event_id
            )
            await conn.execute(delete_stmt)
