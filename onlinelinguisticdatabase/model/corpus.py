# Copyright 2013 Joel Dunham
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

"""Corpus model"""

from sqlalchemy import Table, Column, Sequence, ForeignKey
from sqlalchemy.types import Integer, Unicode, UnicodeText, DateTime, Boolean
from sqlalchemy.orm import relation
from onlinelinguisticdatabase.model.meta import Base, now
import logging
log = logging.getLogger(name=__name__)

corpusform_table = Table('corpusform', Base.metadata,
    Column('id', Integer, Sequence('corpusform_seq_id', optional=True), primary_key=True),
    Column('corpus_id', Integer, ForeignKey('corpus.id')),
    Column('form_id', Integer, ForeignKey('form.id')),
    Column('datetimeModified', DateTime(), default=now),
    mysql_charset='utf8'
)

corpustag_table = Table('corpustag', Base.metadata,
    Column('id', Integer, Sequence('corpustag_seq_id', optional=True), primary_key=True),
    Column('corpus_id', Integer, ForeignKey('corpus.id')),
    Column('tag_id', Integer, ForeignKey('tag.id')),
    Column('datetimeModified', DateTime(), default=now),
    mysql_charset='utf8'
)

class Corpus(Base):

    __tablename__ = 'corpus'
    __table_args__ = {'mysql_charset': 'utf8'}

    def __repr__(self):
        return "<Corpus (%s)>" % self.id

    id = Column(Integer, Sequence('corpus_seq_id', optional=True), primary_key=True)
    UUID = Column(Unicode(36))
    name = Column(Unicode(255))
    description = Column(UnicodeText)
    content = Column(UnicodeText)
    enterer_id = Column(Integer, ForeignKey('user.id'))
    enterer = relation('User', primaryjoin='Corpus.enterer_id==User.id')
    modifier_id = Column(Integer, ForeignKey('user.id'))
    modifier = relation('User', primaryjoin='Corpus.modifier_id==User.id')
    formSearch_id = Column(Integer, ForeignKey('formsearch.id'))
    formSearch = relation('FormSearch')
    datetimeEntered = Column(DateTime)
    datetimeModified = Column(DateTime, default=now)
    tags = relation('Tag', secondary=corpustag_table)
    forms = relation('Form', secondary=corpusform_table, backref='corpora')

    # ``files`` attribute holds references to ``CorpusFile`` models, not ``File``
    # models.  This is a one-to-many relation, like form.translations.
    files = relation('CorpusFile', backref='corpus', cascade='all, delete, delete-orphan')

    def getDict(self):
        """Return a Python dictionary representation of the Corpus.  This
        facilitates JSON-stringification, cf. utils.JSONOLDEncoder.  Relational
        data are truncated, e.g., corpusDict['elicitor'] is a dict with keys
        for 'id', 'firstName' and 'lastName' (cf. getMiniUserDict above) and
        lacks keys for other attributes such as 'username',
        'personalPageContent', etc.
        """

        return {
            'id': self.id,
            'UUID': self.UUID,
            'name': self.name,
            'description': self.description,
            'content': self.content,
            'enterer': self.getMiniUserDict(self.enterer),
            'modifier': self.getMiniUserDict(self.modifier),
            'formSearch': self.getMiniFormSearchDict(self.formSearch),
            'datetimeEntered': self.datetimeEntered,
            'datetimeModified': self.datetimeModified,
            'tags': self.getTagsList(self.tags),
            'files': self.getCorpusFilesList(self.files)
        }

    def getFullDict(self):
        result = self.getDict()
        result['forms'] = self.getFormsList(self.forms)
        return result


class CorpusFile(Base):
    """Represents a corpus' forms written to disk in a certain format."""

    __tablename__ = 'corpusfile'
    __table_args__ = {'mysql_charset': 'utf8'}

    def __repr__(self):
        return "<CorpusFile (%s)>" % self.id

    id = Column(Integer, Sequence('corpusfile_seq_id', optional=True), primary_key=True)
    corpus_id = Column(Integer, ForeignKey('corpus.id'))
    filename = Column(Unicode(255))
    format = Column(Unicode(255))
    creator_id = Column(Integer, ForeignKey('user.id'))
    creator = relation('User', primaryjoin='CorpusFile.creator_id==User.id')
    modifier_id = Column(Integer, ForeignKey('user.id'))
    modifier = relation('User', primaryjoin='CorpusFile.modifier_id==User.id')
    datetimeModified = Column(DateTime, default=now)
    datetimeCreated = Column(DateTime)
    restricted = Column(Boolean)

    def getDict(self):
        """Return a Python dictionary representation of the corpus file."""
        return {
            'id': self.id,
            'corpus_id': self.corpus_id,
            'filename': self.filename,
            'format': self.format,
            'creator': self.getMiniUserDict(self.creator),
            'modifier': self.getMiniUserDict(self.modifier),
            'datetimeModified': self.datetimeModified,
            'datetimeEntered': self.datetimeEntered,
            'restricted': self.restricted
        }
