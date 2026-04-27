import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# override=True : le .env prend toujours le dessus sur les variables déjà
# présentes dans l'environnement shell (évite les surprises lors des tests).
load_dotenv(BASE_DIR / ".env", override=True)


def _get_bool(name: str, default: bool = False) -> bool:
    """Convertit une variable d'env en booléen de façon robuste."""
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in ("true", "1", "yes", "y", "on")


DATABASE_PATH = str(BASE_DIR / "nudge.db")

APP_NAME    = "Nudge"
APP_VERSION = "0.1.0"

# ── Mode envoi ────────────────────────────────────────────────────────────────
# NUDGE_SIMULATE=true  → simulation console uniquement (aucun mail réel)
# NUDGE_SIMULATE=false → envoi SMTP réel (nécessite les paramètres SMTP)
# Absent                → simulation activée par sécurité
MAIL_SIMULATE = _get_bool("NUDGE_SIMULATE", default=True)

# ── Paramètres SMTP ───────────────────────────────────────────────────────────
# Définir dans le fichier .env à la racine :
#   NUDGE_SMTP_USER=votre.adresse@gmail.com
#   NUDGE_SMTP_PASS=xxxx xxxx xxxx xxxx   <- mot de passe d'application Gmail
#   NUDGE_SMTP_HOST=smtp.gmail.com        <- optionnel, valeur par défaut ci-dessous
#   NUDGE_SMTP_PORT=587                   <- optionnel
SMTP_HOST = os.getenv("NUDGE_SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("NUDGE_SMTP_PORT", "587"))
SMTP_USER = os.getenv("NUDGE_SMTP_USER", "")
SMTP_PASS = os.getenv("NUDGE_SMTP_PASS", "")

print(f"[NUDGE] Mode simulation : {'ON' if MAIL_SIMULATE else 'OFF'}")
