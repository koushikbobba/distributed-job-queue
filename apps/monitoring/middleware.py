import uuid
import logging

logger = logging.getLogger(__name__)


class CorrelationIdMiddleware:
    """
    Middleware that extracts or generates a unique X-Correlation-ID for each request,
    attaching it to the request and response headers for end-to-end distributed tracing.
    """

    HEADER_NAME = "HTTP_X_CORRELATION_ID"
    RESPONSE_HEADER = "X-Correlation-ID"

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        correlation_id = request.META.get(self.HEADER_NAME) or str(uuid.uuid4())
        request.correlation_id = correlation_id

        response = self.get_response(request)
        response[self.RESPONSE_HEADER] = correlation_id
        return response
