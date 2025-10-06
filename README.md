# UtilityCheck

Code analysis toolkit with language detection, function extraction, and utility ranking.

## Quick Start

```bash
git clone https://github.com/hexronuspi/utilityCheck.git
cd utilityCheck
pip install -e .
```

## Features

### 1. Language Detection
Detect programming languages from code snippets.

```python
from utilitycheck import languagecheck

code = 'def hello(): print("Hello World")'
print(languagecheck(code))  # "py"
```

**Supported Languages**: Python, Java, C++, C, JavaScript, TypeScript, Go, R, MATLAB, Shell, SQL, HTML, CSS

### 2. Function Extraction
Extract functions from source files with cleaned code (no comments/docstrings).

```bash
# Extract from single file
python -m utilitycheck.utility.parser file.py

# Extract from directory
python -m utilitycheck.utility.parser src/

# Custom output directory
python -m utilitycheck.utility.parser src/ output_data/
```

**Output**: JSON file with function metadata and cleaned code.

### 3. Utility Ranking
Rank functions by utility score and classify as utility/core functions.

```bash
# Rank functions with default threshold (0.8)
python -m utilitycheck.rank.weightrank data/

# Custom threshold
python -m utilitycheck.rank.weightrank data/ 0.7

# Different data directory
python -m utilitycheck.rank.weightrank custom_data/ 0.8
```

**Output**: `{filename}_rank.json` with rank scores and `isUtil` classification.

## Workflow

1. **Extract functions**: `python -m utilitycheck.utility.parser src/`
2. **Rank functions**: `python -m utilitycheck.rank.weightrank data/`
3. **Check results**: View `data/{project}_rank.json`

## Testing

```bash
python test_languagecheck.py  # Language detection tests
python test_parser.py         # Function extraction tests
```

## File Structure

```
utilityCheck/
├── utilitycheck/
│   ├── languagecheck/    # Language detection
│   ├── utility/         # Function extraction  
│   └── rank/            # Utility ranking
├── data/                # Output JSON files
└── tests/               # Test files
```

## API Reference

### Language Detection
```python
languagecheck(text: str) -> str                    # Detect language
get_supported_languages() -> List[str]             # List supported languages
get_language_name(code: str) -> str                # Get full language name
```

### Function Extraction
```python
parse_code(path: str, output_dir: str) -> Dict     # Extract functions
```

### Utility Ranking
```python
rank_code(data_dir: str, threshold: float) -> Dict # Rank functions
```

## Ranking Criteria

Functions are scored based on:
- **Simplicity**: Fewer lines, simple returns
- **Function calls**: Moderate complexity preferred
- **Control structures**: Some complexity acceptable
- **Name patterns**: "get", "set", "util" names get bonus

**Threshold**: Functions with score ≥ threshold are classified as utilities (`isUtil: true`).

## License

MIT License
