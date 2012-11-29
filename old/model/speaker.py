"""Speaker model"""

from sqlalchemy import Table, Column, Sequence, ForeignKey
from sqlalchemy.types import Integer, Unicode, UnicodeText, Date, DateTime
from sqlalchemy.orm import relation, backref
from old.model.meta import Base, now

class Speaker(Base):

    __tablename__ = 'speaker'

    def __repr__(self):
        return '<Speaker (%s)>' % self.id

    id = Column(Integer, Sequence('speaker_seq_id', optional=True), primary_key=True)
    firstName = Column(Unicode(255))
    lastName = Column(Unicode(255))
    dialect = Column(Unicode(255))
    speakerPageContent = Column(UnicodeText)
    datetimeModified = Column(DateTime, default=now)