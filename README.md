# Compiler Phases Project

A full-stack compiler design project that demonstrates four compiler phases for C source code using a Flask backend and Streamlit frontend.

## Team Members

| Name | Register Number |
|---|---|
| Shreyans Modi | RA2311026010720 |
| Roshan | RA2311026010713 |
| Lokesh | RA2311026010715 |
| Uthkarsh | RA2311026010725 |

Subject: Compiler Design, SRM Institute of Science & Technology

## Project Overview

The application allows users to enter a C program, choose a compiler phase, and view the generated compiler output in a web interface. The frontend sends code to the Flask API, and the backend returns structured JSON results for display.

## Features

| Phase | Feature | Output |
|---|---|---|
| Phase 1 | Tokenization / Lexical Analysis | Token stream, token table, token summary, lexical errors |
| Phase 2 | Intermediate Code Generation | TAC, quadruples, triples, indirect triples |
| Phase 3 | Code Optimization | Optimized instruction list and removed instruction count |
| Phase 4 | Code Generation | Simplified x86-64 style assembly code |

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Streamlit |
| Backend | Flask, Flask-CORS |
| Data Display | Pandas |
| Language | Python |
| Input Language | C |
| Tests | Python unittest |

## Project Structure

```text
Compiler-Phases-Project/
├── backend/
│   └── app.py
├── frontend/
│   └── app.py
├── docs/
│   └── SUBMISSION.md
├── tests/
│   └── test_api.py
├── requirements.txt
├── .gitignore
└── README.md
```

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Checks backend status |
| POST | `/tokenize` | Generates lexical tokens |
| POST | `/icdg` | Generates intermediate code |
| POST | `/optimize` | Optimizes intermediate instructions |
| POST | `/codegen` | Generates assembly code |

## Setup

Install dependencies:

```bash
pip install -r requirements.txt
```

Start the backend:

```bash
python3 backend/app.py
```

The backend runs on:

```text
http://localhost:5001
```

Start the frontend in another terminal:

```bash
python3 -m streamlit run frontend/app.py
```

The frontend runs on:

```text
http://localhost:8501
```

## Test Cases

Run the automated API test cases:

```bash
python3 -m unittest discover -s tests
```

The tests verify:

- Health endpoint response
- Token generation for valid C code
- Lexical error detection for invalid characters
- Float literal recognition
- Intermediate code output
- Optimization output
- Assembly code generation
- Empty input validation

## Sample Input

```c
#include <stdio.h>
int main() {
    int i = 1;
    int total = 0;
    while(i <= 3) {
        total = total + i;
        i++;
    }
    printf("Total = %d\n", total);
    return 0;
}
```

## Submission Notes

The assignment submission document is available at:

```text
docs/SUBMISSION.md
```

Add project screenshots to a `screenshots/` folder before uploading the final GitHub link.

## License

This project is built for academic use as part of the Compiler Design course.
