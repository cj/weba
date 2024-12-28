from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any, Literal, overload

from bs4 import Comment, NavigableString
from bs4 import Tag as Bs4Tag

from .context import current_parent

if TYPE_CHECKING:  # pragma: no cover
    from contextvars import Token

    from bs4 import BeautifulSoup, PageElement
    from bs4.builder import TreeBuilder


class Tag(Bs4Tag):
    @classmethod
    def from_existing_bs4tag(cls, bs4_tag: Bs4Tag) -> Tag:
        new_tag = cls(name=bs4_tag.name, attrs=bs4_tag.attrs)

        for c in bs4_tag.contents:
            if isinstance(c, Bs4Tag):
                child_tag = cls.from_existing_bs4tag(c)
                new_tag.append(child_tag)
            elif isinstance(c, Comment):
                new_tag.append(Comment(c))
            else:
                new_tag.append(NavigableString(str(c)))

        return new_tag

    def __init__(
        self,
        parser: BeautifulSoup | None = None,
        builder: TreeBuilder | None = None,
        name: str | None = None,
        namespace: str | None = None,
        prefix: str | None = None,
        attrs: dict[str, str] | None = None,
        parent: Tag | None = None,
        previous: PageElement | None = None,
        is_xml: bool | None = None,
        sourceline: int | None = None,
        sourcepos: int | None = None,
        can_be_empty_element: bool | None = None,
        cdata_list_attributes: list[str] | None = None,
        preserve_whitespace_tags: list[str] | None = None,
        interesting_string_types: type[NavigableString] | tuple[type[NavigableString], ...] | None = None,
        namespaces: dict[str, str] | None = None,
    ):
        """Basic constructor.

        :param parser: A BeautifulSoup object.
        :param builder: A TreeBuilder.
        :param name: The name of the tag.
        :param namespace: The URI of this Tag's XML namespace, if any.
        :param prefix: The prefix for this Tag's XML namespace, if any.
        :param attrs: A dictionary of this Tag's attribute values.
        :param parent: The PageElement to use as this Tag's parent.
        :param previous: The PageElement that was parsed immediately before
            this tag.
        :param is_xml: If True, this is an XML tag. Otherwise, this is an
            HTML tag.
        :param sourceline: The line number where this tag was found in its
            source document.
        :param sourcepos: The character position within `sourceline` where this
            tag was found.
        :param can_be_empty_element: If True, this tag should be
            represented as <tag/>. If False, this tag should be represented
            as <tag></tag>.
        :param cdata_list_attributes: A list of attributes whose values should
            be treated as CDATA if they ever show up on this tag.
        :param preserve_whitespace_tags: A list of tag names whose contents
            should have their whitespace preserved.
        :param interesting_string_types: This is a NavigableString
            subclass or a tuple of them. When iterating over this
            Tag's strings in methods like Tag.strings or Tag.get_text,
            these are the types of strings that are interesting enough
            to be considered. The default is to consider
            NavigableString and CData the only interesting string
            subtypes.
        :param namespaces: A dictionary mapping currently active
            namespace prefixes to URIs. This can be used later to
            construct CSS selectors.
        """
        super().__init__(
            parser=parser,
            builder=builder,
            name=name,
            namespace=namespace,
            prefix=prefix,
            attrs=attrs,
            parent=parent,
            previous=previous,
            is_xml=is_xml,
            sourceline=sourceline,
            sourcepos=sourcepos,
            can_be_empty_element=can_be_empty_element,
            cdata_list_attributes=cdata_list_attributes,
            preserve_whitespace_tags=preserve_whitespace_tags,
            interesting_string_types=interesting_string_types,
            namespaces=namespaces,
        )
        self._token: Token[Tag | None] | None = None

    def __enter__(self):
        self._token = current_parent.set(self)
        return self

    def __exit__(self, *args: Any) -> None:
        current_parent.reset(self._token)  # pyright: ignore[reportArgumentType]

    @overload  # pragma: no cover # NOTE: We have tests that cover this case
    def __getitem__(self, key: Literal["class"]) -> list[str]:
        """Get attribute value, ensuring class returns as list."""
        ...

    @overload  # pragma: no cover # NOTE: We have tests that cover this case
    def __getitem__(self, key: str) -> str | list[str]:
        """Get attribute value for non-class attributes."""
        ...

    def __getitem__(self, key: str) -> str | list[str]:
        if key not in self.attrs and key == "class":
            self.attrs["class"] = []
            return self.attrs["class"]

        if key == "class":
            current_value = self.attrs.get("class", [])
            if isinstance(current_value, str):
                self.attrs["class"] = current_value.split()
            elif not isinstance(current_value, list):
                self.attrs["class"] = []
            return self.attrs["class"]

        value = self.attrs[key]

        return json.dumps(value) if isinstance(value, dict | list) else value

    def comment(self, selector: str) -> list[Tag | NavigableString | None]:
        """Find all tags or text nodes that follow comments matching the given selector.

        This method searches for HTML comments containing the selector text and returns
        the elements that immediately follow those comments. It can return both HTML
        elements and text nodes.

        Args:
            selector: The comment text to search for (e.g., "#button" or ".card")

        Returns:
            A list of Tag or NavigableString objects that immediately follow matching comments.
            For text nodes, returns them as `NavigableString`.
            Returns an empty list if no matches are found.
        """
        results: list[Tag | NavigableString | None] = []

        # Find all comment nodes matching the selector
        comments = self.find_all(string=lambda text: isinstance(text, str) and selector in text.strip())

        for comment in comments:
            # Get the next sibling of the comment
            next_node = comment.next_sibling

            # Skip empty text nodes
            while next_node and isinstance(next_node, NavigableString) and not next_node.strip():
                next_node = next_node.next_sibling

            if isinstance(next_node, Tag):
                # Convert to our Tag
                results.append(next_node)
            elif isinstance(next_node, NavigableString) and (text := next_node.strip()):
                # Return the NavigableString as-is
                results.append(NavigableString(text))

        return results

    def comment_one(self, selector: str) -> Tag | NavigableString | None:
        """Find the first tag or text node that follows a comment matching the given selector.

        This method searches for the first HTML comment containing the selector text and returns
        the element that immediately follows it. It can return both HTML elements and text nodes.
        Returns None if no match is found.

        Args:
            selector: The comment text to search for (e.g., "#button" or ".card")

        Returns:
            A Tag object if the next element is an HTML tag, or a NavigableString if it's a text node.
            Returns None if no match is found.
        """
        # Find all comment nodes matching the selector
        comments = self.find_all(string=lambda text: isinstance(text, str) and selector in text.strip())

        for comment in comments:
            # Get the next sibling of the comment
            next_node = comment.next_sibling
            while next_node:
                if isinstance(next_node, Tag):
                    return next_node

                if isinstance(next_node, NavigableString) and (text := next_node.strip()):
                    # Return NavigableString directly for consistency
                    return NavigableString(text)

                next_node = next_node.next_sibling

        return None

    def copy(self) -> Tag:
        """Create a copy of this tag.

        Returns:
            A new Tag instance that is a copy of this tag
        """
        return Tag.from_existing_bs4tag(self)
