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


4. **Run Django App**
   ```bash
   python run_django_frontend.py
   ``` 

5. **Tweak Settings**  
   - Adjust settings to your needs


6. **Run the Analyzer**  
   - In the **Classification**  Tab

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
**Saves** the categorized data to SQLite database  
**Displays** the data in an interactive dashboard using Django
---

## **Dashboard Overview**
![Dashboard Screenshot](https://raw.githubusercontent.com/raziolo/BrowserHistoryAnalyzer/refs/heads/master/screenshots/dashboard.png)
---

## **Detailed Analytics Overview**
![Detailed Analytics Screenshot](https://github.com/raziolo/BrowserHistoryAnalyzer/blob/master/screenshots/detailed_dashboard.png)
---

##  **Classification Overview**
![Classification Screenshot](https://raw.githubusercontent.com/raziolo/BrowserHistoryAnalyzer/refs/heads/master/screenshots/classification_start.png)
---

## **History Overview**
![History Screenshot](https://raw.githubusercontent.com/raziolo/BrowserHistoryAnalyzer/refs/heads/master/screenshots/history.png)
---

##  **Settings Overview**
![Settings Screenshot](https://raw.githubusercontent.com/raziolo/BrowserHistoryAnalyzer/refs/heads/master/screenshots/settings.png)
---

## ❓ **FAQs**  

### **Q: Does this work on Windows/Mac/Linux?**  
✅ Yes! Cross-platform support for all major OS.  

### **Q: Can I use Ollama instead of LM Studio?**  
✅ Absolutely! Just change `base_url` to `http://localhost:11434/v1`.  

### **Q: Where is my data stored?**  
📂 All files are kept locally:  
- Backups → `backupManager/history_backups/`  

---

## 📜 **License**  
MIT License – Use freely, but please attribute if sharing!  

---

**🔍 Happy browsing analysis!** 🚀  

*(Made with Python, SQLite, and local AI magic ✨)*

NOTE: This README has been partially made with AI since I have no creativity. 
