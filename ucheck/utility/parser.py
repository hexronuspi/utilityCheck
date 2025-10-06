import os
import ast
import json
from typing import Dict, List, Any
from ..languagecheck.detector import languagecheck


class FunctionExtractor:
    """Extract functions from Python files and organize them in a tree structure."""
    
    def __init__(self):
        self.supported_languages = {"py": self._parse_python}
        self.graph_nodes: List[Dict[str, Any]] = []
    
    def _clean_code(self, code: str) -> str:
        """Remove comments and docstrings from Python code."""
        try:
            # Parse the code into an AST
            tree = ast.parse(code)
            
            # Convert back to source code without comments and docstrings
            lines = code.split('\n')
            cleaned_lines: List[str] = []
            
            for line in lines:
                # Remove inline comments (but preserve strings with #)
                cleaned_line = self._remove_inline_comments(line)
                
                # Skip empty lines that result from comment removal
                if cleaned_line.strip():
                    cleaned_lines.append(cleaned_line)
            
            # Parse again to remove docstrings
            cleaned_code = '\n'.join(cleaned_lines)
            if cleaned_code.strip():
                tree = ast.parse(cleaned_code)
                return self._remove_docstrings_from_ast(tree, cleaned_code)
            
            return cleaned_code
            
        except:
            # If parsing fails, do basic comment removal
            return self._basic_comment_removal(code)
    
    def _remove_inline_comments(self, line: str) -> str:
        """Remove inline comments while preserving # in strings."""
        in_string = False
        string_char = None
        escaped = False
        result: List[str] = []
        
        i = 0
        while i < len(line):
            char = line[i]
            
            if escaped:
                result.append(char)
                escaped = False
            elif char == '\\' and in_string:
                result.append(char)
                escaped = True
            elif char in ['"', "'"] and not in_string:
                in_string = True
                string_char = char
                result.append(char)
            elif char == string_char and in_string:
                in_string = False
                string_char = None
                result.append(char)
            elif char == '#' and not in_string:
                # Found a comment, stop here
                break
            else:
                result.append(char)
            
            i += 1
        
        return ''.join(result).rstrip()
    
    def _remove_docstrings_from_ast(self, tree: ast.Module, code: str) -> str:
        """Remove docstrings from AST and return cleaned code."""
        lines = code.split('\n')
        lines_to_remove: set[int] = set()
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef)):
                if (node.body and 
                    isinstance(node.body[0], ast.Expr) and 
                    isinstance(node.body[0].value, ast.Constant) and 
                    isinstance(node.body[0].value.value, str)):
                    
                    # This is a docstring, mark lines for removal
                    docstring_node = node.body[0]
                    start_line = docstring_node.lineno - 1
                    end_line = getattr(docstring_node, 'end_lineno', start_line + 1) - 1
                    
                    for line_num in range(start_line, end_line + 1):
                        if line_num < len(lines):
                            lines_to_remove.add(line_num)
        
        # Also check for module-level docstrings
        if (tree.body and 
            isinstance(tree.body[0], ast.Expr) and 
            isinstance(tree.body[0].value, ast.Constant) and 
            isinstance(tree.body[0].value.value, str)):
            
            docstring_node = tree.body[0]
            start_line = docstring_node.lineno - 1
            end_line = getattr(docstring_node, 'end_lineno', start_line + 1) - 1
            
            for line_num in range(start_line, end_line + 1):
                if line_num < len(lines):
                    lines_to_remove.add(line_num)
        
        # Filter out the docstring lines
        cleaned_lines = [line for i, line in enumerate(lines) if i not in lines_to_remove]
        return '\n'.join(cleaned_lines)
    
    def _basic_comment_removal(self, code: str) -> str:
        """Basic comment and docstring removal as fallback."""
        lines = code.split('\n')
        cleaned_lines: List[str] = []
        in_multiline_string = False
        string_delim = None
        
        for line in lines:
            stripped = line.strip()
            
            # Skip docstring lines
            if (stripped.startswith('"""') or stripped.startswith("'''") or
                stripped.startswith('r"""') or stripped.startswith("r'''")):
                if not in_multiline_string:
                    in_multiline_string = True
                    string_delim = '"""' if '"""' in stripped else "'''"
                    if stripped.count(string_delim) >= 2:
                        in_multiline_string = False
                    continue
                elif string_delim is not None and string_delim in stripped:
                    in_multiline_string = False
                    continue
            
            if in_multiline_string:
                continue
            
            # Remove inline comments
            clean_line = self._remove_inline_comments(line)
            if clean_line.strip():
                cleaned_lines.append(clean_line)
        
        return '\n'.join(cleaned_lines)
    
    def _parse_python(self, file_path: str, content: str, relative_path: str) -> List[Dict[str, Any]]:
        """Extract functions from Python code using AST."""
        functions: List[Dict[str, Any]] = []
        
        try:
            tree = ast.parse(content)
            
            # Only process top-level nodes to avoid duplicates
            for node in tree.body:
                if isinstance(node, ast.FunctionDef):
                    # Extract function definition
                    func_start = node.lineno
                    func_end = getattr(node, 'end_lineno', func_start)
                    
                    # Get the function code
                    lines = content.split('\n')
                    func_lines = lines[func_start-1:func_end]
                    func_code = '\n'.join(func_lines)
                    
                    # Clean the code by removing comments and docstrings
                    cleaned_code = self._clean_code(func_code)
                    
                    function_data = {
                        "id": f"code:{relative_path}#{node.name}",
                        "label": node.name,
                        "code": cleaned_code,
                        "language": "py"
                    }
                    functions.append(function_data)
                
                elif isinstance(node, ast.ClassDef):
                    # Extract methods from classes as separate functions
                    for item in node.body:
                        if isinstance(item, ast.FunctionDef):
                            func_start = item.lineno
                            func_end = getattr(item, 'end_lineno', func_start)
                            
                            lines = content.split('\n')
                            func_lines = lines[func_start-1:func_end]
                            func_code = '\n'.join(func_lines)
                            
                            # Clean the code by removing comments and docstrings
                            cleaned_code = self._clean_code(func_code)
                            
                            function_data = {
                                "id": f"code:{relative_path}#{node.name}.{item.name}",
                                "label": f"{node.name}.{item.name}",
                                "code": cleaned_code,
                                "language": "py"
                            }
                            functions.append(function_data)
        
        except SyntaxError as e:
            print(f"Syntax error in {file_path}: {e}")
        except Exception as e:
            print(f"Error parsing {file_path}: {e}")
        
        return functions
    
    def _get_relative_path(self, file_path: str, base_path: str) -> str:
        """Get relative path from base directory."""
        return os.path.relpath(file_path, base_path).replace('\\', '/')
    
    def _process_file(self, file_path: str, base_path: str) -> None:
        """Process a single file and extract functions."""
        # Skip binary files and cache files
        if (file_path.endswith('.pyc') or 
            file_path.endswith('.pyo') or 
            '__pycache__' in file_path or
            file_path.endswith('.so') or
            file_path.endswith('.dll')):
            return
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check language type
            language = languagecheck(content)
            
            if language in self.supported_languages:
                relative_path = self._get_relative_path(file_path, base_path)
                functions = self.supported_languages[language](file_path, content, relative_path)
                self.graph_nodes.extend(functions)
            
        except Exception as e:
            print(f"Error processing file {file_path}: {e}")
    
    def _walk_directory(self, directory_path: str, base_path: str) -> None:
        """Recursively walk through directory and process files."""
        for root, _, files in os.walk(directory_path):
            for file in files:
                file_path = os.path.join(root, file)
                self._process_file(file_path, base_path)
    
    def performParse(self, path: str, output_dir: str = "data") -> Dict[str, Any]:
        """
        Parse files/folders and extract functions.
        
        Args:
            path (str): Path to file or directory to parse
            output_dir (str): Directory to save the output JSON file
            
        Returns:
            Dict[str, Any]: Analysis data with graph nodes
        """
        self.graph_nodes = []  # Reset nodes for new parsing
        
        if not os.path.exists(path):
            raise FileNotFoundError(f"Path does not exist: {path}")
        
        base_path = os.path.dirname(path) if os.path.isfile(path) else path
        
        if os.path.isfile(path):
            self._process_file(path, base_path)
        elif os.path.isdir(path):
            self._walk_directory(path, path)
        
        # Create analysis data structure
        analysis_data = {
            "analysisData": {
                "graphNodes": self.graph_nodes
            }
        }
        
        # Save to JSON file - use absolute path for data directory
        if not os.path.isabs(output_dir):
            # Find the project root (where setup.py or README.md exists)
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = current_dir
            while project_root != os.path.dirname(project_root):
                if (os.path.exists(os.path.join(project_root, 'setup.py')) or 
                    os.path.exists(os.path.join(project_root, 'README.md'))):
                    break
                project_root = os.path.dirname(project_root)
            output_dir = os.path.join(project_root, output_dir)
        
        os.makedirs(output_dir, exist_ok=True)
        
        # Create filename based on the parsed path
        if os.path.isfile(path):
            filename = os.path.splitext(os.path.basename(path))[0]
        else:
            filename = os.path.basename(path.rstrip('/\\'))
        
        output_file = os.path.join(output_dir, f"{filename}.json")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(analysis_data, f, indent=2)
        
        print(f"Analysis saved to: {output_file}")
        print(f"Found {len(self.graph_nodes)} functions")
        
        return analysis_data


def parse_code(path: str, output_dir: str = "data") -> Dict[str, Any]:
    """
    Convenience function to parse code and extract functions.
    
    Args:
        path (str): Path to file or directory to parse
        output_dir (str): Directory to save the output JSON file
        
    Returns:
        Dict[str, Any]: Analysis data with graph nodes
    """
    extractor = FunctionExtractor()
    return extractor.performParse(path, output_dir)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        path = sys.argv[1]
        output_dir = sys.argv[2] if len(sys.argv) > 2 else "data"
        parse_code(path, output_dir)
    else:
        print("Usage: python parser.py <path> [output_dir]")
