from _typeshed import Incomplete, ReadableBuffer  # noqa: I001
from collections.abc import Callable, Iterable, Iterator
from contextvars import ContextVar
from re import Pattern
from typing import Any, Literal, TypeVar, overload
from typing import Self, TypeAlias

from bs4 import BeautifulSoup
from bs4.builder import TreeBuilder
from bs4.formatter import Formatter, _EntitySubstitution  # pyright: ignore[reportPrivateUsage]
from bs4 import Tag as Bs4Tag

DEFAULT_OUTPUT_ENCODING: str
nonwhitespace_re: Pattern[str]
whitespace_re: Pattern[str]
PYTHON_SPECIFIC_ENCODINGS: set[str]

# Context variable that tracks the current parent Tag during component rendering.
# This allows nested components to access their parent Tag context.
# Default is None when outside of a component render context.
current_tag_context: ContextVar[Tag | None]

class NamespacedAttribute(str):
    def __new__(cls, prefix: str, name: str | None = None, namespace: str | None = None) -> Self: ...

class AttributeValueWithCharsetSubstitution(str): ...

class CharsetMetaAttributeValue(AttributeValueWithCharsetSubstitution):
    def __new__(cls, original_value): ...  # pyright: ignore[reportUnknownParameterType, reportMissingParameterType]
    def encode(self, encoding: str) -> str: ...  # type: ignore[override]  # incompatible with str

class ContentMetaAttributeValue(AttributeValueWithCharsetSubstitution):
    CHARSET_RE: Pattern[str]
    def __new__(cls, original_value): ...  # pyright: ignore[reportUnknownParameterType, reportMissingParameterType]
    def encode(self, encoding: str) -> str: ...  # type: ignore[override]  # incompatible with str

_T = TypeVar("_T")
_PageElementT = TypeVar("_PageElementT", bound=PageElement)
_SimpleStrainable: TypeAlias = str | bool | None | bytes | Pattern[str] | Callable[[str], bool] | Callable[[Tag], bool]
_Strainable: TypeAlias = _SimpleStrainable | Iterable[_SimpleStrainable]
_SimpleNormalizedStrainable: TypeAlias = (
    str | bool | None | Pattern[str] | Callable[[str], bool] | Callable[[Tag], bool]
)
_NormalizedStrainable: TypeAlias = _SimpleNormalizedStrainable | Iterable[_SimpleNormalizedStrainable]

