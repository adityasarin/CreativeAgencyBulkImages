# BulkImageGen — AI Bulk Ad Image Generator

A local Python application for creative agencies to generate bulk Instagram ad images (9:16 Stories/Reels format) using AI-driven persona analysis, hook generation, and image synthesis.

---

## What It Does

BulkImageGen automates the end-to-end workflow from client brief to production-ready ad images:

1. **Client Brief Intake** — Chat interface collects product descriptions, target audience, brand context, and campaign goals
2. **Persona Generation** — GPT generates audience personas (e.g. diabetics, gym-goers, health-conscious millennials) from the brief
3. **Hook Generation** — AI generates emotional advertising hooks (fear, aspiration, FOMO, authority, etc.)
4. **Selection** — User picks which personas and hooks to use
5. **Combination Matrix** — System generates all persona × hook combinations (including 1- and 2-hook combos per persona)
6. **Prompt Generation** — Each combination is passed to the System Prompt, producing one consolidated, production-ready image generation prompt per combo
7. **Excel Export** — All prompts exported to Excel with a `selectFlag` column for user review
8. **Excel Review** — User downloads the Excel, sets `selectFlag` True/False per row, re-uploads
9. **Image Generation** — DALL·E 3 generates each selected prompt as a 1024×1792px image
10. **Output Saving** — Images saved to `BulkImageGen/{client}/{datetime}/images/`, labelled by persona and hook
11. **Report Generation** — `Report.xlsx` produced with per-image log (path, persona, hook, cost, status)
12. **Stop / Resume** — Generation can be halted mid-run; feedback box available at every step
13. **Cost Tracking** — Live cost display in the sidebar throughout the session

---

## Tech Stack

| Layer | Technology |
|---|---|
| UI | Streamlit (6-step wizard) |
| LLM — extraction | OpenAI `gpt-4o-mini` |
| LLM — creative generation & vision | OpenAI `gpt-4o` |
| Image generation | DALL·E 3 (OpenAI, ~$0.08/image) |
| RAG / vector store | ChromaDB (local) + sentence-transformers `all-MiniLM-L6-v2` |
| Campaign metadata | SQLite |
| Excel I/O | pandas + openpyxl |
| Platform | Windows 11, PowerShell / Python 3.10+ |

---

## Project Structure

```
AI_BulkImageGen/
├── app.py                    # Streamlit entry point
├── SystemPrompt.txt          # Master creative prompt template
├── AppPrompt.txt             # Project specification
├── requirements.txt
├── .env.example              # Environment variable template
├── .env                      # Your local secrets (not committed)
│
├── core/                     # Business logic
│   ├── llm_client.py         # OpenAI API wrapper
│   ├── session_manager.py    # Streamlit session state
│   ├── persona_generator.py
│   ├── hook_generator.py
│   ├── combination_engine.py
│   ├── prompt_builder.py
│   ├── brand_context_builder.py
│   ├── product_image_processor.py
│   ├── excel_manager.py
│   ├── report_generator.py
│   └── models.py
│
├── image_gen/                # Image generation
│   ├── base_provider.py
│   ├── gpt_image_provider.py # gpt-image-2 (OpenAI)
│   ├── provider_factory.py
│   ├── compositor.py         # Product compositing helpers
│   └── batch_runner.py       # Parallel generation worker
│
├── rag/                      # Retrieval-augmented generation
│   ├── chroma_store.py
│   ├── campaign_indexer.py
│   ├── context_retriever.py
│   └── embedder.py
│
├── db/                       # SQLite persistence
│   ├── db_manager.py
│   └── schema.sql
│
├── ui/                       # Streamlit step pages
│   ├── step_router.py
│   ├── step1_chat.py
│   ├── step2_personas.py
│   ├── step3_product_image.py
│   ├── step4_matrix.py
│   ├── step5_excel.py
│   └── step6_generation.py
│
└── utils/
    ├── file_utils.py
    ├── naming_utils.py
    └── cost_estimator.py
```

---

## Prerequisites

