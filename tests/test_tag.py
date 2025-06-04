# pyright: reportUnknownArgumentType=false, reportCallIssue=false
from __future__ import annotations

from weba import ui


# pyright: reportUnknownVariableType=false, reportGeneralTypeIssues=false, reportOptionalCall=false, reportUnknownMemberType=false, reportAttributeAccessIssue=false
def test_tag_call_syntax():
    """Test that Tag instances can be called directly to use with_attrs under the hood."""
    # Create a tag and use call-style syntax via with_attrs
    tag = ui.div().with_attrs(_class="container")

    with tag as container:
        ui.p("Test content")

    assert "container" in str(container)
    assert "<p>Test content</p>" in str(container)


# pyright: reportUnknownVariableType=false, reportGeneralTypeIssues=false, reportOptionalCall=false, reportUnknownMemberType=false, reportAttributeAccessIssue=false
def test_tag_with_attrs_method():
    """Test that the with_attrs method works as expected."""
    # Create a tag and use the with_attrs method
    with ui.header().with_attrs(_class="site-header", id="main-header") as header:
        ui.h1("Page Title")

    assert "site-header" in str(header)
    assert "main-header" in str(header)
    assert "<h1>Page Title</h1>" in str(header)


# pyright: reportUnknownVariableType=false, reportGeneralTypeIssues=false, reportOptionalCall=false, reportUnknownMemberType=false, reportAttributeAccessIssue=false
def test_tag_methods_chaining():
    """Test with_attrs method chaining."""
    # Chaining with_attrs calls
    tag1 = ui.section().with_attrs(_class="section1").with_attrs(id="section1")

    assert "section1" in str(tag1)
    assert 'id="section1"' in str(tag1)


# pyright: reportUnknownVariableType=false, reportGeneralTypeIssues=false, reportOptionalCall=false, reportUnknownMemberType=false, reportAttributeAccessIssue=false
def test_tag_append_class():
    """Test appending and prepending classes."""
    # Start with a tag with a class
    tag = ui.div().with_attrs(_class="container")

    # Append a class
    tag.with_attrs(_append_class="mt-4")
    assert "container mt-4" in str(tag)

    # Append multiple classes
    tag.with_attrs(_append_class="px-4 text-center")
    assert "container mt-4 px-4 text-center" in str(tag)

    # Prepend a class
    tag.with_attrs(_prepend_class="flex")
    assert "flex container mt-4 px-4 text-center" in str(tag)

    # Prepend multiple classes
    tag.with_attrs(_prepend_class="grid gap-4")
    assert "grid gap-4 flex container mt-4 px-4 text-center" in str(tag)


# pyright: reportUnknownVariableType=false, reportGeneralTypeIssues=false, reportOptionalCall=false, reportUnknownMemberType=false, reportAttributeAccessIssue=false
def test_tag_append_class_with_call_syntax():
    """Test appending and prepending classes with call syntax."""
    # Create a tag with attrs method
    tag = ui.div().with_attrs(_class="container")

    # Append a class with call syntax
    tag(_append_class="mt-4")
    assert "container mt-4" in str(tag)

    # Mixed operations
    tag(_append_class="px-4", _prepend_class="flex", id="main")
    assert "flex container mt-4 px-4" in str(tag)
    assert 'id="main"' in str(tag)


def test_tag_with_class_manipulation():
    """Test using special class manipulation in a component-like context."""
    # Start with a base component
    with ui.div().with_attrs(_class="component"):
        # Add a header with base class and appended class
        with ui.header().with_attrs(_class="header", _append_class="sticky") as header:
            ui.h1("Title")

        # Add a content area with base class and prepended class
        with ui.main().with_attrs(_class="content", _prepend_class="flex") as main:
            ui.p("Content")

        # Add a footer with both prepended and appended classes
        with ui.footer().with_attrs(_class="footer", _prepend_class="grid", _append_class="mt-4") as footer:
            ui.p("Footer")

    # Verify classes were applied correctly
    assert "header sticky" in str(header)
    assert "flex content" in str(main)
    assert "grid footer mt-4" in str(footer)


def test_tag_with_input_name():
    name = 'orders["123456"][lender]'
    html = ui.input(name=name)

    assert name in str(html)

    name = 'orders["123456"][lender]'
    html = ui.input()
    html["name"] = name

    assert name in str(html)
