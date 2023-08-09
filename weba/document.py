from typing import Any

import dominate
import dominate.tags as t

from .build import build
from .env import env


class WebaDocument(dominate.document):
    body: t.body
    head: t.head

    def __init__(self, title: str = "Weba", doctype: str = "<!DOCTYPE html>", *args: Any, **kwargs: Any):
        self._weba_head_rendered = False

        super().__init__(*args, title=title, doctype=doctype, **kwargs)  # type: ignore

    def render(self, indent: str = "  ", pretty: bool = True, xhtml: bool = False):
        self._render_default_head()

        return super().render(indent, pretty, xhtml)

    def _render_default_head(self) -> None:
        if self._weba_head_rendered:
            return

        with self.head:
            t.meta(charset="utf-8")
            t.meta(name="viewport", content="width=device-width, initial-scale=1")
            t.link(
                rel="stylesheet",
                href=f"{env.static_url}/styles.css?v={build.static_dir_hash}",
                type="text/css",
            )
            self._weba_head_rendered = True


def get_document(
    doctype: str = "<!DOCTYPE html>",
    *args: Any,
    **kwargs: Any,
):
    doc = WebaDocument(*args, doctype=doctype, **kwargs)

    if env.htmx_boost:
        doc.body["hx-boost"] = "true"

    if env.live_reload:
        doc.body["ws-connect"] = env.live_reload_url
        doc.body["hx-on"] = "htmx:wsClose: htmx.ajax('GET', window.location.href, null, {history: 'replace'});"

    return doc