- Python 3.10 or higher
- An [OpenAI API key](https://platform.openai.com/) — powers both text generation (GPT) and image generation (DALL·E 3)

---

## Local Development Setup

### 1. Clone / navigate to the project

```powershell
cd C:\Users\91882\Documents\VibeCodedSideProjects\CreativeAgency\AI_BulkImageGen
```

### 2. Create and activate a virtual environment

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```powershell
pip install -r requirements.txt
```

### 4. Configure environment variables

```powershell
Copy-Item .env.example .env
```

Open `.env` and fill in your key:

```env
# OpenAI — single API key powers both text generation and image generation
OPENAI_API_KEY=sk-...
OPENAI_MINI_MODEL=gpt-4o-mini
OPENAI_MAIN_MODEL=gpt-4o

# Generation Settings
IMAGE_GEN_WORKERS=3                # parallel image generation threads
IMAGE_GEN_MAX_RETRIES=2

# Paths (defaults work out of the box)
OUTPUT_ROOT=BulkImageGen
CHROMA_DB_PATH=data/chroma_db
SQLITE_PATH=data/campaigns.sqlite
SYSTEM_PROMPT_PATH=SystemPrompt.txt
```

### 5. Run the app

```powershell
streamlit run app.py
```

The app opens at **http://localhost:8501** in your browser.

---

## Production Deployment

### Option A — Streamlit Community Cloud (recommended for quick hosting)

1. Push the repository to a GitHub repo (ensure `.env` is in `.gitignore`)
2. Go to [share.streamlit.io](https://share.streamlit.io) and connect the repo
3. Set all environment variables in the **Secrets** panel (equivalent to your `.env` file)
4. Deploy — Streamlit handles the Python environment automatically

> Note: ChromaDB persists to disk. On Streamlit Community Cloud the filesystem resets on each redeploy. Use an external vector store (Pinecone, Weaviate) if persistence across deploys matters.

### Option B — VPS / Cloud VM (Ubuntu 22.04 recommended)

#### 1. Provision a server

Any VPS with 2 vCPU / 4 GB RAM is sufficient (e.g. DigitalOcean Droplet, AWS EC2 `t3.medium`, Azure B2s).

#### 2. Install Python and dependencies

```bash
sudo apt update && sudo apt install -y python3.11 python3.11-venv python3-pip git
```

#### 3. Clone the repo and set up the environment

```bash
git clone <your-repo-url> /opt/bulkimagegen
cd /opt/bulkimagegen
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
nano .env   # fill in your API keys
```

#### 4. Run with a process manager (systemd)

Create `/etc/systemd/system/bulkimagegen.service`:

```ini
[Unit]
Description=BulkImageGen Streamlit App
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/opt/bulkimagegen
EnvironmentFile=/opt/bulkimagegen/.env
ExecStart=/opt/bulkimagegen/.venv/bin/streamlit run app.py --server.port 8501 --server.headless true
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable bulkimagegen
sudo systemctl start bulkimagegen
```

#### 5. Expose via Nginx reverse proxy (with HTTPS)

```bash
sudo apt install -y nginx certbot python3-certbot-nginx
```

`/etc/nginx/sites-available/bulkimagegen`:

```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_read_timeout 86400;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/bulkimagegen /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
sudo certbot --nginx -d yourdomain.com
```

App is now live at `https://yourdomain.com`.

### Option C — Docker

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.headless=true", "--server.address=0.0.0.0"]
```

```bash
docker build -t bulkimagegen .
docker run -d -p 8501:8501 --env-file .env bulkimagegen
```

---

## Cost Estimates

| Operation | Model / Provider | Cost |
|---|---|---|
| Brief extraction + persona generation | `gpt-4o-mini` | ~$0.001 per run |
| Hook + prompt generation (per combo) | `gpt-4o` | ~$0.005–0.015 |
| Image generation (per image) | DALL·E 3 (1024×1792) | ~$0.08 |

A typical campaign with 5 personas × 3 hooks = 15 combos costs approximately **$1–2** in API fees.

---

## Output

Generated images and reports are saved to:

```
BulkImageGen/
└── {Client_Project_Name}/
    └── {YYYY-MM-DD_HH-MM-SS}/
        ├── images/
        │   ├── persona1_hook_a_safe_001.png
        │   ├── persona1_hook_a_bold_002.png
        │   └── ...
        └── Report.xlsx
            ├── Log sheet    (one row per image: path, persona, hook, cost, status)
            └── Summary sheet (totals, cost breakdown, generation stats)
```

---

## Environment Variable Reference

| Variable | Required | Default | Description |
|---|---|---|---|
| `OPENAI_API_KEY` | Yes | — | OpenAI API key — used for text generation (GPT) and image generation (DALL·E 3) |
| `OPENAI_MINI_MODEL` | No | `gpt-4o-mini` | Model for extraction tasks |
| `OPENAI_MAIN_MODEL` | No | `gpt-4o` | Model for creative generation and vision tasks |
| `IMAGE_GEN_WORKERS` | No | `3` | Parallel generation threads |
| `IMAGE_GEN_MAX_RETRIES` | No | `2` | Retries per failed image |
| `OUTPUT_ROOT` | No | `BulkImageGen` | Root folder for generated output |
| `CHROMA_DB_PATH` | No | `data/chroma_db` | ChromaDB persistence path |
| `SQLITE_PATH` | No | `data/campaigns.sqlite` | SQLite database path |
| `SYSTEM_PROMPT_PATH` | No | `SystemPrompt.txt` | Path to the creative system prompt |
