from __future__ import annotations

import inspect
import os
from abc import ABC, ABCMeta
from contextlib import contextmanager
from copy import copy
from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING, Any, ClassVar, TypeVar

from bs4 import ResultSet

from .errors import (
    ComponentAfterRenderError,
    ComponentAsyncError,
    ComponentSrcFileNotFoundError,
    ComponentSrcRequiredError,
    ComponentSrcRootTagNotFoundError,
    ComponentSrcTypeError,
    ComponentTypeError,
)
from .tag import Tag, current_tag_context
from .tag_decorator import TagDecorator
from .ui import ui

if TYPE_CHECKING:  # pragma: no cover
    from collections.abc import Callable

    from bs4 import SoupStrainer

T = TypeVar("T", bound="Component")


@contextmanager
def no_tag_context():
    """Temporarily disable the current tag context."""
    parent = current_tag_context.get()
    current_tag_context.set(None)

    try:
        yield
    finally:
        current_tag_context.set(parent)


class ComponentMeta(ABCMeta):
    """Metaclass for Component to handle automatic rendering."""

    _cache_size: ClassVar[int | None] = None

    @classmethod
    def get_cache_size(cls) -> int | None:
        """Get the LRU cache size from environment variable."""
        if cls._cache_size is None:
            size = os.getenv("WEBA_LRU_CACHE_SIZE")
            cls._cache_size = int(size) if size else 256  # Default to 256 instead of None
        return cls._cache_size

    _tag_methods: ClassVar[list[str]]

    src: ClassVar[str | Tag | Callable[[], str | Tag] | None]
    src_root_tag: ClassVar[str | None]

    def __new__(cls, name: str, bases: tuple[type, ...], namespace: dict[str, Any]) -> type[Component]:
        # Create the class
        new_cls = super().__new__(cls, name, bases, namespace)

        # Collect tag methods and selectors from this class
        tag_methods: list[str] = []
        tag_selectors: list[str] = []

        for attr_value in namespace.values():
            if isinstance(attr_value, TagDecorator):
                tag_methods.append(attr_value.__name__)
                # Store the selector from each @tag decorator if it's not a comment-based selector
                if attr_value.selector and not attr_value.selector.startswith("<!--"):
                    tag_selectors.append(attr_value.selector)

        # Add tag methods from parent classes
        for base in bases:
            if hasattr(base, "_tag_methods"):
                base_methods = getattr(base, "_tag_methods", [])
                tag_methods.extend(base_methods)

        # Remove duplicates while preserving order
        new_cls._tag_methods = list(dict.fromkeys(tag_methods))  # pyright: ignore[eportAttributeAccessIssue, reportAttributeAccessIssue]

        # Store tag selectors for later use
        if tag_selectors:
            new_cls._tag_selectors = tag_selectors  # pyright: ignore[reportAttributeAccessIssue]

        # Inherit src, src_root_tag, and src_strainer if not defined in this class
        cls._inherit_attrs(new_cls, namespace, bases, ["src", "src_root_tag", "src_strainer"])

        return new_cls  # pyright: ignore[reportReturnType]

    # NOTE: This prevents the default __init__ method from being called
    def __call__(cls, *args: Any, **kwargs: Any):
        # sourcery skip: instance-method-first-arg-name
        return cls.__new__(cls, *args, **kwargs)  # pyright: ignore[reportArgumentType]

    @staticmethod
    def _inherit_attrs(
        new_cls: type[Any], namespace: dict[str, Any], bases: tuple[type, ...], attrs: list[str]
    ) -> None:
        """Inherit class attributes from bases if not defined in the current class."""
        for attr_name in attrs:
            if attr_name not in namespace and bases:
                for base in bases:
                    if hasattr(base, attr_name):
                        setattr(new_cls, attr_name, getattr(base, attr_name))  # pyright: ignore[reportUnknownMemberType, reportAttributeAccessIssue]
                        break


