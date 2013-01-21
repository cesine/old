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
from old.lib.schemata import ElicitationMethodSchema
import old.lib.helpers as h
from old.lib.SQLAQueryBuilder import SQLAQueryBuilder, OLDSearchParseError
from old.model.meta import Session
from old.model import ElicitationMethod

log = logging.getLogger(__name__)

class ElicitationmethodsController(BaseController):
    """REST Controller styled on the Atom Publishing Protocol"""

    queryBuilder = SQLAQueryBuilder('ElicitationMethod', config=config)

    @h.OLDjsonify
    @restrict('GET')
    @h.authenticate
    def index(self):
        """GET /elicitationmethods: Return all elicitation methods."""
        try:
            query = Session.query(ElicitationMethod)
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
        """POST /elicitationmethods: Create a new elicitation method."""
        try:
            schema = ElicitationMethodSchema()
            values = json.loads(unicode(request.body, request.charset))
            result = schema.to_python(values)
            elicitationMethod = createNewElicitationMethod(result)
            Session.add(elicitationMethod)
            Session.commit()
            return elicitationMethod
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
        """GET /elicitationmethods/new: Return the data necessary to create a new OLD
        elicitation method.  NOTHING TO RETURN HERE ...
        """
        return {}

    @h.OLDjsonify
    @restrict('PUT')
    @h.authenticate
    @h.authorize(['administrator', 'contributor'])
    def update(self, id):
        """PUT /elicitationmethods/id: Update an existing elicitation method."""
        elicitationMethod = Session.query(ElicitationMethod).get(int(id))
        if elicitationMethod:
            try:
                schema = ElicitationMethodSchema()
                values = json.loads(unicode(request.body, request.charset))
                state = h.getStateObject(values)
                state.id = id
                data = schema.to_python(values, state)
                elicitationMethod = updateElicitationMethod(elicitationMethod, data)
                # elicitationMethod will be False if there are no changes (cf. updateElicitationMethod).
                if elicitationMethod:
                    Session.add(elicitationMethod)
                    Session.commit()
                    return elicitationMethod
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
            return {'error': 'There is no elicitation method with id %s' % id}

    @h.OLDjsonify
    @restrict('DELETE')
    @h.authenticate
    @h.authorize(['administrator', 'contributor'])
    def delete(self, id):
        """DELETE /elicitationmethods/id: Delete an existing elicitation method."""
        elicitationMethod = Session.query(ElicitationMethod).get(id)
        if elicitationMethod:
            Session.delete(elicitationMethod)
            Session.commit()
            return elicitationMethod
        else:
            response.status_int = 404
            return {'error': 'There is no elicitation method with id %s' % id}

    @h.OLDjsonify
    @restrict('GET')
    @h.authenticate
    def show(self, id):
        """GET /elicitationmethods/id: Return a JSON object representation of the elicitation
        method with id=id.

        If the id is invalid, the header will contain a 404 status int and a
        JSON object will be returned.  If the id is unspecified, then Routes
        will put a 404 status int into the header and the default 404 JSON
        object defined in controllers/error.py will be returned.
        """
        elicitationMethod = Session.query(ElicitationMethod).get(id)
        if elicitationMethod:
            return elicitationMethod
        else:
            response.status_int = 404
            return {'error': 'There is no elicitation method with id %s' % id}

    @h.OLDjsonify
    @restrict('GET')
    @h.authenticate
    @h.authorize(['administrator', 'contributor'])
    def edit(self, id):
        """GET /elicitationmethods/id/edit: Return the data necessary to update an existing
        OLD elicitation method; here we return only the elicitation method and
        an empty JSON object.
        """
        elicitationMethod = Session.query(ElicitationMethod).get(id)
        if elicitationMethod:
            return {'data': {}, 'elicitationMethod': elicitationMethod}
        else:
            response.status_int = 404
            return {'error': 'There is no elicitation method with id %s' % id}


################################################################################
# ElicitationMethod Create & Update Functions
################################################################################

def createNewElicitationMethod(data):
    """Create a new elicitation method model object given a data dictionary
    provided by the user (as a JSON object).
    """

    elicitationMethod = ElicitationMethod()
    elicitationMethod.name = h.normalize(data['name'])
    elicitationMethod.description = h.normalize(data['description'])
    elicitationMethod.datetimeModified = datetime.datetime.utcnow()
    return elicitationMethod

# Global CHANGED variable keeps track of whether an update request should
# succeed.  This global may only be used/changed in the updateElicitationMethod
# function below.
CHANGED = None

def updateElicitationMethod(elicitationMethod, data):
    """Update the input elicitation method model object given a data dictionary
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
    setAttr(elicitationMethod, 'name', h.normalize(data['name']))
    setAttr(elicitationMethod, 'description', h.normalize(data['description']))
    
    if CHANGED:
        CHANGED = None      # It's crucial to reset the CHANGED global!
        elicitationMethod.datetimeModified = datetime.datetime.utcnow()
        return elicitationMethod
    return CHANGED