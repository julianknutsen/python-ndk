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

from ndk import serialize
from ndk.event import event
from relay.event_repo import event_repo

logger = logging.getLogger(__name__)

METADATA = sqlalchemy.MetaData()
EVENTS_TABLE = sqlalchemy.Table(
    "events",
    METADATA,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True, autoincrement=True),
    sqlalchemy.Column("event_id", sqlalchemy.String),
    sqlalchemy.Column("pubkey", sqlalchemy.String),
    sqlalchemy.Column("created_at", sqlalchemy.Integer),
    sqlalchemy.Column("kind", sqlalchemy.Integer),
    sqlalchemy.Column("content", sqlalchemy.String),
    sqlalchemy.Column("sig", sqlalchemy.String),
    sqlalchemy.Column("serialized", sqlalchemy.String),
)

TAGS_TABLE = sqlalchemy.Table(
    "tags",
    METADATA,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True, autoincrement=True),
    sqlalchemy.Column("identifier", sqlalchemy.String),
    sqlalchemy.Column("value", sqlalchemy.String),
    sqlalchemy.UniqueConstraint("identifier", "value", name="uq_identifier_value"),
)

# Create the bridge table
EVENT_TAGS_TABLE = sqlalchemy.Table(
    "event_tags",
    METADATA,
    sqlalchemy.Column(
        "event_id", sqlalchemy.Integer, sqlalchemy.ForeignKey("events.id")
    ),
    sqlalchemy.Column("tag_id", sqlalchemy.Integer, sqlalchemy.ForeignKey("tags.id")),
    sqlalchemy.PrimaryKeyConstraint("event_id", "tag_id"),
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
        logger.debug([row[:2] for row in ev.tags])
        async with self._engine.begin() as conn:
            # if it is already in the db, do nothing
            select_stmt = sqlalchemy.select(EVENTS_TABLE).where(
                EVENTS_TABLE.c.event_id == ev.id
            )

            if (await conn.execute(select_stmt)).fetchone():
                return ev.id

            event_insert_stmt = postgresql.insert(EVENTS_TABLE).values(
                event_id=ev.id,
                pubkey=ev.pubkey,
                created_at=ev.created_at,
                kind=ev.kind,
                content=ev.content,
                sig=ev.sig,
                serialized=serialize.serialize_as_str(ev),
            )

            event_id = (await conn.execute(event_insert_stmt)).inserted_primary_key[0]

            for tag in ev.tags:
                if len(tag) == 0:
                    continue

                # Check if the tag already exists
                select_stmt = sqlalchemy.select(TAGS_TABLE).where(
                    (TAGS_TABLE.c.identifier == tag[0]) & (TAGS_TABLE.c.value == tag[1])
                )

                existing_tag = (await conn.execute(select_stmt)).fetchone()

                if existing_tag:
                    # Use the existing tag if it already exists
                    tag_id = existing_tag.id
                else:
                    # Insert the tag if it doesn't exist
                    tag_insert_stmt = sqlalchemy.insert(TAGS_TABLE).values(
                        identifier=tag[0],
                        value=tag[1],
                    )

                    # Get the tag_id of the inserted tag
                    tag_id = (await conn.execute(tag_insert_stmt)).inserted_primary_key[
                        0
                    ]

                # Insert the event_tag relationship
                tag_event_insert_stmt = sqlalchemy.insert(EVENT_TAGS_TABLE).values(
                    event_id=event_id,
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

    async def get(self, fltrs: list[dict]) -> list[event.SignedEvent]:
        query = sqlalchemy.select(EVENTS_TABLE)

        queries = []
        limit = float("-inf")
        for f in fltrs:
            conditions = []
            if "ids" in f:
                conditions.append(EVENTS_TABLE.c.event_id.in_(f["ids"]))

            if "authors" in f:
                conditions.append(EVENTS_TABLE.c.pubkey.in_(f["authors"]))

            if "kinds" in f:
                conditions.append(EVENTS_TABLE.c.kind.in_(f["kinds"]))

            if "#e" in f:
                conditions.append(self.tag_query_from("e", f["#e"]))

            if "#p" in f:
                conditions.append(self.tag_query_from("p", f["#p"]))

            if "since" in f:
                conditions.append(EVENTS_TABLE.c.created_at > f["since"])

            if "until" in f:
                conditions.append(EVENTS_TABLE.c.created_at < f["until"])

            if "limit" in f:
                limit = max(limit, f["limit"])

            queries.append(sqlalchemy.and_(*conditions))

        final = query.where(sqlalchemy.or_(*queries)).order_by(
            sqlalchemy.desc(EVENTS_TABLE.c.created_at)
        )
        if limit != float("-inf"):
            final = final.limit(int(limit))
        logger.debug(final.compile(dialect=self._engine.dialect).string)

        async with self._engine.connect() as conn:
            result = (await conn.execute(final)).fetchall()

            return [
                event.SignedEvent.from_dict(serialize.deserialize(row[7]))
                for row in result
            ]
