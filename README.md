# UtilityCheck

Code analysis toolkit with language detection, function extraction, and utility ranking.

Step 1) Input folder(sub-files/folders - .py only)
Step 2) Make a Tree for all functions
Step 3) Algo(Mathematically and Statistically Weight functions + If any folder/file has util/utils/utility: bool = true)

A threshold value of 0.7(> 0.7 : bool = true, for utils - This was manually checked after a few experiments `data`)

![Utility Function Analysis](https://github.com/hexronuspi/utilityCheck/blob/main/public/data.png)

Then threshold was set at 0.7(It can be between 0.7 - 0.8, and this can be better known for a particular codebase by using KNN algorithm)

It was tested on the test dataset(as given in google doc - fastapi dataset - there were few null values and other problems, which forced us to use a transformData function)

![Transform Data](https://github.com/hexronuspi/utilityCheck/blob/main/public/transfer%20data.png)

Final Results on fastapi data, it can also be seen under, `testdata`

![Test Data](https://github.com/hexronuspi/utilityCheck/blob/main/public/testdata.png)

## Quick Start

```bash
git clone https://github.com/hexronuspi/utilityCheck.git
cd utilityCheck
pip install -e .
```

## Usage

### Step 1: Transform Data
Convert raw code data to analyzable format:
```bash
python transformData.py
```

### Step 2: Rank Functions
Analyze and rank functions by utility score:
```bash
python ucheck/rank/weightrank.py testData/ 0.7
```

**Output**: Creates `{filename}_rank.json` with function rankings and utility classification.

## Features

### 1. Language Detection
```python
from utilitycheck import languagecheck
print(languagecheck('def hello(): print("Hello")'))  # "py"
```

### 2. Function Extraction & Ranking
- Extracts functions from source files
- Scores based on complexity, naming patterns, and structure
- **Auto-scores utility files**: Functions in `util/utils/utility` folders get score 1.0
- Classifies as utility (`isUtil: true`) or core functions

### 3. Supported Languages
Python, Java, C++, C, JavaScript, TypeScript, Go, R, MATLAB, Shell, SQL, HTML, CSS

## Workflow

1. **Transform**: `python transformData.py`
2. **Rank**: `python ucheck/rank/weightrank.py testData/ 0.7`
3. **Results**: Check `testData/{project}_rank.json`

## Testing

```bash
python tests/test_languagecheck.py  # Language detection tests
python tests/test_parser.py         # Function extraction tests
```

## Ranking System

- **Utility files**: Functions in `util/utils/utility` folders automatically get score 1.0
- **Heuristic scoring**: Other functions scored on complexity, naming, structure
- **Threshold**: Functions ≥ threshold classified as utilities (`isUtil: true`)

## File Structure

```
utilityCheck/
├── ucheck/              # Core modules
│   ├── languagecheck/   # Language detection
│   ├── utility/         # Function extraction  
│   └── rank/            # Utility ranking
├── testData/            # Test data & output
├── data/                # Analysis output
└── tests/               # Test files
```

## License

MIT License
