from wsgi import application  # импорт из вашего проекта
from vercel_wsgi import handle_request

def handler(request, context):
    return handle_request(request, application)