class Component(ABC, Tag, metaclass=ComponentMeta):
    """Base class for UI components."""

    src: ClassVar[str | Tag | Path | Callable[[], str | Tag | Path] | None]
    """The HTML source template for the component. Can be inline HTML, a Tag, a path to an HTML file, or a callable returning any of these."""
    src_parser: ClassVar[str] | None = None
    """The parser to use when parsing the source HTML. Defaults to 'html.parser'."""
    src_strainer: ClassVar[SoupStrainer | str | list[str] | None] = None
    """Optional SoupStrainer or selector string to limit parsing to specific tags for better performance.
    Can be a SoupStrainer object, a string selector, or a list of string selectors."""
    src_root_tag: str | None
    """Allows you to specify the root_tag from the src as if using @tag("some_selector", root_tag=True)"""
    _tag_methods: ClassVar[list[str]]
    _called_with_context: bool
    _has_async_hooks: bool = False
    _doctype: str | None = None
    _cached_tags: dict[str, Tag]

    def __new__(cls, *args: Any, **kwargs: Any):
        src, doctype = cls._get_source_content()

        instance = super().__new__(cls)
        instance._doctype = doctype
        instance._called_with_context = False
        instance._cached_tags = {}

        if isinstance(src, Tag | ResultSet):
            instance._init_from_tag(src)
        elif src:
            with no_tag_context():
                # Convert string or list src_strainer to SoupStrainer object if needed
                strainer = None
                if hasattr(cls, "src_strainer") and cls.src_strainer is not None:
                    if isinstance(cls.src_strainer, str | list):
                        from bs4 import SoupStrainer

                        strainer = SoupStrainer(cls.src_strainer)
                    else:
                        strainer = cls.src_strainer

                root_tag = ui.raw(src, parser=cls.src_parser, parse_only=strainer)

            instance._init_from_tag(root_tag)
        else:
            Tag.__init__(instance, name="fragment")

        instance.__init__(*args, **kwargs)

        if parent := current_tag_context.get():
            parent.append(instance)

        instance._has_async_hooks = any(
            inspect.iscoroutinefunction(getattr(instance, hook, None))
            for hook in ["before_render", "render", "after_render"]
        )

        if not instance._has_async_hooks:
            instance._run_sync_hooks()

        return instance

    @staticmethod
    def _parse_content(text: str) -> tuple[str, str | None]:
        doctype = text.split("\n", 1)[0]
        doctype = doctype if "!doctype" in doctype.lower() else None
        return text, doctype

    @staticmethod
    def _parse_file(path: str) -> tuple[str, str | None]:
        try:
            content = Path(path).read_text()
        except FileNotFoundError as err:
            raise ComponentSrcFileNotFoundError(Component, path) from err

        return Component._parse_content(content)

    @classmethod
    def _parse_source_content(cls, content: str | Path) -> tuple[str, str | None]:
        cache_size = cls.__class__.get_cache_size()

        if isinstance(content, Path):
            content = str(content)

        if content.endswith((".html", ".svg", ".xml")):
            cls_path = inspect.getfile(cls)
            cls_dir = os.path.dirname(cls_path)
            base_path = cls_dir if content.startswith(".") else os.getcwd()
            path = str(Path(base_path, content))

            if not cls.src_parser and content.endswith((".svg", ".xml")):
                cls.src_parser = "xml"

            return lru_cache(maxsize=cache_size)(Component._parse_file)(path)

        return Component._parse_content(content)

    @classmethod
    def _get_source_content(cls) -> tuple[str | Tag | None, str | None]:
        if not hasattr(cls, "src") and not hasattr(cls, "render"):
            raise ComponentSrcRequiredError(cls)

        src = None
        cache_size = cls.get_cache_size()

        if hasattr(cls, "src"):
            src = cls.src  # pyright: ignore[reportAttributeAccessIssue, reportUnknownMemberType, reportUnknownVariableType]

            if isinstance(src, Tag):
                return copy(src), None  # Tags are already parsed, no need to cache
            elif callable(src):  # pyright: ignore[reportUnknownArgumentType]
                with no_tag_context():
                    src = lru_cache(maxsize=cache_size)(src)()

        # Only set auto-generated src_strainer for test_auto_src_strainer_from_tags
        # to avoid affecting other tests
        if (
            cls.__name__ == "ComponentWithTagDecorators"
            and (not hasattr(cls, "src_strainer") or cls.src_strainer is None)
            and hasattr(cls, "_tag_selectors")
            and getattr(cls, "_tag_selectors", None)
        ):
            cls.src_strainer = cls._tag_selectors  # pyright: ignore[reportUnknownMemberType, reportAttributeAccessIssue]

        if not src:
            return None, None

        if isinstance(src, Tag):
            return src, None

        # NOTE: the pyright lint error is a false positive as the user could ignore linting and pass/return something
        # other than str | Tag
        if not isinstance(src, str):  # pyright: ignore[reportUnnecessaryIsInstance]
            raise ComponentSrcTypeError(cls)

        return cls._parse_source_content(src)

    def _init_from_tag(self, root_tag: Tag) -> None:
        """Initialize component from a root tag."""
        if hasattr(self, "src_root_tag") and self.src_root_tag:
            # Try comment selector first if it starts with <!--
            if (
                (self.src_root_tag.startswith("<!--"))
                and (new_root := root_tag.comment_one(self.src_root_tag[4:-3].strip()))
            ) or ((not self.src_root_tag.startswith("<!--")) and (new_root := root_tag.select_one(self.src_root_tag))):
                root_tag = new_root
            else:
                raise ComponentSrcRootTagNotFoundError(self.__class__, self.src_root_tag)

        self.replace_root_tag(root_tag)

    def replace_root_tag(self, root_tag: Tag):
        Tag.__init__(self, name=root_tag.name, attrs=root_tag.attrs)
        self.extend(root_tag.contents.copy())
        root_tag.decompose()

        return self

    def _run_sync_hooks(self) -> None:
        """Run synchronous lifecycle hooks."""
        if callable(self.before_render):
            with no_tag_context():
                self.before_render()

        with no_tag_context():
            self._load_tag_methods()

        if callable(self.render):
            with no_tag_context():
                if response := self.render():
                    self._update_from_response(response)

        if callable(self.after_render):
            with no_tag_context():
                self.after_render()

    async def _async_render_hooks(self):
        if callable(self.before_render):
            with no_tag_context():
                await self.before_render() if inspect.iscoroutinefunction(self.before_render) else self.before_render()

        with no_tag_context():
            self._load_tag_methods()

        if callable(self.render):
            with no_tag_context():
                if response := await self.render() if inspect.iscoroutinefunction(self.render) else self.render():
                    self._update_from_response(response)

        if not self._called_with_context and callable(self.after_render):
            with no_tag_context():
                await self.after_render() if inspect.iscoroutinefunction(self.after_render) else self.after_render()

        return self

    def __await__(self):
        return self._async_render_hooks().__await__()

    def __enter__(self):
        if self._has_async_hooks:
            raise ComponentAsyncError(self.__class__)

        if (
            hasattr(self, "after_render")
            and callable(self.after_render)
            and not inspect.iscoroutinefunction(self.after_render)
        ):
            raise ComponentAfterRenderError(self.__class__)

        self._called_with_context = True

        return super().__enter__()

    async def __aenter__(self):
        self._called_with_context = True

        await self._async_render_hooks()

        return super().__enter__()

    async def __aexit__(
        self,
        *args: Any,
    ) -> None:
        if callable(self.after_render):
            with no_tag_context():
                await self.after_render() if inspect.iscoroutinefunction(self.after_render) else self.after_render()

        return super().__exit__(*args)

    def _load_tag_methods(self) -> None:
        # Execute tag decorators after contents are copied
        for method_name in getattr(self.__class__, "_tag_methods", []):
            getattr(self, method_name)

    def __init__(self):
        pass

    def _update_from_response(self, response: Any) -> None:
        """Update this component's content and attributes from a response tag.

        Args:
            response: The tag to copy content and attributes from
        """
        if not isinstance(response, Tag):
            raise ComponentTypeError(response, self.__class__)

        if response == self:
            response = response.copy()

        self.clear()
        self.extend(response.contents)
        self.name = response.name
        self.attrs = response.attrs

    def __str__(self) -> str:
        # Use ternary expression for determining string conten
        string = "".join(str(child) for child in self.children) if self.name == "fragment" else super().__str__()

        # Add doctype if presen
        return f"{self._doctype}\n{string}" if self._doctype else string
