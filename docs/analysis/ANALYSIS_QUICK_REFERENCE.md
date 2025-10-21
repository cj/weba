# Weba Improvement Guide - Quick Reference

## Quick File Locations Reference

### Files Most Needing Changes

| File | Lines | Priority | Issues |
|------|-------|----------|--------|
| `tag.py` | 424 | HIGH | Test code (228), commented code (266, 299-301, 331-333, 416-424), complex logic (223-251), string concat (354-414) |
| `ui.py` | 225 | HIGH | Duplicate code (172-222), no caching (132-134), type ignores (3) |
| `component.py` | 375 | HIGH | Type ignores (8), missing cache methods, weak validation (193-210) |
| `tag_decorator.py` | 83 | MEDIUM | Missing docstrings (34, 38), incomplete error handling (54) |
| `context.py` | 48 | LOW | Unused ContextMixin implementation, not used |
| `errors.py` | 79 | LOW | Error messages could be more descriptive |

---

## High-Priority Fixes (Code Examples)

### FIX #1: Remove Test-Specific Code (tag.py:228-230)

**Current:**
```python
# tag.py, Line 223-251, inside Tag.__getitem__
def __getitem__(self, key: str) -> str | list[str]:
    if key == "class":
        current_value = self.attrs.get("class")

        # For test_ui_tag_attributes, there's a specific test case with value 42
        if current_value == 42:
            # Special case - return empty list as test requires
            return []
```

**Fixed:**
```python
def __getitem__(self, key: str) -> str | list[str]:
    if key == "class":
        current_value = self.attrs.get("class")

        # Handle None - no class attribute set
        if current_value is None:
            return []
        
        # ... rest of logic
```

**Action:** Grep and remove in line 228-230, update test to use proper fixture

---

### FIX #2: Remove Commented Code (tag.py:266, 299-301, 331-333, 416-424)

**Current:** 60+ lines of commented code

**Action:** Delete entirely:
- Line 266: Commented return type annotation
- Lines 299-301: Commented NavigableString handling in `comment()`
- Lines 331-333: Commented NavigableString handling in `comment_one()`
- Lines 416-424: Entire commented `output_ready()` method

**Result:** Clean tag.py to ~360 lines

---

### FIX #3: Implement Missing Cache Methods (component.py)

**Add to Component class:**
```python
# After line 350, add:

def clear_cache(self) -> None:
    """Clear instance-level cache for this component.
    
    This removes cached tag selectors found by @tag decorators.
    Useful for memory management when reusing component instances.
    """
    self._cached_tags.clear()

@classmethod
def clear_class_cache(cls) -> None:
    """Clear all class-level caches.
    
    This clears the LRU cache used for source file parsing.
    Affects all instances of this component class.
    
    Example:
        UserCard.clear_class_cache()  # Reset source parsing cache
    """
    # Clear LRU cache for _parse_source_content if it exists
    if hasattr(cls._parse_source_content, 'cache_clear'):
        cls._parse_source_content.cache_clear()
```

---

### FIX #4: Optimize String Concatenation (tag.py:354-414)

**Current (inefficient):**
```python
def __str__(self) -> str:
    if self.name == "fragment":
        return "".join(str(child) for child in self.contents)

    doctype_prefix: str = ""
    if hasattr(self, "_doctype") and self._doctype:
        doctype_prefix = str(self._doctype) + "\n"

    result = f"<{self.name}"

    for key, value in self.attrs.items():
        if value == "":
            result += f" {key}"
        elif isinstance(value, list):
            # ... build result with += operations
            result += f' {key}="{escaped_value}"'
        # ... more += operations
    
    result += ">"
    for child in self.contents:
        result += f"<!--{child}-->" if isinstance(child, Comment) else str(child)
    result += f"</{self.name}>"

    return doctype_prefix + result
```

**Fixed (efficient):**
```python
def __str__(self) -> str:
    if self.name == "fragment":
        return "".join(str(child) for child in self.contents)

    # Build as list for O(n) performance
    parts: list[str] = []
    
    if hasattr(self, "_doctype") and self._doctype:
        parts.append(str(self._doctype))
        parts.append("\n")
    
    parts.append(f"<{self.name}")
    
    # Add attributes
    for key, value in self.attrs.items():
        if value == "":
            parts.append(f" {key}")
        elif isinstance(value, list):
            value_str = " ".join(str(item) for item in value)
            escaped_value = html.escape(value_str, quote=False)
            parts.append(f' {key}="{escaped_value}"')
        elif value is not None:
            # ... handle other cases
            parts.append(f' {key}="{escaped_value}"')
    
    if self.contents:
        parts.append(">")
        for child in self.contents:
            if isinstance(child, Comment):
                parts.append(f"<!--{child}-->")
            else:
                parts.append(str(child))
        parts.append(f"</{self.name}>")
    else:
        parts.append(f"></{self.name}>")
    
    return "".join(parts)
```

