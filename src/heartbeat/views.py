from collections import OrderedDict
from importlib import import_module
from django.http import HttpResponse, JsonResponse

from .auth import auth
from .settings import HEARTBEAT


def index(request):
    return HttpResponse(content='all good in the hood')


@auth
def details(request):
    response = {}
    for checker in HEARTBEAT['checkers']:
        checker_module = import_module(checker)
        checker_name = checker_module.__name__.split('.')[-1]
        data = checker_module.check(request)
        response.update({checker_name: data})
    return JsonResponse({'checkers': OrderedDict(sorted(response.items()))})
