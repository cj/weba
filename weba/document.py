from typing import Any, cast

import dominate
import dominate.tags as t


class DocumentOverride(object):
    body: t.body
    head: t.head


WebaDocument = type("WebaDocument", (dominate.document, DocumentOverride), {})


def get_document(
    doctype: str = "<!DOCTYPE html>",
    *args: Any,
    **kwargs: Any,
):
    doc = cast(WebaDocument, dominate.document(*args, doctype=doctype, **kwargs))

    with doc.head:
        t.meta(charset="utf-8")
        t.meta(name="viewport", content="width=device-width, initial-scale=1")

    return doc
