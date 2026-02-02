# Deploy Project to Render
If Gusto mo i deploy to to online, sundin mo to, but ipasok mo muna sa git before starting
Follow these steps to deploy the "Vibe" project on Render.com.

## Render Configuration

1.  **Create a New Web Service**: Choose your GitHub repository.
2.  **Environment**: Python
3.  **Build Command**: `./build.sh`
4.  **Start Command**: `x``

## Environment Variables

Add the following environment variables in the Render dashboard:

| Key | Value | Note |
| :--- | :--- | :--- |
| `DJANGO_SECRET_KEY` | `your-secure-secret-key-here` | Generate a random 50-character string |
| `PYTHON_VERSION` | `3.11.0` | Or your preferred version (3.8+) |

## Persistent Data Warning
> [!CAUTION]
> This deployment uses **SQLite**. Render's disk is ephemeral by default, meaning any data added (members, attendance, etc.) will be **LOST** whenever the service restarts or redeploys. 
> 
> For a production environment, you should use a managed database like Render PostgreSQL and update `DATABASES` in `vibe/settings.py`.

## Static Files
Static files are served using **WhiteNoise**. This is already configured in `settings.py` and `requirements.txt`.
