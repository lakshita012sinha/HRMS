"""
Security middleware: prevent browser from caching authenticated pages.

When a user logs out and another user logs in, pressing the browser Back
button must NOT show pages from the previous session.  Setting
Cache-Control: no-store on every HTML response achieves this because the
browser is forced to re-fetch every page — and re-fetch triggers the
JavaScript auth guard which redirects to /login/ if no valid token is found.
"""


class NoCacheMiddleware:
    """
    Adds no-cache headers to every HTML response so that the browser never
    serves a cached page after logout.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Apply to HTML pages only (not API responses, static files, etc.)
        content_type = response.get('Content-Type', '')
        if 'text/html' in content_type:
            response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'

        return response
