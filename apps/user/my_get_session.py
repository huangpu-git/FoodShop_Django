import jsonpickle
from django.http import request


def get_session(request):
    user = ''
    if 'user' in request.session:
        user = jsonpickle.loads(request.session.get('user'))
    return {'user': user}
