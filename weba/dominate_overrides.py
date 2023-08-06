def clean_attribute(attribute: str):
    """
    Normalize attribute names for shorthand and work arounds for limitations
    in Python's syntax
    """

    # Shorthand
    attribute = {
        "cls": "class",
        "className": "class",
        "class_name": "class",
        "klass": "class",
        "fr": "for",
        "html_for": "for",
        "htmlFor": "for",
        "phor": "for",
    }.get(attribute, attribute)

    # Workaround for Python's reserved words
    if attribute != "_" and attribute[0] == "_":
        attribute = attribute[1:]

    # Workaround for dash
    special_prefix = any(
        attribute.startswith(x)
        for x in (
            "data_",
            "aria_",
            # htmx
            "hx_",
            # alpine
            "x_",
        )
    )
    if attribute in {"http_equiv"} or special_prefix:
        attribute = attribute.replace("_", "-").lower()

    # if starts and ends with _, replace the first with a : and remove the last
    if attribute.startswith("_") and attribute.endswith("__"):
        attribute = attribute.replace("_", ":", 1).replace("__", "")

    # replace with @
    if attribute != "_" and attribute.startswith("_"):
        attribute = attribute.replace("_", "@")

    if attribute.startswith("hx-"):
        # : is for javascript events
        # :: is for htmx events
        attribute = attribute.replace("---", "::").replace("--", ":")

    # Workaround for colon
    if attribute.split("_")[0] in ("xlink", "xml", "xmlns"):
        attribute = attribute.replace("_", ":", 1).lower()

    return attribute