class PageElement:
    parent: Tag | None
    previous_element: PageElement | None
    next_element: PageElement | None
    next_sibling: PageElement | None
    previous_sibling: PageElement | None
    def setup(
        self,
        parent: Tag | None = None,
        previous_element: PageElement | None = None,
        next_element: PageElement | None = None,
        previous_sibling: PageElement | None = None,
        next_sibling: PageElement | None = None,
    ) -> None: ...
    def format_string(self, s: str, formatter: Formatter | str | None) -> str: ...
    def formatter_for_name(self, formatter: Formatter | str | _EntitySubstitution): ...  # pyright: ignore[reportUnknownParameterType]
    nextSibling: PageElement | None  # noqa: N815
    previousSibling: PageElement | None  # noqa: N815
    @property
    def stripped_strings(self) -> Iterator[str]: ...
    def get_text(
        self, separator: str = "", strip: bool = False, types: tuple[type[NavigableString], ...] = ...
    ) -> str: ...
    getText = get_text  # noqa: N815
    @property
    def text(self) -> str: ...
    def replace_with(self, *args: PageElement | str) -> Self: ...
    replaceWith = replace_with  # noqa: N815
    def unwrap(self) -> Self: ...
    replace_with_children = unwrap
    replaceWithChildren = unwrap  # noqa: N815
    def wrap(self, wrap_inside: _PageElementT) -> _PageElementT: ...
    def extract(self, _self_index: int | None = None) -> Self: ...
    def insert(self, position: int, new_child: PageElement | str) -> None: ...
    def append(self, tag: PageElement | str) -> None: ...
    def extend(self, tags: Iterable[PageElement | str]) -> None: ...
    def insert_before(self, *args: PageElement | str) -> None: ...
    def insert_after(self, *args: PageElement | str) -> None: ...
    def find_next(
        self,
        name: _Strainable | SoupStrainer | None = None,
        attrs: dict[str, _Strainable] | _Strainable = {},
        string: _Strainable | None = None,
        **kwargs: _Strainable,
    ) -> Tag | NavigableString | None: ...
    findNext = find_next  # noqa: N815
    def find_all_next(
        self,
        name: _Strainable | SoupStrainer | None = None,
        attrs: dict[str, _Strainable] | _Strainable = {},
        string: _Strainable | None = None,
        limit: int | None = None,
        **kwargs: _Strainable,
    ) -> ResultSet[PageElement]: ...
    findAllNext = find_all_next  # noqa: N815
    def find_next_sibling(
        self,
        name: _Strainable | SoupStrainer | None = None,
        attrs: dict[str, _Strainable] | _Strainable = {},
        string: _Strainable | None = None,
        **kwargs: _Strainable,
    ) -> Tag | NavigableString | None: ...
    findNextSibling = find_next_sibling  # noqa: N815
    def find_next_siblings(
        self,
        name: _Strainable | SoupStrainer | None = None,
        attrs: dict[str, _Strainable] | _Strainable = {},
        string: _Strainable | None = None,
        limit: int | None = None,
        **kwargs: _Strainable,
    ) -> ResultSet[PageElement]: ...
    findNextSiblings = find_next_siblings  # noqa: N815
    fetchNextSiblings = find_next_siblings  # noqa: N815
    def find_previous(
        self,
        name: _Strainable | SoupStrainer | None = None,
        attrs: dict[str, _Strainable] | _Strainable = {},
        string: _Strainable | None = None,
        **kwargs: _Strainable,
    ) -> Tag | NavigableString | None: ...
    findPrevious = find_previous  # noqa: N815
    def find_all_previous(
        self,
        name: _Strainable | SoupStrainer | None = None,
        attrs: dict[str, _Strainable] | _Strainable = {},
        string: _Strainable | None = None,
        limit: int | None = None,
        **kwargs: _Strainable,
    ) -> ResultSet[PageElement]: ...
    findAllPrevious = find_all_previous  # noqa: N815
    fetchPrevious = find_all_previous  # noqa: N815
    def find_previous_sibling(
        self,
        name: _Strainable | SoupStrainer | None = None,
        attrs: dict[str, _Strainable] | _Strainable = {},
        string: _Strainable | None = None,
        **kwargs: _Strainable,
    ) -> Tag | NavigableString | None: ...
    findPreviousSibling = find_previous_sibling  # noqa: N815
    def find_previous_siblings(
        self,
        name: _Strainable | SoupStrainer | None = None,
        attrs: dict[str, _Strainable] | _Strainable = {},
        string: _Strainable | None = None,
        limit: int | None = None,
        **kwargs: _Strainable,
    ) -> ResultSet[PageElement]: ...
    findPreviousSiblings = find_previous_siblings  # noqa: N815
    fetchPreviousSiblings = find_previous_siblings  # noqa: N815
    def find_parent(
        self,
        name: _Strainable | SoupStrainer | None = None,
        attrs: dict[str, _Strainable] | _Strainable = {},
        **kwargs: _Strainable,
    ) -> Tag | None: ...
    findParent = find_parent  # noqa: N815
    def find_parents(
        self,
        name: _Strainable | SoupStrainer | None = None,
        attrs: dict[str, _Strainable] | _Strainable = {},
        limit: int | None = None,
        **kwargs: _Strainable,
    ) -> ResultSet[Tag]: ...
    findParents = find_parents  # noqa: N815
    fetchParents = find_parents  # noqa: N815
    @property
    def next(self) -> Tag | NavigableString | None: ...
    @property
    def previous(self) -> Tag | NavigableString | None: ...
    @property
    def next_elements(self) -> Iterable[PageElement]: ...
    @property
    def next_siblings(self) -> Iterable[PageElement]: ...
    @property
    def previous_elements(self) -> Iterable[PageElement]: ...
    @property
    def previous_siblings(self) -> Iterable[PageElement]: ...
    @property
    def parents(self) -> Iterable[Tag]: ...
    @property
    def decomposed(self) -> bool: ...
    def nextGenerator(self) -> Iterable[PageElement]: ...  # noqa: N802
    def nextSiblingGenerator(self) -> Iterable[PageElement]: ...  # noqa: N802
    def previousGenerator(self) -> Iterable[PageElement]: ...  # noqa: N802
    def previousSiblingGenerator(self) -> Iterable[PageElement]: ...  # noqa: N802
    def parentGenerator(self) -> Iterable[Tag]: ...  # noqa: N802

