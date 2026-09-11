# JobFinder AI 🔍

**JobFinder AI** is an intelligent, hackathon-grade career assistant powered by the **Google Gemini API**. It bridges the gap between candidates and recruiters by deeply parsing resumes, analyzing job descriptions, computing transparent compatibility scores, and generating ethical, impact-oriented CV improvements.

---

## 🌟 Key Features

1. **Intelligent CV Parsing**: Extracts structured entities (technical & soft skills, career chronology, degrees, certifications, and portfolio projects) from PDF, DOCX, and TXT files.
2. **Transparent Multi-Factor Job Matching**:
   - Computes an **AI Compatibility Score: XX%** backed by an explicit arithmetic breakdown (45% skills alignment, 25% experience depth, 15% education, 15% project relevance).
   - Identifies matching skills, missing keywords, and adjacent competencies without making inflated hiring claims.
3. **Ethical Resume Tailoring (Google XYZ Formula)**:
   - Provides concrete bullet point enhancements (*Accomplished [X], measured by [Y], by doing [Z]*).
   - Strictly forbids the fabrication of degrees, employers, or nonexistent technical skills.
4. **Curated Job Exploration**:
   - Filter jobs by keywords, location, or work model (Remote, Hybrid, Full-time).
   - Auto-computes candidate-specific compatibility estimations for every open role.
5. **Report Export**: Download complete, formatted Markdown reports of your match analysis with one click.
6. **Graceful Fallbacks**: Fully operational in offline / demo mode with zero fatal crashes if API keys or videos are missing.

---

## 🛠️ Technology Stack

- **AI Model**: Google Gemini 3.8 Flash (`@google/genai` / Python `google-genai`)
- **Python / Streamlit Framework**:
  - Python 3.10+
  - Streamlit (multi-page state management)
  - Pydantic v2 (structured schema validation)
  - `pypdf` & `python-docx` (safe document parsing)
- **Web App / Live Preview**:
  - React 19 + TypeScript + Tailwind CSS
  - Node.js / Express proxy layer (zero frontend API key exposure)
- **Quality Assurance**:
  - Python `unittest` suite covering parsers, match algorithms, and schemas.

---

## 🚀 Getting Started

### 1. Prerequisites
- Python 3.10 or higher
- Node.js 18+ (for web preview)
- A Google Gemini API key from [Google AI Studio](https://aistudio.google.com/)

### 2. Environment Configuration
Copy the example environment file:
```bash
cp .env.example .env
```
Open `.env` and set your API key:
```env
GEMINI_API_KEY=your_actual_gemini_api_key_here
```

---

## 🏃‍♂️ Running the Application

### Option A: Run Streamlit (Native Python App)
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Launch Streamlit
streamlit run app.py
```
The Streamlit app will open in your browser at `http://localhost:8501`.

### Option B: Run Fullstack React + Express Server
```bash
# 1. Install node dependencies
npm install

# 2. Start server
npm run dev
```
The application will be accessible at `http://localhost:3000`.

---

## 🧪 Running Unit Tests

Run the complete test suite:
```bash
python3 -m unittest discover tests
```
All 14 tests verify:
- Safe file parsing for PDF/DOCX/TXT and empty-file guardrails.
- Mathematical boundaries of the matching algorithm (0-100%).
- Keyword categorization into matching, missing, and partial skills.
- Fallback schema conformity and markdown report export.

---

## ☁️ Streamlit Cloud Deployment Guide

1. Push this repository to GitHub.
2. Log in to [Streamlit Community Cloud](https://share.streamlit.io/).
3. Click **"New app"** and select your repository and branch (`main`).
4. Set **Main file path** to `app.py`.
5. Under **Advanced settings > Secrets**, add your Gemini API key:
   ```toml
   GEMINI_API_KEY = "your_actual_gemini_api_key_here"
   ```
6. Click **Deploy!**

---

## 🔒 Security & Privacy Architecture

- **Server-Side API Proxying**: API keys are never bundled into the browser JavaScript client or sent in client requests.
- **In-Memory Document Handling**: CV documents and resume texts are analyzed in memory and never written to permanent disk or unencrypted databases.
- **Strict `.gitignore`**: Environment files (`.env`), API keys, build artifacts, and test logs are ignored by Git.

---

## 📜 License
Apache-2.0. Built for student hackathon demonstration.
