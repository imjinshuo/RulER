_SRC_MAPPING_SYSTEM_MSG_py = \
"""You are a helpful assistant that map Python code and translated C++ code. 
For user requests, you output the mapping directly in consistent formats without explanations.
You should not make any changes to the provided code pair when you output the mapping. 
You can only add annotations at the end of the line for each statement.
You should not skip statements when you output the mapping.
"""
_SRC_MAPPING_SYSTEM_MSG_java = \
"""You are a helpful assistant that map Java code and translated C++ code. 
For user requests, you output the mapping directly in consistent formats without explanations.
You should not make any changes to the provided code pair when you output the mapping. 
You can only add annotations at the end of the line for each statement.
You should not skip statements when you output the mapping.
"""

_NEW_TRANS_HEADER_py = "## Code Translation from Python to C++"
_NEW_TRANS_HEADER_java = "## Code Translation from Java to C++"
_NEW_MAPPING_HEADER = "**Please match the above translation statement by statement by appending annotations to the code lines.**"

_SRC_MAPPING_EXAMPLE_py = _NEW_TRANS_HEADER_py \
+ """

### Python

```python
def f_gold(s: str) -> int:
    i = 0
    ans = 0
    chars = set()
    for j, c in enumerate(s):
        if c == ' ':
            continue
        elif c == '*':
            break
        while c in chars:
            chars.remove(s[i])
            i += 1
        chars.add(c)
        ans = max(ans, j - i + 1)
        ans = max(
          ans, i - j + 1
        )
    ans, i = ans * 2, i + 1
    return ans
```

### C++

```cpp
int f_gold(const string& s) {
    int i = 0;
    int ans = 0;
    unordered_set<char> chars;
    for (int j = 0; j < s.length(); ++j) {
        char c = s[j];
        if (c == ' ') continue;
        else if (c == '*') {
            break;
        }
        while (chars.find(c) != chars.end()) {
            chars.erase(s[i]);
            ++i;
        }
        chars.insert(c);
        ans = max(ans, j - i + 1);
        ans = max(ans, i - j + 1);
    }
    ans *= 2;
    i += 1;
    return ans;
}
```

""" + _NEW_MAPPING_HEADER + "\n"

_SRC_MAPPING_EXAMPLE_java = _NEW_TRANS_HEADER_java \
+ """

### Java

```java
public static int f_gold(String s) {
    int i = 0;
    int ans = 0;
    Set<Character> chars = new HashSet<>();
    for (int j = 0; j < s.length(); j++) {
        char c = s.charAt(j);
        if (c == ' ') {
            continue;
        } else if (c == '*') {
            break;
        }
        while (chars.contains(c)) {
            chars.remove(s.charAt(i));
            i++;
        }
        chars.add(c);
        ans = Math.max(ans, j - i + 1);
        ans = Math.max(ans, i - j + 1);
    }
    ans = ans * 2;
    i = i + 1;
    return ans;
}
```

### C++

```cpp
int f_gold(const string& s) {
    int i = 0;
    int ans = 0;
    unordered_set<char> chars;
    for (int j = 0; j < s.length(); ++j) {
        char c = s[j];
        if (c == ' ') continue;
        else if (c == '*') {
            break;
        }
        while (chars.find(c) != chars.end()) {
            chars.erase(s[i]);
            ++i;
        }
        chars.insert(c);
        ans = max(ans, j - i + 1);
        ans = max(ans, i - j + 1);
    }
    ans *= 2;
    i += 1;
    return ans;
}
```

""" + _NEW_MAPPING_HEADER + "\n"

