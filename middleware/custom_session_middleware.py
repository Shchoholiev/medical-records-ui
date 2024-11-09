import uuid
from django.utils.deprecation import MiddlewareMixin
from services.cosmosdb_helper import get_session_data, save_session_data

class CosmosDBSessionMiddleware(MiddlewareMixin):
    def process_request(self, request):
        session_id = request.COOKIES.get('sessionid', str(uuid.uuid4()))
        session_data = get_session_data(session_id)
        request.session = session_data or {}

    def process_response(self, request, response):
        session_id = request.COOKIES.get('sessionid', str(uuid.uuid4()))
        save_session_data(session_id, request.session)
        response.set_cookie('sessionid', session_id)
        return response
