"""Performance benchmark tests for weba.

These tests verify performance characteristics of critical operations,
particularly the Tag.__str__() optimization that uses list building
instead of string concatenation.
"""

from __future__ import annotations

import time

import pytest

from weba import ui


class TestTagStringPerformance:
    """Benchmark tests for Tag string rendering performance."""

    def test_small_tag_performance(self):
        """Benchmark small tags (1-10 attributes).

        Expected: ~5% improvement from O(n) list building.
        This test ensures no performance regression.
        """
        iterations = 1000

        # Create a small tag with a few attributes
        def create_small_tag():
            tag = ui.div(
                id="test",
                class_="container",
                data_value="123",
                style="color: red;",
            )
            tag.append(ui.p("Hello"))
            tag.append(ui.p("World"))
            return tag

        # Warm up
        for _ in range(100):
            str(create_small_tag())

        # Benchmark
        start = time.perf_counter()
        for _ in range(iterations):
            str(create_small_tag())
        elapsed = time.perf_counter() - start

        # Should complete in reasonable time (< 300ms for 1000 iterations)
        # This is a regression test - we expect O(n) performance
        assert elapsed < 0.3, f"Small tag rendering too slow: {elapsed:.4f}s for {iterations} iterations"

        # Log performance for visibility
        per_iteration = (elapsed / iterations) * 1000
        print(f"\nSmall tag: {per_iteration:.4f}ms per iteration ({iterations} iterations in {elapsed:.4f}s)")

    def test_medium_tag_performance(self):
        """Benchmark medium tags (10-50 attributes).

        Expected: ~15% improvement from O(n) list building.
        """
        iterations = 1000

        # Create a medium-sized tag with many attributes and children
        def create_medium_tag():
            tag = ui.div(
                id="test",
                class_="container main-content active",
                data_user_id="12345",
                data_session="abcdef",
                data_timestamp="1234567890",
                style="color: red; background: blue; margin: 10px;",
                aria_label="Test container",
                aria_role="main",
                tabindex="0",
                data_custom="custom value",
            )
            # Add 20 child elements
            for i in range(20):
                tag.append(ui.p(f"Paragraph {i}", class_="text-content", data_index=str(i)))
            return tag

        # Warm up
        for _ in range(100):
            str(create_medium_tag())

        # Benchmark
        start = time.perf_counter()
        for _ in range(iterations):
            str(create_medium_tag())
        elapsed = time.perf_counter() - start

        # Should complete in reasonable time (< 2s for 1000 iterations)
        # This is a regression test - we expect O(n) performance
        assert elapsed < 2.0, f"Medium tag rendering too slow: {elapsed:.4f}s for {iterations} iterations"

        per_iteration = (elapsed / iterations) * 1000
        print(f"\nMedium tag: {per_iteration:.4f}ms per iteration ({iterations} iterations in {elapsed:.4f}s)")

    def test_large_tag_performance(self):
        """Benchmark large tags (50+ attributes/children).

        Expected: ~20-30% improvement from O(n) list building.
        This is where the optimization has the most impact.
        """
        iterations = 500  # Fewer iterations for large tags

        # Create a large tag with many attributes and deeply nested children
        def create_large_tag():
            tag = ui.div(
                id="test",
                class_="container main-content active responsive mobile desktop tablet",
                data_user_id="12345",
                data_session="abcdef",
                data_timestamp="1234567890",
                data_locale="en-US",
                data_theme="dark",
                data_version="1.0.0",
                style="color: red; background: blue; margin: 10px; padding: 20px; border: 1px solid black;",
                aria_label="Test container",
                aria_role="main",
                aria_expanded="true",
                aria_hidden="false",
                tabindex="0",
                title="Test title",
                data_custom1="value1",
                data_custom2="value2",
                data_custom3="value3",
                data_custom4="value4",
                data_custom5="value5",
            )

            # Add 50 child elements with nested structure
            for i in range(50):
                with ui.div(class_="item", data_index=str(i)) as item:
                    ui.h3(f"Item {i}", class_="title")
                    ui.p(f"Description for item {i}", class_="description")
                    with ui.ul(class_="list"):
                        for j in range(5):
                            ui.li(f"Sub-item {j}", data_sub_index=str(j))
                tag.append(item)

            return tag

        # Warm up
        for _ in range(50):
            str(create_large_tag())

        # Benchmark
        start = time.perf_counter()
        for _ in range(iterations):
            str(create_large_tag())
        elapsed = time.perf_counter() - start

        # Should complete in reasonable time (< 20s for 500 iterations)
        # This is a regression test - we expect O(n) performance
        assert elapsed < 20.0, f"Large tag rendering too slow: {elapsed:.4f}s for {iterations} iterations"

        per_iteration = (elapsed / iterations) * 1000
        print(f"\nLarge tag: {per_iteration:.4f}ms per iteration ({iterations} iterations in {elapsed:.4f}s)")

    def test_nested_structure_performance(self):
        """Benchmark deeply nested structures.

        Expected: Performance improvement compounds with nesting depth.
        """
        iterations = 500

        # Create a deeply nested structure
        def create_nested_structure():
            with ui.div(id="root", class_="container") as root:
                with ui.div(class_="level-1"):
                    with ui.div(class_="level-2"):
                        with ui.div(class_="level-3"):
                            with ui.div(class_="level-4"):
                                with ui.div(class_="level-5"):
                                    for i in range(10):
                                        ui.p(f"Content {i}", class_="deep-content", data_index=str(i))
            return root

        # Warm up
        for _ in range(50):
            str(create_nested_structure())

        # Benchmark
        start = time.perf_counter()
        for _ in range(iterations):
            str(create_nested_structure())
        elapsed = time.perf_counter() - start

        # Should complete in reasonable time (< 3s for 500 iterations)
        # This is a regression test - we expect O(n) performance
        assert elapsed < 3.0, f"Nested structure rendering too slow: {elapsed:.4f}s for {iterations} iterations"

        per_iteration = (elapsed / iterations) * 1000
        print(f"\nNested structure: {per_iteration:.4f}ms per iteration ({iterations} iterations in {elapsed:.4f}s)")

    @pytest.mark.parametrize("attr_count", [5, 10, 25, 50, 100])
    def test_attribute_scaling(self, attr_count: int):
        """Test that performance scales linearly with attribute count.

        With O(n) algorithm, doubling attributes should roughly double time.
        """
        iterations = 500

        # Create tag with specified number of attributes
        def create_tag_with_attrs(count: int):
            attrs = {f"data_attr_{i}": f"value_{i}" for i in range(count)}
            attrs["id"] = "test"
            attrs["class_"] = "container"
            return ui.div(**attrs)

        # Warm up
        for _ in range(50):
            str(create_tag_with_attrs(attr_count))

        # Benchmark
        start = time.perf_counter()
        for _ in range(iterations):
            str(create_tag_with_attrs(attr_count))
        elapsed = time.perf_counter() - start

        per_iteration = (elapsed / iterations) * 1000

        # Should maintain reasonable performance even with many attributes
        # Allow 10ms per 100 attributes (regression test for O(n) behavior)
        max_time = (attr_count / 100) * 10
        assert per_iteration < max_time, (
            f"Attribute scaling: {attr_count} attributes took {per_iteration:.4f}ms, expected < {max_time:.2f}ms"
        )

        print(f"\n{attr_count} attributes: {per_iteration:.4f}ms per iteration")

    @pytest.mark.parametrize("child_count", [10, 25, 50, 100, 200])
    def test_children_scaling(self, child_count: int):
        """Test that performance scales linearly with child count.

        With O(n) algorithm, doubling children should roughly double time.
        """
        iterations = 500

        # Create tag with specified number of children
        def create_tag_with_children(count: int):
            tag = ui.div(id="parent", class_="container")
            for i in range(count):
                tag.append(ui.p(f"Child {i}", data_index=str(i)))
            return tag

        # Warm up
        for _ in range(50):
            str(create_tag_with_children(child_count))

        # Benchmark
        start = time.perf_counter()
        for _ in range(iterations):
            str(create_tag_with_children(child_count))
        elapsed = time.perf_counter() - start

        per_iteration = (elapsed / iterations) * 1000

        # Should maintain reasonable performance even with many children
        # Allow 10ms per 100 children (regression test for O(n) behavior)
        max_time = (child_count / 100) * 10
        assert per_iteration < max_time, (
            f"Children scaling: {child_count} children took {per_iteration:.4f}ms, expected < {max_time:.2f}ms"
        )

        print(f"\n{child_count} children: {per_iteration:.4f}ms per iteration")


class TestFragmentPerformance:
    """Benchmark tests for fragment rendering."""

    def test_fragment_with_many_children(self):
        """Test fragment performance with many children.

        Fragments use a different code path in __str__().
        """
        iterations = 1000

        # Create fragment with many children
        def create_fragment():
            with ui.div(name="fragment") as fragment:
                for i in range(50):
                    ui.p(f"Paragraph {i}")
            fragment.name = "fragment"  # Convert to fragment
            return fragment

        # Warm up
        for _ in range(100):
            str(create_fragment())

        # Benchmark
        start = time.perf_counter()
        for _ in range(iterations):
            str(create_fragment())
        elapsed = time.perf_counter() - start

        # Should complete in reasonable time (< 4s for 1000 iterations)
        # This is a regression test - we expect O(n) performance
        assert elapsed < 4.0, f"Fragment rendering too slow: {elapsed:.4f}s"

        per_iteration = (elapsed / iterations) * 1000
        print(f"\nFragment (50 children): {per_iteration:.4f}ms per iteration")
