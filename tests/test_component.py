from weba import Component, Tag, tag, ui


def test_basic_component():
    class Button(Component):
        html = "<button>Example</button>"

        def __init__(self, msg: str):
            self.msg = msg

        def render(self):
            self.string = self.msg

    with ui.div() as container:
        Button("Click me")

    assert str(container) == "<div><button>Click me</button></div>"


def test_component_with_tag_decorator_passing_tag():
    class Button(Component):
        html = "<div><button class='btn'>Example</button></div>"

        def __init__(self, msg: str):
            self.msg = msg

        @tag("button")
        def button_tag(self, t: Tag):
            t.string = self.msg

    with ui.div() as container:
        Button("Submit")

    assert str(container) == '<div><div><button class="btn">Submit</button></div></div>'


def test_component_with_tag_decorator():
    class Button(Component):
        html = "<div><button class='btn'>Example</button></div>"

        def __init__(self, msg: str):
            self.msg = msg

        def render(self):
            self.button_tag.string = "Submit"

        @tag("button")
        def button_tag(self):
            pass

    with ui.div() as container:
        Button("Submit")

    assert str(container) == '<div><div><button class="btn">Submit</button></div></div>'


# def test_component_with_comment_selector():
#     class Button(Component):
#         html = """
#             <!-- #button -->
#             <button>Example</button>
#         """
#
#         def __init__(self, text: str):
#             self.text = text
#
#         @tag("<!-- #button -->")
#         def button_tag(self, t: Tag):
#             t.string = self.text
#
#     with ui.div() as container:
#         Button("Delete")
#
#     assert str(container) == "<div><!-- #button --><button>Delete</button></div>"
#
#
# def test_component_from_file(tmp_path):
#     class Button(Component):
#         html = "./button.html"
#
#         def __init__(self, text: str):
#             self.text = text
#
#         def render(self):
#             self.string = self.text
#
#     with ui.div() as container:
#         Button("Save")
#
#     assert str(container) == "<div><button>Save</button></div>"
#
#
# def test_missing_html_attribute():
#     class InvalidComponent(Component):
#         pass
#
#     with pytest.raises(ValueError, match="Component must define 'html' class variable"):
#         InvalidComponent()
#
#
# def test_missing_template_file():
#     class InvalidComponent(Component):
#         html = "nonexistent.html"
#
#     with pytest.raises(FileNotFoundError, match="Template file not found"):
#         InvalidComponent()
#
#
# def test_multiple_components_in_list():
#     class Button(Component):
#         html = "<button></button>"
#
#         def __init__(self, text: str):
#             self.text = text
#
#         def render(self):
#             self.string = self.text
#
#     with ui.ul() as button_list:
#         with ui.li():
#             Button("first")
#         with ui.li():
#             Button("second")
#             Button("third")
#
#     expected = "<ul><li><button>first</button></li><li><button>second</button><button>third</button></li></ul>"
#     assert str(button_list) == expected
