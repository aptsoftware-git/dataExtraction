# Intelligence Data Extraction Engine

## 📌 Overview

This project is a hybrid Intelligence Data Extraction Engine that processes structured and narrative PDF reports and converts them into standardized Excel outputs.

The system combines:

- Deterministic rule-based extraction
- HTML → Markdown PDF parsing
- Local LLM-based semantic enrichment
- Automated Excel generation

---

## 🏗 Project Architecture

PDF → Text Extraction → Record Splitting → Rule-Based Mapping → LLM Enrichment → Excel Output

---

## 📂 Project Structure

```
project_Jetly/
│
├── backend/                 # Flask backend (core extraction engine)
│   ├── app/
│   │   ├── routes/          # API endpoints
│   │   ├── services/        # Extraction & mapping logic
│   │   ├── schemas/         # Output schema definitions
│   │   └── utils/           # Logger and utilities
│   └── run.py               # Flask entry point
│
├── frontend/                # React frontend
├── input files/             # Sample PDFs for testing
├── output/                  # Generated Excel outputs
├── venv/                    # Virtual environment (ignored)
└── requirements.txt         # Python dependencies
```

---

## 🚀 How To Run This Project

### 1️⃣ Clone the Repository

```
git clone https://github.com/aptsoftware-git/dataExtraction.git
cd project_Jetly
```

---

### 2️⃣ Create Virtual Environment

```
python -m venv venv
```

Activate:

**Windows:**
```
venv\Scripts\activate
```

**Mac/Linux:**
```
source venv/bin/activate
```

---

### 3️⃣ Install Dependencies

```
pip install -r requirements.txt
```

---

### 4️⃣ Run Backend (Flask)

From project root:

```
python -m backend.run
```

Server will start at:

```
http://127.0.0.1:5000
```

---

### 5️⃣ Run Frontend

Open a new terminal:

```
cd frontend
npm install
npm start
```

Frontend runs at:

```
http://localhost:3000
```

---

## 📊 Output

Generated Excel files are saved in:

```
output/
```

---

## 👩‍💻 Author

Sanjukta Mukherjee  
Intelligence Data Extraction System – Hybrid Rule-Based + LLM Architecture