---

### FIX #5: Add Missing Docstrings

**tag_decorator.py - Add docstrings:**

```python
def __set__(self, instance: T, value: Tag):
    """Set the tag value, replacing the old tag with the new one.
    
    This descriptor method allows assignment like:
        component.my_tag = new_tag
    
    Args:
        instance: The component instance
        value: The new Tag to replace the old one with
    """
    getattr(instance, self.method.__name__).replace_with(value)
    instance._cached_tags[self.__name__] = value

def __get__(self, instance: T, owner: type[T]) -> Tag:
    """Get the tag, executing the decorated method if needed.
    
    This descriptor implements the @tag decorator functionality.
    It finds the tag using the selector and caches the result.
    
    Args:
        instance: The component instance
        owner: The component class
        
    Returns:
        The Tag found by the selector or returned by the method
        
    Raises:
        ComponentTagNotFoundError: If selector doesn't match any element
    """
    # Return cached result if it exists
    if response := instance._cached_tags.get(self.__name__):
        return response
    # ... rest of method
```

---

## Medium-Priority Improvements

### IMPROVEMENT #1: Extract Attribute Processing (ui.py)

**Current pattern (repeated):**
```python
# In Ui.__getattr__
for key, value in kwargs.items():
    processed_key = self._process_attribute_key(key)
    include, processed_value = self._process_attribute_value(processed_key, value)
    if include:
        converted_kwargs[processed_key] = processed_value
```

**Better approach:**
```python
def _convert_attributes(self, kwargs: dict[str, Any]) -> dict[str, Any]:
    """Convert all attributes from kwargs format to HTML format.
    
    Handles:
    - Underscore to dash conversion (data_x -> data-x)
    - Class attribute list processing
    - Boolean attribute empty string handling
    
    Args:
        kwargs: Raw keyword arguments from tag creation
        
    Returns:
        Dictionary with processed attributes ready for Tag creation
    """
    result: dict[str, Any] = {}
    
    # Handle special class operations separately
    append_class = kwargs.pop("_append_class", None)
    prepend_class = kwargs.pop("_prepend_class", None)
    
    # Process regular attributes
    for key, value in kwargs.items():
        processed_key = self._process_attribute_key(key)
        include, processed_value = self._process_attribute_value(processed_key, value)
        
        if include:
            result[processed_key] = processed_value
    
    return result, append_class, prepend_class

# Usage in __getattr__:
converted, append_cls, prepend_cls = self._convert_attributes(kwargs)
```

---

### IMPROVEMENT #2: Add Caching to _process_attribute_key (ui.py)

**Before:**
```python
def _process_attribute_key(self, key: str) -> str:
    """Process attribute key by converting underscores to dashes."""
    return key.rstrip("_").replace("_", "-")
```

**After:**
```python
# Add at class level
_attribute_key_cache: ClassVar[dict[str, str]] = {}

def _process_attribute_key(self, key: str) -> str:
    """Process attribute key by converting underscores to dashes.
    
    Cached for performance - common keys like 'class_', 'hx_post'
    are converted repeatedly.
    """
    if key in self._attribute_key_cache:
        return self._attribute_key_cache[key]
    
    result = key.rstrip("_").replace("_", "-")
    
    # Only cache if dictionary doesn't exceed 1000 entries
    if len(self._attribute_key_cache) < 1000:
        self._attribute_key_cache[key] = result
    
    return result
```

---

### IMPROVEMENT #3: Add Comment Selector Helper (component_tag.py or __init__.py)

**Add helper function:**
```python
def comment_selector(selector: str) -> str:
    """Create an HTML comment-based selector for @tag decorator.
    
    HTML comments are used to mark sections of templates that should
    be populated by component methods.
    
    Args:
        selector: The selector text without comment markers
        
    Returns:
        Formatted comment selector ready for @tag decorator
        
    Example:
        @tag(comment_selector("refresh-button"))
        def setup_refresh(self, button_tag: Tag):
            button_tag["onclick"] = "location.reload()"
        
        # Corresponds to HTML:
        # <div><!-- refresh-button --><button>Refresh</button></div>
    """
    return f"<!-- {selector} -->"

# Or as an alternative class-based approach
class Selector:
    @staticmethod
    def comment(text: str) -> str:
        """Create HTML comment selector."""
        return f"<!-- {text} -->"
    
    @staticmethod
    def css(text: str) -> str:
        """Create CSS selector (identity function for clarity)."""
        return text
```

---

### IMPROVEMENT #4: Add Boolean Attribute Helpers (tag.py)

