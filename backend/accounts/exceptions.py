import logging

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler

logger = logging.getLogger(__name__)


def api_exception_handler(exc, context):
    """DRF's default handler only converts APIException, Http404, and
    PermissionDenied into a response - anything else (a bare exception from
    a library, a storage/database error, ...) would otherwise propagate all
    the way up to Django's own error handling and come back as a raw HTML
    500 page, even on an endpoint that returns JSON everywhere else. This
    exists so every API response is JSON regardless of what actually broke,
    while still logging the real exception server-side."""
    response = drf_exception_handler(exc, context)
    if response is not None:
        return response

    logger.exception("Unhandled exception in API view", exc_info=exc)
    return Response(
        {"error": "An unexpected error occurred. Please try again later."},
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
