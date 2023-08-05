from typing import Any, cast

import dominate
import dominate.tags as t


class DocumentOverride(object):
    body: t.body
    head: t.head


WEBADocument = type("WEBADocument", (dominate.document, DocumentOverride), {})


def get_document(
    title: str = "weba",
    doctype: str = "<!DOCTYPE html>",
    *args: Any,
    **kwargs: Any,
):
    doc = cast(WEBADocument, dominate.document(title, doctype, *args, **kwargs))

    with doc.head:
        t.meta(charset="utf-8")
        t.meta(name="viewport", content="width=device-width, initial-scale=1")
        t.title(title)

    return doc
