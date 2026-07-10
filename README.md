# Cloud-Native Notes Management System

A simple notes app used as a hands-on exercise in multi-container architecture and cloud deployment — built with **Flask**, **MySQL**, and **Nginx**, containerized with **Docker Compose**, and provisioned on **AWS EC2** using **Terraform**.

The app itself is intentionally simple (add/delete text notes). The real focus of this project is the infrastructure around it: reverse proxying, persistent storage, container orchestration, and Infrastructure as Code.

---

## Architecture

```
                    ┌─────────────┐
  Browser  ───────► │    Nginx    │  (port 80 — reverse proxy)
                    └──────┬──────┘
                           │ proxy_pass
                           ▼
                    ┌─────────────┐
                    │  Flask App  │  (Gunicorn, port 5000)
                    └──────┬──────┘
                           │
                           ▼
                    ┌─────────────┐
                    │    MySQL    │  (persistent volume)
                    └─────────────┘

All three run as separate containers on one Docker network,
orchestrated by Docker Compose, deployed on an AWS EC2 instance
provisioned via Terraform.
```

- **Nginx** sits in front as a reverse proxy, forwarding all traffic on port 80 to the Flask app
- **Flask** (served via Gunicorn) handles the note-taking logic and talks to MySQL
- **MySQL** stores notes in a persistent Docker volume, so data survives container restarts
- A Compose **healthcheck** on the MySQL container ensures Flask doesn't start trying to query the database before it's actually ready

---

## Project structure

```
flask-notes-app/
├── flask-notes-app/
│   ├── app/
│   │   ├── app.py               # Flask routes: /, /add, /delete/<id>
│   │   ├── requirements.txt
│   │   └── templates/
│   │       └── index.html       # Single-page notes UI
│   ├── Dockerfile                # Flask app image (Gunicorn entrypoint)
│   ├── docker-compose.yml        # 3-service stack: flask_app, nginx, db
│   └── nginx/
│       ├── Dockerfile
│       └── default.conf          # Reverse proxy config
└── terraform/
    ├── main.tf                   # EC2 instance, security group, key pair
    ├── variables.tf
    ├── outputs.tf
    └── provider.tf
```

---

## The app itself

A minimal Flask app with three routes:

| Route | Method | Description |
|---|---|---|
| `/` | GET | Lists all notes from MySQL |
| `/add` | POST | Inserts a new note |
| `/delete/<id>` | GET | Deletes a note by ID |

On startup, the app creates the `notes` table if it doesn't already exist — no separate migration step needed for this simple schema.

---

## Running it locally

You'll need Docker and Docker Compose installed.

1. **Create a `.env` file** in `flask-notes-app/` (same folder as `docker-compose.yml`) with the MySQL connection details the Flask app expects:

   ```env
   MYSQL_HOST=db
   MYSQL_USER=root
   MYSQL_PASSWORD=root
   MYSQL_DB=notes_db
   ```

   > These must match the `MYSQL_ROOT_PASSWORD` / `MYSQL_DATABASE` values set for the `db` service in `docker-compose.yml`.

2. **Build and start the stack**:

   ```bash
   cd flask-notes-app
   docker compose up --build
   ```

3. **Open the app**: visit `http://localhost` (port 80, via Nginx) — not port 5000 directly, since Nginx is the entry point.

4. **Stop everything**:

   ```bash
   docker compose down
   ```
   Add `-v` if you also want to wipe the persisted MySQL volume (`docker compose down -v`).

---

## Cloud deployment (AWS + Terraform)

The `terraform/` folder provisions everything needed to run this on AWS:

- An **EC2 instance** (Amazon Linux 2, `t3.micro` by default)
- A **security group** allowing SSH (22) and HTTP (80)
- A **key pair** for SSH access
- A `user_data` bootstrap script that installs **Docker** and **Docker Compose** automatically on first boot

### Deploy steps

1. **Generate an SSH key pair** (if you don't already have one) and place the public key where `main.tf` expects it — update the `public_key` path in `main.tf` to point to your own key file rather than a hardcoded local path.

2. **Provision the infrastructure**:

   ```bash
   cd terraform
   terraform init
   terraform apply
   ```

   Terraform will output the instance's public IP (`instance_public_ip`).

3. **Copy the app onto the instance** and start it:

   ```bash
   scp -i notes-app-key -r ../flask-notes-app ec2-user@<PUBLIC_IP>:~/
   ssh -i notes-app-key ec2-user@<PUBLIC_IP>
   cd flask-notes-app
   # create the .env file here too, same as the local setup
   docker-compose up --build -d
   ```

4. **Visit the app**: `http://<PUBLIC_IP>` in your browser.

> **Security note**: the default security group opens SSH to `0.0.0.0/0` (anywhere on the internet). For anything beyond a quick personal test, restrict the SSH ingress rule to your own IP before applying.

### Tearing it down

```bash
cd terraform
terraform destroy
```
This removes the EC2 instance, security group, and key pair — stopping any associated AWS costs.

---

## Tech stack

| Layer | Tools |
|---|---|
| Backend | Flask, Gunicorn, Flask-MySQLdb, PyMySQL |
| Database | MySQL 8.0 |
| Reverse Proxy | Nginx |
| Containerization | Docker, Docker Compose |
| Infrastructure as Code | Terraform (AWS EC2, security groups) |

---

## Notes / possible improvements

- No CI/CD pipeline yet (unlike the [Healthcare Fraud API](https://github.com/ananyadwivedi1010/Healthcare-Fraud-api) project) — deployment is currently manual via `scp` + SSH
- No automated tests
- The `notes` table has no `user` concept — all notes are global/shared, there's no auth
- Passwords are set via plain environment variables for this learning project; a real deployment would use a secrets manager (e.g. AWS Secrets Manager) instead of committing them to `.env` files on the server