class NavigableString(str, PageElement):
    PREFIX: str
    SUFFIX: str
    known_xml: bool | None
    def __new__(cls, value: str | ReadableBuffer) -> Self: ...
    def __copy__(self) -> Self: ...
    def __getnewargs__(self) -> tuple[str]: ...
    def output_ready(self, formatter: Formatter | str | None = "minimal") -> str: ...
    @property
    def name(self) -> None: ...
    @property
    def strings(self) -> Iterable[str]: ...

class PreformattedString(NavigableString):
    PREFIX: str
    SUFFIX: str
    def output_ready(self, formatter: Formatter | str | None = None) -> str: ...

class CData(PreformattedString):
    PREFIX: str
    SUFFIX: str

class ProcessingInstruction(PreformattedString):
    PREFIX: str
    SUFFIX: str

class XMLProcessingInstruction(ProcessingInstruction):
    PREFIX: str
    SUFFIX: str

class Comment(PreformattedString):
    PREFIX: str
    SUFFIX: str

class Declaration(PreformattedString):
    PREFIX: str
    SUFFIX: str

class Doctype(PreformattedString):
    @classmethod
    def for_name_and_ids(cls, name: str | None, pub_id: str, system_id: str) -> Doctype: ...
    PREFIX: str
    SUFFIX: str

class Stylesheet(NavigableString): ...
class Script(NavigableString): ...
class TemplateString(NavigableString): ...