_SRC_MAPPING_EXAMPLE_RESP_py = """### Python

```python
def f_gold(s: str) -> int:
    i = 0   # --- py stmt 1
    ans = 0   # --- py stmt 2
    chars = set()   # --- py stmt 3
    for j, c in enumerate(s):   # --- py stmt 4
        if c == ' ':   # --- py stmt 5
            continue   # --- py stmt 6
        elif c == '*':   # --- py stmt 7
            break   # --- py stmt 8
        while c in chars:   # --- py stmt 9
            chars.remove(s[i])   # --- py stmt 10
            i += 1   # --- py stmt 11
        chars.add(c)   # --- py stmt 12
        ans = max(ans, j - i + 1)   # --- py stmt 13
        ans = max(   # --- py stmt 14
          ans, i - j + 1
        )
    ans, i = ans * 2, i + 1   # --- py stmt 15
    return ans   # --- py stmt 16
```

### C++

```cpp
int f_gold(const string& s) {
    int i = 0;   // --- py stmt 1
    int ans = 0;   // --- py stmt 2
    unordered_set<char> chars;   // --- py stmt 3
    for (int j = 0; j < s.length(); ++j) {   // --- py stmt 4
        char c = s[j];   // --- py stmt 4
        if (c == ' ') continue;   // --- py stmt 5, py stmt 6
        else if (c == '*') {   // --- py stmt 7
            break;   // --- py stmt 8
        }
        while (chars.find(c) != chars.end()) {   // --- py stmt 9
            chars.erase(s[i]);   // --- py stmt 10
            ++i;   // --- py stmt 11
        }
        chars.insert(c);   // --- py stmt 12
        ans = max(ans, j - i + 1);   // --- py stmt 13
        ans = max(ans, i - j + 1);   // --- py stmt 14
    }
    ans *= 2;   // --- py stmt 15
    i += 1;   // --- py stmt 15
    return ans;   // --- py stmt 16
}
```
"""

_SRC_MAPPING_EXAMPLE_RESP_java = """### Java

```java
public static int f_gold(String s) {
    int i = 0;   // --- java stmt 1
    int ans = 0;   // --- java stmt 2
    Set<Character> chars = new HashSet<>();   // --- java stmt 3
    for (int j = 0; j < s.length(); j++) {   // --- java stmt 4
        char c = s.charAt(j);   // --- java stmt 5
        if (c == ' ') {   // --- java stmt 6
            continue;   // --- java stmt 7
        } else if (c == '*') {   // --- java stmt 8
            break;   // --- java stmt 9
        }
        while (chars.contains(c)) {   // --- java stmt 10
            chars.remove(s.charAt(i));   // --- java stmt 11
            i++;   // --- java stmt 12
        }
        chars.add(c);   // --- java stmt 13
        ans = Math.max(ans, j - i + 1);   // --- java stmt 14
        ans = Math.max(ans, i - j + 1);   // --- java stmt 15
    }
    ans = ans * 2;   // --- java stmt 16
    i = i + 1;   // --- java stmt 17
    return ans;   // --- java stmt 18
}
```

### C++

```cpp
int f_gold(const string& s) {
    int i = 0;   // --- java stmt 1
    int ans = 0;   // --- java stmt 2
    unordered_set<char> chars;   // --- java stmt 3
    for (int j = 0; j < s.length(); ++j) {   // --- java stmt 4
        char c = s[j];   // --- java stmt 5
        if (c == ' ') continue;   // --- java stmt 6, java stmt 7
        else if (c == '*') {   // --- java stmt 8
            break;   // --- java stmt 9
        }
        while (chars.find(c) != chars.end()) {   // --- java stmt 10
            chars.erase(s[i]);   // --- java stmt 11
            ++i;   // --- java stmt 12
        }
        chars.insert(c);   // --- java stmt 13
        ans = max(ans, j - i + 1);   // --- java stmt 14
        ans = max(ans, i - j + 1);   // --- java stmt 15
    }
    ans *= 2;   // --- java stmt 16
    i += 1;   // --- java stmt 17
    return ans;   // --- java stmt 18
}
```
"""
_SRC_MAPPING_INPUT_TMPL_py = lambda pycode, cppcode :  \
_NEW_TRANS_HEADER_py + f"""

### Python

```python
{pycode}
```

### C++

```cpp
{cppcode}
```

""" + _NEW_MAPPING_HEADER + "\n"
_SRC_MAPPING_INPUT_TMPL_java = lambda javacode, cppcode :  \
_NEW_TRANS_HEADER_java + f"""

### Java

```java
{javacode}
```

### C++

```cpp
{cppcode}
```

""" + _NEW_MAPPING_HEADER + "\n"


_srcmapping_messages_template_py = lambda pycode, cppcode : (
  _SRC_MAPPING_SYSTEM_MSG_py,
  [(_SRC_MAPPING_EXAMPLE_py, _SRC_MAPPING_EXAMPLE_RESP_py)],
  _SRC_MAPPING_INPUT_TMPL_py(pycode, cppcode)
)
_srcmapping_messages_template_java = lambda javacode, cppcode : (
  _SRC_MAPPING_SYSTEM_MSG_java,
  [(_SRC_MAPPING_EXAMPLE_java, _SRC_MAPPING_EXAMPLE_RESP_java)],
  _SRC_MAPPING_INPUT_TMPL_java(javacode, cppcode)
)