**Add methods to Tag class:**
```python
def set_boolean(self, name: str, value: bool = True) -> Self:
    """Set a boolean attribute.
    
    In HTML, boolean attributes are set by presence (disabled) or
    absence (no disabled attribute). This method handles the conversion.
    
    Args:
        name: Attribute name (e.g., 'disabled', 'readonly')
        value: True to enable, False to remove
        
    Returns:
        self for chaining
        
    Example:
        tag.set_boolean("disabled", True)  # Adds disabled=""
        tag.set_boolean("disabled", False)  # Removes disabled
    """
    if value:
        self[name] = ""
    else:
        self.attrs.pop(name, None)
    return self

def has_boolean(self, name: str) -> bool:
    """Check if a boolean attribute is set.
    
    Args:
        name: Attribute name to check
        
    Returns:
        True if attribute exists, False otherwise
    """
    return name in self.attrs

# Add convenience properties for common boolean attributes
@property
def disabled(self) -> bool:
    return self.has_boolean("disabled")

@disabled.setter
def disabled(self, value: bool) -> None:
    self.set_boolean("disabled", value)
```

---

### IMPROVEMENT #5: Add Class Manipulation Helpers (tag.py)

**Add to Tag class:**
```python
def add_class(self, *classes: str) -> Self:
    """Add one or more CSS classes.
    
    Args:
        *classes: One or more class names to add
        
    Returns:
        self for chaining
        
    Example:
        tag.add_class("active").add_class("highlight")
    """
    for cls in classes:
        if cls not in self["class"]:
            self["class"].append(cls)
    return self

def remove_class(self, *classes: str) -> Self:
    """Remove one or more CSS classes.
    
    Args:
        *classes: One or more class names to remove
        
    Returns:
        self for chaining
    """
    class_list = self["class"]
    for cls in classes:
        if cls in class_list:
            class_list.remove(cls)
    return self

def toggle_class(self, cls: str, force: bool | None = None) -> Self:
    """Toggle a CSS class.
    
    Args:
        cls: Class name to toggle
        force: If True, add class; if False, remove class;
               if None, toggle based on current state
        
    Returns:
        self for chaining
    """
    has_class = cls in self["class"]
    
    if force is None:
        force = not has_class
    
    if force and not has_class:
        self["class"].append(cls)
    elif not force and has_class:
        self["class"].remove(cls)
    
    return self

def has_class(self, cls: str) -> bool:
    """Check if tag has a CSS class.
    
    Args:
        cls: Class name to check
        
    Returns:
        True if class is present, False otherwise
    """
    return cls in self["class"]
```

---

## Type Annotation Improvements

### ISSUE: Excessive Type Ignores

**Current state:** 25+ `# pyright: ignore[...]` annotations

**Strategy:**

1. **For ContextVar issues (tag.py:147, 152):**
   ```python
   # Instead of:
   self._token = current_tag_context.set(self)  # pyright: ignore[...]
   
   # Use better typing:
   from typing import TypeVar
   
   TagT = TypeVar('TagT', bound='Tag')
   
   def _set_context(self: TagT) -> Token[TagT | None]:
       """Set this tag as current context."""
       return current_tag_context.set(self)
   ```

2. **For list type handling (tag.py:240, 376):**
   ```python
   # Instead of:
   value_list: list[Any] = current_value  # pyright: ignore[...]
   
   # Use cast:
   from typing import cast
   
   value_list = cast(list[str], current_value)
   ```

3. **For metaclass issues (component.py:101):**
   ```python
   # Properly type the __call__ method
   def __call__(cls, *args: Any, **kwargs: Any) -> Component:  # Better return type
       return cls.__new__(cls)
   ```

---

## Testing Additions Needed

**Add tests for:**
1. cache methods: `test_component_clear_cache()`
2. Boolean helpers: `test_tag_disabled_property()`
3. Class helpers: `test_tag_add_remove_class()`
4. Selector helpers: `test_comment_selector_helper()`
5. Performance: `test_string_concat_performance()`

---

## Files Modified Summary

```
HIGH PRIORITY:
  weba/tag.py              ← Remove test code, commented code, optimize string concat
  weba/ui.py               ← Refactor attribute processing, add caching
  weba/component.py        ← Add cache methods, improve validation
  
MEDIUM PRIORITY:
  weba/tag_decorator.py    ← Add docstrings
  weba/errors.py           ← Improve error messages
  weba/component_tag.py    ← Add helper functions
  
LOW PRIORITY:
  weba/context.py          ← Consider deprecating
  weba/__init__.py         ← Export new helpers
  
DOCUMENTATION:
  README.md                ← Add attribute naming guide
  docs/lifecycle.md        ← Component lifecycle guide
  docs/api-reference.md    ← Complete API reference
```

