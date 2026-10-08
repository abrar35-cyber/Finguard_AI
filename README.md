# 🛡️ FinGuard AI

**An AI-powered multi-agent assistant that finds, understands, reminds and helps you pay your bills — so you never miss a due date again.**

FinGuard AI scans bill-related emails and documents, extracts the key details using OCR and an LLM, tracks everything in a database, sends timely reminders, and supports payment handling — all through a simple web interface.

---

## ✨ Features

- 📧 **Bill Finder Agent** – detects bill-related emails/messages from your inbox data
- 🧠 **Bill Intelligence Agent** – extracts amount, due date, biller and category from bills
- 🔍 **OCR Service** – reads text from bill images and scanned documents
- ⚡ **Groq LLM Service** – fast AI reasoning for understanding and summarising bills
- ⏰ **Reminder Agent** – notifies you before due dates
- 💳 **Payment Agent & Service** – handles payment flow and status tracking
- 🗄️ **Database Layer** – stores bills, reminders and payment history
- 🖥️ **Web App** – clean interface to view and manage everything (`app.py`)

---

## 🏗️ Architecture

```
          ┌──────────────┐
          │   app.py UI  │
          └──────┬───────┘
                 │
     ┌───────────┼───────────────┐
     ▼           ▼               ▼
Bill Finder   Bill Intelligence  Reminder
  Agent          Agent            Agent
     │           │   │             │
     │      OCR Service  Groq      │
     │                  Service    │
     └───────────┬───────────────┬─┘
                 ▼               ▼
            database.py    Payment Agent
                                 │
                          Payment Service
```

---

## 📁 Project Structure

```
finguard-ai/
├── app.py                      # Main application entry point
├── bill_finder_agent.py        # Finds bills in emails/messages
├── bill_intelligence_agent.py  # Extracts & structures bill details
├── payment_agent.py            # Orchestrates payment actions
├── payment_service.py          # Payment processing logic
├── reminder_agent.py           # Due-date reminders
├── groq_service.py             # Groq LLM integration
├── ocr_service.py              # OCR for bill images/documents
├── database.py                 # Data storage layer
├── demo_emails.json            # Sample data for demo/testing
├── requirements.txt            # Python dependencies
└── packages.txt                # System-level dependencies (e.g. OCR engine)
```

---

## 🛠️ Tech Stack

- **Language:** Python
- **LLM:** Groq API
- **OCR:** Tesseract-based OCR
- **Interface:** Streamlit
- **Storage:** Database layer via `database.py`

> Update this list if any of the above differs from your actual implementation.

---

## 🚀 Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/abrar35-cyber/<repo-name>.git
cd <repo-name>
```

### 2. Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

System packages listed in `packages.txt` (such as the OCR engine) must also be installed, e.g. on Ubuntu/Debian:

```bash
sudo xargs -a packages.txt apt-get install -y
```

### 4. Set up environment variables

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_api_key_here
```

### 5. Run the app

```bash
streamlit run app.py
```

---

## 🎬 Demo

The repo includes `demo_emails.json` with sample bill emails, so you can try the full flow without connecting a real inbox.

*(Add screenshots or a short demo GIF here.)*

---

## 🔄 How It Works

1. **Discover** – the Bill Finder Agent scans emails/messages for bills.
2. **Understand** – OCR and the Groq LLM extract amount, due date and biller.
3. **Store** – structured bill data is saved to the database.
4. **Remind** – the Reminder Agent alerts you before the due date.
5. **Pay** – the Payment Agent guides and records the payment.

---

## 🔐 Security Notes

- Never commit your `.env` file or API keys.
- Use demo data when testing; avoid uploading real personal financial documents to public deployments.

---

## 🗺️ Roadmap

- [ ] Real email integration (Gmail API)
- [ ] Multi-currency and multi-language bill support
- [ ] WhatsApp / SMS reminder channel
- [ ] Spending analytics dashboard
- [ ] Unit tests and CI

---

## 🤝 Contributing

Contributions, issues and feature requests are welcome. Feel free to open an issue or submit a pull request.

---

## 👤 Author

**Abrar Ahmed**
- GitHub: [@abrar35-cyber](https://github.com/abrar35-cyber)
- LinkedIn: [abrarahmedsoomro](https://www.linkedin.com/in/abrarahmedsoomro/)
- Email: abrarsoomro35@gmail.com

---

⭐ If you found this project useful, consider giving it a star!
