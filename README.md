# 🌐 **Local Browser History Classifier**  

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
   git clone https://github.com/yourusername/local-history-classifier.git
   cd local-history-classifier
   ```

2. **Install dependencies**  
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure LM Studio**  
   - Download & run [LM Studio](https://lmstudio.ai/)  
   - Load your preferred model (e.g., `granite-3.1-8b-instruct`)  
   - Ensure the local API is running at `http://localhost:1234/v1`  

4. **Run the app**  
   ```bash
   python main.py
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

## 🔧 **Customization**  

### **Using a Different Local LLM?**  
Modify `classifier/main.py`:  
```python
classifier = HistoryClassifier(
    model_name="your-model-name",  # e.g., "llama-3-8b"
    base_url="http://localhost:your-port/v1"  # LM Studio or Ollama
)
```

### **Changing Categories?**  
Edit `classification_categories` in `classifier/main.py`:  
```python
self.classification_categories = {
    "categories": ["Your", "Custom", "Categories", "Here"],
    "temperature": 0.3,
    "max_tokens": 50
}
```

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

### **Q: How do I analyze a specific date range?**  
Modify `DAYS_TO_ANALYZE` in `main.py`:  
```python
DAYS_TO_ANALYZE = 30  # Analyze last 30 days
```

---

## 📜 **License**  
MIT License – Use freely, but please attribute if sharing!  

---

**🔍 Happy browsing analysis!** 🚀  

*(Made with Python, SQLite, and local AI magic ✨)*

NOTE: This README has been partially made with AI since I have no creativity. 
