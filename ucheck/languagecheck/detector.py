import re

def languagecheck(text: str = "") -> str:
    """
    Detect the programming language of the given code text.
    
    Args:
        text (str): The code text to analyze. Defaults to empty string.
        
    Returns:
        str: The detected programming language code:
             - "py" for Python
             - "cpp" for C++
             - "c" for C
             - "java" for Java
             - "js" for JavaScript
             - "ts" for TypeScript
             - "go" for Go
             - "r" for R
             - "matlab" for MATLAB
             - "shell" for Shell/Bash
             - "sql" for SQL
             - "html" for HTML
             - "css" for CSS
             - "unknown" for unrecognized languages
    """
    
    if not text or not text.strip():
        return "unknown"
    
    text_clean = text.strip()
    text_lower = text_clean.lower()
    
    language_patterns = {
        "py": {
            "keywords": ["def ", "import ", "from ", "class ", "if __name__", "print(", "elif ", "lambda "],
            "patterns": [r"def\s+\w+\s*\(", r"import\s+\w+", r"from\s+\w+\s+import", r"#.*", r"print\s*\("]
        },
        "java": {
            "keywords": ["public class", "public static void main", "System.out.println", "import java", "public static", "private ", "protected "],
            "patterns": [r"public\s+class\s+\w+", r"System\.out\.println", r"public\s+static\s+void\s+main"]
        },
        "cpp": {
            "keywords": ["#include <", "std::", "cout <<", "cin >>", "namespace std", "using namespace", "int main()"],
            "patterns": [r"#include\s*<\w+>", r"std::\w+", r"cout\s*<<", r"cin\s*>>", r"using\s+namespace\s+std"]
        },
        "c": {
            "keywords": ["#include <stdio.h>", "#include <stdlib.h>", "printf(", "scanf(", "int main()", "void main()"],
            "patterns": [r"#include\s*<\w+\.h>", r"printf\s*\(", r"scanf\s*\(", r"int\s+main\s*\(\s*\)"]
        },
        "js": {
            "keywords": ["function ", "var ", "let ", "const ", "console.log", "document.", "window.", "=> "],
            "patterns": [r"function\s+\w+\s*\(", r"console\.log\s*\(", r"document\.\w+", r"=>\s*", r"var\s+\w+\s*="]
        },
        "ts": {
            "keywords": ["interface ", "type ", ": string", ": number", ": boolean", "export ", "import {"],
            "patterns": [r"interface\s+\w+", r":\s*(string|number|boolean)", r"export\s+(interface|type|class)"]
        },
        "go": {
            "keywords": ["package main", "func main()", "import (", "fmt.Println", "var ", "func "],
            "patterns": [r"package\s+main", r"func\s+main\s*\(\s*\)", r"fmt\.Println", r"func\s+\w+\s*\("]
        },
        "r": {
            "keywords": ["library(", "<- ", "print(", "cat(", "data.frame(", "c("],
            "patterns": [r"library\s*\(", r"\w+\s*<-", r"data\.frame\s*\(", r"\bc\s*\("]
        },
        "matlab": {
            "keywords": ["function ", "end", "fprintf(", "disp(", "plot(", "clear all"],
            "patterns": [r"function\s+\w+", r"fprintf\s*\(", r"disp\s*\(", r"clear\s+all"]
        },
        "shell": {
            "keywords": ["#!/bin/bash", "#!/bin/sh", "echo ", "if [", "for ", "while "],
            "patterns": [r"#!/bin/(bash|sh)", r"echo\s+", r"if\s*\[", r"\$\w+"]
        },
        "sql": {
            "keywords": ["SELECT ", "FROM ", "WHERE ", "INSERT INTO", "UPDATE ", "DELETE FROM", "CREATE TABLE"],
            "patterns": [r"SELECT\s+.*\s+FROM", r"INSERT\s+INTO", r"CREATE\s+TABLE", r"UPDATE\s+\w+\s+SET"]
        },
        "html": {
            "keywords": ["<html>", "<head>", "<body>", "<div>", "<!DOCTYPE", "<script>"],
            "patterns": [r"<!DOCTYPE\s+html>", r"<(html|head|body|div|script)", r"</\w+>"]
        },
        "css": {
            "keywords": ["{", "}", "color:", "background:", "margin:", "padding:"],
            "patterns": [r"\w+\s*\{[^}]*\}", r"(color|background|margin|padding)\s*:", r"#[0-9a-fA-F]{3,6}"]
        }
    }
    
    # Score each language based on keyword and pattern matches
    language_scores: dict[str, int] = {}
    
    for lang, rules in language_patterns.items():
        score = 0
        
        # Check keywords
        for keyword in rules["keywords"]:
            if keyword.lower() in text_lower:
                score += 2
        
        # Check patterns
        for pattern in rules["patterns"]:
            matches = re.findall(pattern, text_clean, re.IGNORECASE | re.MULTILINE)
            score += len(matches)
    
        if score > 0:
            language_scores[lang] = score
    
    # Special cases and additional heuristics
    
    # C++ vs C disambiguation
    if "cpp" in language_scores and "c" in language_scores:
        if any(keyword in text_lower for keyword in ["std::", "cout", "cin", "namespace", "using namespace"]):
            language_scores["cpp"] += 3
        else:
            language_scores["c"] += 1
    
    # JavaScript vs TypeScript disambiguation
    if "js" in language_scores and "ts" in language_scores:
        if any(keyword in text_lower for keyword in ["interface", "type ", ": string", ": number", ": boolean"]):
            language_scores["ts"] += 3
        else:
            language_scores["js"] += 1
    
    # Return the language with the highest score
    if language_scores:
        return max(language_scores.keys(), key=lambda x: language_scores[x])
    
    return "unknown"



def get_supported_languages() -> list[str]:
    """
    Get a list of all supported programming languages.
    
    Returns:
        list: List of supported language codes.
    """
    return [
        "py", "cpp", "c", "java", "js", "ts", "go", "r", "matlab", "shell", 
        "sql", "html", "css"
    ]


def get_language_name(code: str) -> str:
    """
    Get the full name of a programming language from its code.
    
    Args:
        code (str): The language code (e.g., "py", "cpp", "java").
        
    Returns:
        str: The full name of the programming language.
    """
    language_names = {
        "py": "Python",
        "cpp": "C++",
        "c": "C",
        "java": "Java",
        "js": "JavaScript",
        "ts": "TypeScript",
        "go": "Go",
        "r": "R",
        "matlab": "MATLAB",
        "shell": "Shell/Bash",
        "sql": "SQL",
        "html": "HTML",
        "css": "CSS",
        "unknown": "Unknown"
    }
    return language_names.get(code, "Unknown")