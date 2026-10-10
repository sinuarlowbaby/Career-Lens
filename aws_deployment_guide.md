# AWS Deployment Guide for CareerLens AI

This guide walks you through deploying **CareerLens AI** to Amazon Web Services (AWS). All Docker configurations, dependency manifests, database connections, and environment files have been audited and updated for production cloud deployment.

---

## 1. What Was Fixed & Audited for AWS

| Area | Previous State (Broken for AWS) | Current State (AWS Production-Ready) |
| :--- | :--- | :--- |
| **Dockerfile Host & CMD** | Used `--host [IP_ADDRESS]` (invalid syntax) and `--reload` (dev flag causing CPU loops). | Bound to `0.0.0.0:8000`, removed `--reload`, added `--proxy-headers` for AWS ALB / CloudFront SSL. |
| **Docker User Security** | Ran as `root` (violates AWS container security compliance). | Uses dedicated non-root `appuser (uid 1000)`. |
| **Health Checks** | No container healthcheck. | Added `HEALTHCHECK` pinging `/health` every 30s. |
| **requirements.txt** | Included `pywin32` (crashed Linux Docker builds) and `+xpu` wheels, while missing `chromadb`, `langchain-chroma`, `groq`, `python-docx`, `PyPDF2`. | Completely clean, pinned Linux/Windows compatible manifest with zero bloat. |
| **docker-compose.yaml** | Targeted `qdrant/qdrant` on port 6333 (unused by app). | Uses official `chromadb/chroma:latest` with persistent volume and internal networking. |
| **Vector DB Connection** | Hardcoded to `localhost:8001`, causing Docker containers to fail. | Dynamically reads `CHROMA_HOST` and `CHROMA_PORT` with resilient `LazyVectorStore` fallback. |
| **Database Pool** | Basic SQLite/Postgres without connection pooling. | Added `pool_pre_ping=True`, `pool_recycle=300`, and `postgres://` URL normalization for AWS RDS. |
| **Security & Secrets** | Hardcoded reversed Groq API key inside 7 files. | Removed all hardcoded keys; strictly reads from environment / AWS Secrets Manager. |

---

## 2. Choosing Your AWS Hosting Architecture

Choose the hosting option that best fits your budget and operational needs:

```mermaid
graph TD
    A[Choose AWS Deployment] --> B{Budget & Complexity?}
    B -->|Lowest Cost: $5 - $10/mo| C[Option 1: AWS Lightsail / EC2 with Docker Compose]
    B -->|Fully Managed Containers: $15 - $25/mo| D[Option 2: AWS App Runner + RDS]
    B -->|Enterprise Scalable: $40+/mo| E[Option 3: AWS ECS Fargate + RDS + EFS]
```

### Quick Recommendation:
- **For fastest setup and lowest cost (~$5 - $10/mo):** Use **Option 1 (AWS Lightsail / EC2)**. You run FastAPI, ChromaDB, and Caddy (automatic SSL) all in one instance using `docker-compose.yaml`.
- **For production scale with zero server management:** Use **Option 2 or 3 (ECS Fargate / App Runner + AWS RDS)**.

---

## 3. Option 1: AWS Lightsail or EC2 with Docker Compose (Recommended)

### Step 1: Launch an Instance
1. Go to **AWS Lightsail** (or EC2).
2. Choose **Linux/Unix** -> **Ubuntu 22.04 LTS** (or Amazon Linux 2023).
3. Instance Plan:
   - Minimum: **2 GB RAM, 1 vCPU** ($10/month on Lightsail, or `t3.small` / `t4g.small` on EC2).
4. Under Networking / Firewall, open:
   - `HTTP (80)`
   - `HTTPS (443)`
   - `SSH (22)`

### Step 2: Install Docker and Docker Compose on the Server
Connect to your instance via SSH and run:
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y curl git ufw

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose Plugin
sudo apt install -y docker-compose-plugin

# Exit and reconnect SSH so group permissions apply
exit
```

### Step 3: Clone Your Repository & Configure Environment
```bash
git clone https://github.com/sinuarlowbaby/Career-Lens.git
cd Career-Lens

