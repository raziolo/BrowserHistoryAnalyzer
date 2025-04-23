# 🌐 **Local Browser History Analyzer**  

**🔍 Analyze, classify, and visualize your browsing history—100% locally!**  

This tool **backups**, **classifies**, and **visualizes** your Chrome/Firefox history using a **local LLM** (via LM Studio). Your data never leaves your machine!  

---

## 🚀 **Features**  

✅ **Local & Private** – No cloud services, your data stays on your computer  
✅ **Automatic Backups** – Creates JSON backups of your browsing history  
✅ **AI Classification** – Uses LM Studio (or any local LLM) to categorize sites  
✅ **Interactive Dashboard** – Beautiful visualizations with charts and stats  
✅ **Custom Models** – Easily swap in your preferred local LLM  

---

## 📦 **Installation**  

### **Requirements**  
- Python 3.10+  
- LM Studio (for local LLM inference)  
- Chrome/Firefox installed (to read history)  

### **Setup**  
1. **Clone the repo**  
   ```bash
   git clone https://github.com/raziolo/BrowserHistoryAnalyzer.git
   cd BrowserHistoryAnalyzer
   ```
   
    **OR** download the ZIP file and extract it.


2. **Create and Activate Virtual Environment**  
   ```bash
   # Create virtual environment
   python -m venv .venv
   
   # Activate it
   # On Windows:
   .\.venv\Scripts\activate
   # On Mac/Linux:
   source .venv/bin/activate
   ```

3. **Install dependencies**  
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure LM Studio**  
   - Download & run [LM Studio](https://lmstudio.ai/)  
   - Load your preferred model (e.g., `granite-3.1-8b-instruct`)  
   - Ensure the local API is running at `http://localhost:1234/v1`  

5. **Run the app**  
   ```bash
   python main.py # when done run `deactivate` or close the terminal
   ```
   

---

## 🛠 **How It Works**  

### **1. Backup Phase**  
📂 Creates a backup of your Chrome/Firefox history in `backupManager/history_backups/`  

### **2. Classification Phase**  
🤖 Uses your local LLM (via LM Studio) to categorize each URL into:  
- Social Media  
- News  
- Shopping  
- Education  
- Entertainment  
- Technology  
- Other  

### **3. Visualization Phase**  
📊 Generates an **interactive HTML dashboard** (`visualization/output/browsing_dashboard.html`) with:  
- Category distribution charts  
- Daily activity timeline  
- Recent browsing tables  

---
## ⚙️ Configuration
### All settings in `app_settings.py`:

#### Model Selection
```python
AI_MODEL_N = 2  # 0-9,  index N of model in AI_MODELS list
AI_MODEL_NAME = "granite-3.1-8b-instruct"  # Override directly

# ** Classification Parameters **
DAYS_TO_ANALYZE = 31  # Number of last days to analyze
```

### 🤠 Run Django App
```bash
python ./django_app/run_django_frontend.py
``` 

## 🛠 Customization Guide

### 1. Adding New Models
Edit `AI_MODELS` list:
```python
AI_MODELS = [
    {'name': 'your-model-identifier', 'thinking': True or False},
    ...
]
```

### 2. Category Fine-Tuning
Modify `CLASSIFICATION_PARAMETERS`:
```python
   "categories": [
       "Social Media",
       "News",
       # ...add/remove as needed
   ],
   "temperature": 0.3  # Higher = more creative classifications ( Max 1.0)
   "max_tokens": 2000  # Response length control, big number for thinking models
```

### 3. Backup Location
```python
BACKUP_DIR = Path("your/custom/path")  # Change backup storage
```


## 📊 **Django Dashboard Overview**
![Dashboard Screenshot](https://i.ibb.co/7NyQNc8p/image.png)
---

## ❓ **FAQs**  

### **Q: Does this work on Windows/Mac/Linux?**  
✅ Yes! Cross-platform support for all major OS.  

### **Q: Can I use Ollama instead of LM Studio?**  
✅ Absolutely! Just change `base_url` to `http://localhost:11434/v1`.  

### **Q: Where is my data stored?**  
📂 All files are kept locally:  
- Backups → `backupManager/history_backups/`  
- Classified data → `classified/classified_history.db`  
- Dashboard → `visualization/output/browsing_dashboard.html`

---

## 📜 **License**  
MIT License – Use freely, but please attribute if sharing!  

---

**🔍 Happy browsing analysis!** 🚀  

*(Made with Python, SQLite, and local AI magic ✨)*

NOTE: This README has been partially made with AI since I have no creativity. 