class Tag(PageElement):
    parser_class: type[BeautifulSoup] | None
    name: str
    namespace: str | None
    prefix: str | None
    sourceline: int | None
    sourcepos: int | None
    known_xml: bool | None
    attrs: dict[str, str | Any]
    contents: list[PageElement]
    hidden: bool
    can_be_empty_element: bool | None
    cdata_list_attributes: list[str] | None
    preserve_whitespace_tags: list[str] | None
    @classmethod
    def from_existing_bs4tag(cls, bs4_tag: Bs4Tag) -> Tag: ...
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
    ) -> None: ...
    parserClass: type[BeautifulSoup] | None  # noqa: N815
    def __copy__(self) -> Self: ...
    @property
    def is_empty_element(self) -> bool: ...
    @property
    def isSelfClosing(self) -> bool: ...  # noqa: N802
    @property
    def string(self) -> str | None: ...
    @string.setter
    def string(self, string: str) -> None: ...
    DEFAULT_INTERESTING_STRING_TYPES: tuple[type[NavigableString], ...]
    @property
    def strings(self) -> Iterable[str]: ...
    def decompose(self) -> None: ...
    def clear(self, decompose: bool = False) -> None: ...
    def smooth(self) -> None: ...
    def index(self, element: PageElement) -> int: ...
    @overload
    def get(self, key: str, default: None = None) -> str | list[str] | None: ...
    @overload
    def get(self, key: str, default: _T) -> str | list[str] | _T: ...
    @overload
    def get_attribute_list(self, key: str, default: None = None) -> list[str | None]: ...
    @overload
    def get_attribute_list(self, key: str, default: list[_T]) -> list[str | _T]: ...
    @overload
    def get_attribute_list(self, key: str, default: _T) -> list[str | _T]: ...
    def has_attr(self, key: str) -> bool: ...
    def __hash__(self) -> int: ...
    @overload
    def __getitem__(self, key: Literal["class"]) -> list[str]: ...
    @overload
    def __getitem__(self, key: str) -> str | list[str]: ...
    def __iter__(self) -> Iterator[PageElement]: ...
    def __len__(self) -> int: ...
    def __contains__(self, x: object) -> bool: ...
    def __bool__(self) -> bool: ...
    def __setitem__(self, key: str, value: str | list[str]) -> None: ...
    def __delitem__(self, key: str) -> None: ...
    def __getattr__(self, tag: str) -> Tag | None: ...
    def __eq__(self, other: object) -> bool: ...
    def __ne__(self, other: object) -> bool: ...
    def __unicode__(self) -> str: ...
    def encode(
        self,
        encoding: str = "utf-8",
        indent_level: int | None = None,
        formatter: Literal["html", "html5", "minimal"] | Formatter | None = "minimal",
        errors: str = "xmlcharrefreplace",
    ) -> bytes: ...
    def decode(
        self,
        indent_level: int | None = None,
        eventual_encoding: str = "utf-8",
        formatter: Literal["html", "html5", "minimal"] | Formatter | None = "minimal",
        iterator: Iterator[PageElement] | None = None,
    ) -> str: ...
    @overload
    def prettify(
        self, encoding: str, formatter: Literal["html", "html5", "minimal"] | Formatter | None = "minimal"
    ) -> bytes: ...
    @overload
    def prettify(
        self, encoding: None = None, formatter: Literal["html", "html5", "minimal"] | Formatter | None = "minimal"
    ) -> str: ...
    def decode_contents(
        self,
        indent_level: int | None = None,
        eventual_encoding: str = "utf-8",
        formatter: Literal["html", "html5", "minimal"] | Formatter | None = "minimal",
    ) -> str: ...
    def copy(self) -> Self: ...
    def __enter__(self) -> Self: ...
    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None: ...
    def comment(self, text: str) -> Comment: ...
    def comment_one(self, selector: str) -> Tag | None: ...
    # def comment_one(self, selector: str) -> Tag | NavigableString | None: ...
    def encode_contents(
        self,
        indent_level: int | None = None,
        encoding: str = "utf-8",
        formatter: Literal["html", "html5", "minimal"] | Formatter | None = "minimal",
    ) -> bytes: ...
    def renderContents(self, encoding: str = "utf-8", prettyPrint: bool = False, indentLevel: int = 0) -> bytes: ...  # noqa: N802, N803
    def find(
        self,
        name: _Strainable | None = None,
        attrs: dict[str, _Strainable] | _Strainable = {},
        recursive: bool = True,
        string: _Strainable | None = None,
        **kwargs: _Strainable,
    ) -> Tag | NavigableString | None: ...
    findChild = find  # noqa: N815
    def find_all(
        self,
        name: _Strainable | None = None,
        attrs: dict[str, _Strainable] | _Strainable = {},
        recursive: bool = True,
        string: _Strainable | None = None,
        limit: int | None = None,
        **kwargs: _Strainable,
    ) -> ResultSet[Any]: ...
    __call__ = find_all
    findAll = find_all  # noqa: N815
    findChildren = find_all  # noqa: N815
    @property
    def children(self) -> Iterable[PageElement]: ...
    @property
    def descendants(self) -> Iterable[PageElement]: ...
    def select_one(
        self,
        selector: str,
        namespaces: Incomplete | None = None,
        *,
        flags: int = ...,
        custom: dict[str, str] | None = ...,
    ) -> Tag | None: ...
    def select(
        self,
        selector: str,
        namespaces: Incomplete | None = None,
        limit: int | None = None,
        *,
        flags: int = ...,
        custom: dict[str, str] | None = ...,
    ) -> ResultSet[Tag]: ...
    def childGenerator(self) -> Iterable[PageElement]: ...  # noqa: N802
    def recursiveChildGenerator(self) -> Iterable[PageElement]: ...  # noqa: N802
    def has_key(self, key: str) -> bool: ...

class SoupStrainer:
    name: _NormalizedStrainable
    attrs: dict[str, _NormalizedStrainable]
    string: _NormalizedStrainable
    def __init__(
        self,
        name: _Strainable | None = None,
        attrs: dict[str, _Strainable] | _Strainable = {},
        string: _Strainable | None = None,
        **kwargs: _Strainable,
    ) -> None: ...
    def search_tag(self, markup_name: Tag | str | None = None, markup_attrs={}): ...  # pyright: ignore[reportUnknownParameterType, reportMissingParameterType]
    searchTag = search_tag  # noqa: N815 # pyright: ignore[reportUnknownVariableType]
    def search(self, markup: PageElement | Iterable[PageElement]): ...  # pyright: ignore[reportUnknownVariableType, reportUnknownParameterType]

class ResultSet(list[_PageElementT]):
    source: SoupStrainer
    @overload
    def __init__(self, source: SoupStrainer) -> None: ...
    @overload
    def __init__(self, source: SoupStrainer, result: Iterable[_PageElementT]) -> None: ...
