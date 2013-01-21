import logging
import datetime
import re
import simplejson as json

from pylons import request, response, session, app_globals, config
from pylons.decorators.rest import restrict
from formencode.validators import Invalid
from sqlalchemy.exc import OperationalError, InvalidRequestError
from sqlalchemy.sql import asc

from old.lib.base import BaseController
from old.lib.schemata import SpeakerSchema
import old.lib.helpers as h
from old.lib.SQLAQueryBuilder import SQLAQueryBuilder, OLDSearchParseError
from old.model.meta import Session
from old.model import Speaker

log = logging.getLogger(__name__)

class SpeakersController(BaseController):
    """REST Controller styled on the Atom Publishing Protocol"""

    queryBuilder = SQLAQueryBuilder('Speaker', config=config)

    @h.OLDjsonify
    @restrict('GET')
    @h.authenticate
    def index(self):
        """GET /speakers: Return all speakers."""
        try:
            query = Session.query(Speaker)
            query = h.addOrderBy(query, dict(request.GET), self.queryBuilder)
            return h.addPagination(query, dict(request.GET))
        except Invalid, e:
            response.status_int = 400
            return {'errors': e.unpack_errors()}

    @h.OLDjsonify
    @restrict('POST')
    @h.authenticate
    @h.authorize(['administrator', 'contributor'])
    def create(self):
        """POST /speakers: Create a new speaker."""
        try:
            schema = SpeakerSchema()
            values = json.loads(unicode(request.body, request.charset))
            data = schema.to_python(values)
            speaker = createNewSpeaker(data)
            Session.add(speaker)
            Session.commit()
            return speaker
        except h.JSONDecodeError:
            response.status_int = 400
            return h.JSONDecodeErrorResponse
        except Invalid, e:
            response.status_int = 400
            return {'errors': e.unpack_errors()}

    @h.OLDjsonify
    @restrict('GET')
    @h.authenticate
    @h.authorize(['administrator', 'contributor'])
    def new(self):
        """GET /speakers/new: Return the data necessary to create a new OLD
        speaker.  NOTHING TO RETURN HERE ...
        """
        return {}

    @h.OLDjsonify
    @restrict('PUT')
    @h.authenticate
    @h.authorize(['administrator', 'contributor'])
    def update(self, id):
        """PUT /speakers/id: Update an existing speaker."""
        speaker = Session.query(Speaker).get(int(id))
        if speaker:
            try:
                schema = SpeakerSchema()
                values = json.loads(unicode(request.body, request.charset))
                data = schema.to_python(values)
                speaker = updateSpeaker(speaker, data)
                # speaker will be False if there are no changes (cf. updateSpeaker).
                if speaker:
                    Session.add(speaker)
                    Session.commit()
                    return speaker
                else:
                    response.status_int = 400
                    return {'error':
                        u'The update request failed because the submitted data were not new.'}
            except h.JSONDecodeError:
                response.status_int = 400
                return h.JSONDecodeErrorResponse
            except Invalid, e:
                response.status_int = 400
                return {'errors': e.unpack_errors()}
        else:
            response.status_int = 404
            return {'error': 'There is no speaker with id %s' % id}

    @h.OLDjsonify
    @restrict('DELETE')
    @h.authenticate
    @h.authorize(['administrator', 'contributor'])
    def delete(self, id):
        """DELETE /speakers/id: Delete an existing speaker."""
        speaker = Session.query(Speaker).get(id)
        if speaker:
            Session.delete(speaker)
            Session.commit()
            return speaker
        else:
            response.status_int = 404
            return {'error': 'There is no speaker with id %s' % id}

    @h.OLDjsonify
    @restrict('GET')
    @h.authenticate
    def show(self, id):
        """GET /speakers/id: Return a JSON object representation of the speaker
        with id=id.

        If the id is invalid, the header will contain a 404 status int and a
        JSON object will be returned.  If the id is unspecified, then Routes
        will put a 404 status int into the header and the default 404 JSON
        object defined in controllers/error.py will be returned.
        """
        speaker = Session.query(Speaker).get(id)
        if speaker:
            return speaker
        else:
            response.status_int = 404
            return {'error': 'There is no speaker with id %s' % id}

    @h.OLDjsonify
    @restrict('GET')
    @h.authenticate
    @h.authorize(['administrator', 'contributor'])
    def edit(self, id):
        """GET /speakers/id/edit: Return the data necessary to update an existing
        OLD speaker; here we return only the speaker and an empty JSON object.
        """
        speaker = Session.query(Speaker).get(id)
        if speaker:
            return {'data': {}, 'speaker': speaker}
        else:
            response.status_int = 404
            return {'error': 'There is no speaker with id %s' % id}


################################################################################
# Speaker Create & Update Functions
################################################################################

def createNewSpeaker(data):
    """Create a new speaker model object given a data dictionary provided by the
    user (as a JSON object).
    """

    speaker = Speaker()
    speaker.firstName = h.normalize(data['firstName'])
    speaker.lastName = h.normalize(data['lastName'])
    speaker.dialect = h.normalize(data['dialect'])
    speaker.pageContent = h.normalize(data['pageContent'])
    speaker.datetimeModified = datetime.datetime.utcnow()
    return speaker

# Global CHANGED variable keeps track of whether an update request should
# succeed.  This global may only be used/changed in the updateSpeaker function
# below.
CHANGED = None

def updateSpeaker(speaker, data):
    """Update the input speaker model object given a data dictionary
    provided by the user (as a JSON object).  If CHANGED is not set to true in
    the course of attribute setting, then None is returned and no update occurs.
    """

    global CHANGED

    def setAttr(obj, name, value):
        if getattr(obj, name) != value:
            setattr(obj, name, value)
            global CHANGED
            CHANGED = True

    # Unicode Data
    setAttr(speaker, 'firstName', h.normalize(data['firstName']))
    setAttr(speaker, 'lastName', h.normalize(data['lastName']))
    setAttr(speaker, 'dialect', h.normalize(data['dialect']))
    setAttr(speaker, 'pageContent', h.normalize(data['pageContent']))

    if CHANGED:
        CHANGED = None      # It's crucial to reset the CHANGED global!
        speaker.datetimeModified = datetime.datetime.utcnow()
        return speaker
    return CHANGED