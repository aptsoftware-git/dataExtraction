# 🛰 Intelligence Data Extraction Engine

## 📌 Overview

This project is a hybrid Intelligence Data Extraction System that processes structured and narrative PDF reports and converts them into standardized Excel outputs.

It combines rule-based extraction with contextual enrichment to ensure consistent, accurate, and structured intelligence data mapping.

---

## 🧠 Key Features

- Handles structured and narrative PDFs  
- Extracts tactical intelligence fields  
- Automatically detects:
  - Date  
  - Source (Agency, AOR, Unit)  
  - Location (State, District, Area)  
  - Group/Faction (GP)  
  - Event Type  
  - Cadre Strength  
  - Leader Names  
  - Weapons & Ammunition  
- Generates standardized Excel output  
- Works across multiple report formats  

---

## 🏗 Project Structure

```
project_Jetly/
│
├── backend/        # Flask backend (extraction engine)
├── frontend/       # React frontend
├── input files/    # Sample PDFs
├── output/         # Generated Excel files
└── requirements.txt
```

---

## 🚀 How To Run

### 1️⃣ Clone Repository

```bash
git clone https://github.com/aptsoftware-git/dataExtraction.git
cd backend
```

### 2️⃣ Create Virtual Environment

```bash
python -m venv venv
```

Activate:

**Windows**
```bash
venv\Scripts\activate
```

**Mac/Linux**
```bash
source venv/bin/activate
```

### 3️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

### 4️⃣ Run Backend

```bash
python -m backend.run
```

Backend runs at:

```
http://127.0.0.1:5000
```

### 5️⃣ Run Frontend

```bash
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
/output
```

---

## 👩‍💻 Author

Sanjukta Mukherjee  
Intelligence Data Extraction System  
Hybrid Rule-Based Architecture
