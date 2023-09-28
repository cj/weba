import json
from typing import Any, Optional

import dominate
import dominate.tags as t
from dominate.util import raw  # type: ignore
from fastapi import Request

from .env import env

SCRIPT_TAGS: Any = []
"""Used to cache the script tags as this is only needed to be ran once and does not change"""


def load_script_tags() -> None:
    if SCRIPT_TAGS:
        return SCRIPT_TAGS

    from .build import build

    files = sorted(build.files.items())

    tags: Any = []

    for file_name, file_hash in files:
        if file_hash == "":
            file_url = f"{env.weba_public_url}/{file_name}"
        else:
            split = file_name.rsplit(".", 1)
            file_url = f"{env.weba_public_url}/{split[0]}-{file_hash}.{split[1]}"

        # If the file is a js file
        if file_url.endswith(".css"):
            # Create a script tag with the file name and hash as key and value
            tags.append(
                t.link(
                    rel="stylesheet",
                    href=file_url,
                    type="text/css",
                )
            )
        elif file_url.endswith("._hs"):
            tags.append(t.script(src=file_url, type="text/hyperscript"))
        else:
            # Create a script tag with the file name and hash as key and value
            tags.append(t.script(src=file_url, type="text/javascript"))

    # FIXME: currently htmx boost does not update the body tag
    # https://github.com/bigskysoftware/htmx/issues/1384
    tags.append(
        t.script(
            raw(
                """
                    document.addEventListener("DOMContentLoaded", function() {
                        document.body.addEventListener('htmx:afterSwap', function(evt) {
                            const parser = new DOMParser();
                            const parsedResponse = parser.parseFromString(evt.detail.xhr.response, "text/html");
                            const bodyAttributes = parsedResponse.getElementsByTagName('body')[0].attributes;
                            for (const attribute of bodyAttributes) {
                                evt.detail.target.setAttribute(attribute.name, attribute.value);
                            }
                        });
                    });
                 """
            )
        )
    )

    SCRIPT_TAGS.extend(tags)

    return SCRIPT_TAGS


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
            t.meta(name="htmx-config", content=f"{json.dumps(env.htmx_config)}")

        self.head.add(load_script_tags())  # type: ignore
        self._weba_head_rendered = True


def weba_document(request: Request) -> WebaDocument:
    return request.scope["weba_document"]


def get_document(
    doctype: str = "<!DOCTYPE html>",
    request: Optional[Request] = None,
    *args: Any,
    **kwargs: Any,
):
    doc = WebaDocument(*args, doctype=doctype, **kwargs)

    doc.body["hx-ext"] = ", ".join(env.htmx_extentions)

    doc.body["class"] = "min-h-screen overflow-x-hidden overflow-y-auto overscroll-y-none flex flex-col"

    if request:
        request.session.setdefault("store", {})
        csrf_token = request.session.get("csrf_token", "")
        doc.body["hx-headers"] = f'{{"X-CSRF-Token": "{csrf_token}"}}'

    if env.htmx_boost:
        doc.body["hx-boost"] = "true"

    if env.live_reload:
        doc.body["ws-connect"] = env.live_reload_url
        # TODO: Fix the build process to stop it loading assets multiple times
        # doc.body["hx-on"] = "htmx:wsClose: htmx.ajax('GET', window.location.href, null, {history: 'replace'});"
        doc.body["hx-on"] = "htmx:wsClose: window.location.reload();"

    return doc
