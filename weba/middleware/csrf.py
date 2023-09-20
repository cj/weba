import uuid

from fastapi import Request
from securecookies.middleware import SecureCookiesMiddleware
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import PlainTextResponse


class CSRFTokenError(Exception):
    pass


class CSRFMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint):
        # middleware is built and instantiated once during application creation.
        # since we don't want to recreate the middleware (seems not nice), we need to
        # loop through the entire ASGI stack to find our SecureCookieMiddleware.
        # this might be excessive but ¯\_(ツ)_/¯
        if not hasattr(self, "_secure_middleware"):
            app = request.scope["app"].middleware_stack
            while not isinstance(app, SecureCookiesMiddleware):
                try:
                    app = app.app
                except AttributeError as e:
                    raise Exception(  # sourcery skip: raise-specific-error
                        "You must use SecureCSRFMiddleware in conjunction with" " SecureCookiesMiddleware."
                    ) from e

            self._secure_middleware = app

        host = request.headers.get("host", None)
        user_agent = request.headers.get("user-agent", None)
        session_id = request.session.setdefault("uuid", uuid.uuid4().hex)
        session_user_agent = request.session.setdefault("user_agent", user_agent)

        if request.method in ("GET", "HEAD", "OPTIONS", "TRACE"):
            csrf_token = self._secure_middleware.encrypt(f"{session_id}||{host}||{user_agent}")

            request.session["csrf_token"] = csrf_token
        else:
            if user_agent != session_user_agent:
                return PlainTextResponse("Invalid Session", status_code=403)

            try:
                decoded_csrf_token = self._secure_middleware.decrypt(request.headers.get("x-csrf-token", ""))
                csrf_session_id, csrf_host, csrf_user_agent = decoded_csrf_token.split("||")
                if session_id != csrf_session_id or host != csrf_host or user_agent != csrf_user_agent:
                    return PlainTextResponse("Invalid CSRF Token", status_code=403)
            except CSRFTokenError:
                return PlainTextResponse("Invalid CSRF Token", status_code=403)

        return await call_next(request)
