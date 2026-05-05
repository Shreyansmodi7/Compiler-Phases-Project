# Compiler Phases Project - Submission Document

## 1. GitHub Link

Repository: https://github.com/UT-23/Compiler-Phases-Project

## 2. Project Explanation

This project is a web-based compiler phase visualizer for C programs. It uses a Flask backend to process source code and a Streamlit frontend to present each compiler phase in a simple interactive interface.

The user enters or selects a C program in the frontend, chooses one compiler phase, and clicks Run Phase. The frontend sends the source code to the backend API. The backend analyzes the code and returns structured JSON output, which the frontend displays as token tables, three-address code, optimization output, or assembly code.

### Modules

| Module | File | Purpose |
|---|---|---|
| Backend API | `backend/app.py` | Implements compiler phase endpoints using Flask |
| Frontend UI | `frontend/app.py` | Streamlit interface for entering code and viewing results |
| Tests | `tests/test_api.py` | Unit tests for API endpoints and phase outputs |
| Dependencies | `requirements.txt` | Python packages required to run the project |

### Compiler Phases Implemented

| Phase | Endpoint | Description |
|---|---|---|
| Tokenization | `POST /tokenize` | Splits C source code into keywords, identifiers, numbers, strings, operators, and delimiters |
| Intermediate Code Generation | `POST /icdg` | Generates TAC, quadruples, triples, and indirect triples |
| Code Optimization | `POST /optimize` | Removes adjacent duplicate intermediate instructions |
| Code Generation | `POST /codegen` | Produces simplified x86-64 style assembly output |

## 3. Screenshots To Attach

Create a `screenshots/` folder in the repository and add these images before final submission:

| Screenshot | Suggested file name |
|---|---|
| Home screen with sample C input | `screenshots/01-home-input.png` |
| Tokenization output with token stream and token table | `screenshots/02-tokenization.png` |
| Intermediate code output showing TAC, quadruple, triple, indirect triple | `screenshots/03-icg.png` |
| Code optimization output | `screenshots/04-optimization.png` |
| Assembly code generation output | `screenshots/05-code-generation.png` |
| Test cases running successfully in terminal | `screenshots/06-test-cases.png` |
| Important code section from `backend/app.py` | `screenshots/07-backend-code.png` |
| Important code section from `frontend/app.py` | `screenshots/08-frontend-code.png` |

## 4. Important Code Files

The main code for evaluation is:

- `backend/app.py`
- `frontend/app.py`
- `tests/test_api.py`

Backend endpoints:

```python
@app.route('/tokenize', methods=['POST'])
@app.route('/icdg', methods=['POST'])
@app.route('/optimize', methods=['POST'])
@app.route('/codegen', methods=['POST'])
@app.route('/health', methods=['GET'])
```

Frontend communicates with the backend using:

```python
BACKEND_URL = "http://127.0.0.1:5001"
```

## 5. Test Cases

Run all tests from the project root:

```bash
python3 -m unittest discover -s tests
```

### Test Case Summary

| Test Case | Expected Result |
|---|---|
| Health endpoint | Returns status `ok` |
| Valid tokenization | Returns tokens and summary counts |
| Invalid character tokenization | Reports lexical error for invalid character |
| Float literal tokenization | Recognizes decimal values as `FLOAT` |
| Intermediate code generation | Returns TAC, quadruples, triples, and indirect triples |
| Optimization | Removes adjacent duplicate instructions |
| Code generation | Returns assembly containing prologue, `CALL printf`, and `RET` |
| Empty source | Returns HTTP 400 with `No code` |

## 6. How To Run

Install requirements:

```bash
pip install -r requirements.txt
```

Start backend:

```bash
python3 backend/app.py
```

Start frontend in another terminal:

```bash
python3 -m streamlit run frontend/app.py
```

Open:

```text
http://localhost:8501
```