# Create your production .env file
cp .env.example .env
nano .env
```
Fill in your production values:
```ini
OPENAI_API_KEY=sk-proj-your-openai-key
GROQ_API_KEY=gsk_your-groq-key
SECRET_KEY=generate_a_64_char_random_hex_string
DATABASE_URL=sqlite:///./career_lens.db   # or postgresql://user:pass@rds_host/careerlens
FRONTEND_URL=https://yourdomain.com
ALLOWED_ORIGINS=https://yourdomain.com
GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-google-client-secret
```

### Step 4: Add Caddy or Nginx for Automatic HTTPS (SSL)
To serve your application securely over `https://yourdomain.com`, add a reverse proxy. Create a `Caddyfile`:
```bash
cat << 'EOF' > Caddyfile
yourdomain.com {
    reverse_proxy career-lens:8000
}
EOF
```
Add Caddy to your `docker-compose.yaml` or run it standalone. Caddy automatically provisions and renews free SSL certificates from Let's Encrypt!

### Step 5: Start the Containers
```bash
docker compose up -d --build
```
Check status:
```bash
docker compose ps
docker compose logs -f
```

---

## 4. Option 2: AWS ECS Fargate + RDS PostgreSQL (Enterprise)

### Step 1: Create an ECR Repository & Push Container Image
```bash
# 1. Authenticate Docker with AWS ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <aws_account_id>.dkr.ecr.us-east-1.amazonaws.com

# 2. Create Repository
aws ecr create-repository --repository-name career-lens --region us-east-1

# 3. Build & Tag
docker build -t career-lens:latest .
docker tag career-lens:latest <aws_account_id>.dkr.ecr.us-east-1.amazonaws.com/career-lens:latest

# 4. Push
docker push <aws_account_id>.dkr.ecr.us-east-1.amazonaws.com/career-lens:latest
```

### Step 2: Set up AWS RDS PostgreSQL
1. Create a `PostgreSQL 15+` instance (e.g. `db.t4g.micro` for Free Tier).
2. Set master username (e.g. `careeradmin`) and password.
3. In RDS VPC Security Group, allow inbound port `5432` from your ECS Security Group.
4. Set `DATABASE_URL=postgresql://careeradmin:<password>@<rds-endpoint>:5432/careerlens`.

### Step 3: Create ECS Task Definition
Create a Task Definition in AWS ECS using Fargate (0.5 vCPU, 1 GB RAM):
- **Container 1 (`career-lens`)**:
  - Image: `<aws_account_id>.dkr.ecr.us-east-1.amazonaws.com/career-lens:latest`
  - Port: `8000`
  - Environment variables: `OPENAI_API_KEY`, `GROQ_API_KEY`, `SECRET_KEY`, `DATABASE_URL`, `CHROMA_HOST=localhost`, `CHROMA_PORT=8000`
- **Container 2 (`vector-db`)**:
  - Image: `chromadb/chroma:latest`
  - Port: `8000`
  - Environment variables: `IS_PERSISTENT=TRUE`, `ANONYMIZED_TELEMETRY=FALSE`

*(In ECS Fargate, containers in the same Task Definition communicate over `localhost`)*.

### Step 4: Attach Application Load Balancer (ALB)
1. Point your ALB target group to container port `8000` on path `/health`.
2. Configure AWS Certificate Manager (ACM) for HTTPS on port `443`.
3. In Google Cloud Console, update your OAuth redirect URI to:
   `https://yourdomain.com/auth/callback/google`

---

## 5. Google OAuth 2.0 Configuration for AWS

When deploying to AWS, Google requires an HTTPS redirect URI:
1. Open the [Google Cloud Console](https://console.cloud.google.com/apis/credentials).
2. Edit your **OAuth 2.0 Client ID**.
3. Under **Authorized JavaScript origins**, add:
   - `https://yourdomain.com` (or your CloudFront/ALB domain)
4. Under **Authorized redirect URIs**, add:
   - `https://yourdomain.com/auth/callback/google`
5. Note: Because our Dockerfile starts Uvicorn with `--proxy-headers` and `--forwarded-allow-ips *`, FastAPI automatically detects the `https` scheme terminated by AWS ALB / CloudFront!

---

## 6. Pre-Flight Checklist Before Launching

- [x] Dockerfile binds to `0.0.0.0:8000` without `--reload`
- [x] Docker healthcheck configured on `/health`
- [x] Linux-compatible `requirements.txt` with all application dependencies
- [x] ChromaDB container configured in `docker-compose.yaml`
- [x] Database connection pooling (`pool_pre_ping=True`) for RDS
- [x] Hardcoded API keys removed from source code
- [x] `.env.example` file provided for reference
- [x] Local test passed: `TestClient` confirmed `/health` returns `200 OK`
