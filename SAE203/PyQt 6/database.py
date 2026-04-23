import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.expanduser("~"), "nudge.db")


def _connexion() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def initialiser_base():
    conn = _connexion()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS Utilisateur (
            id_utilisateur  INTEGER PRIMARY KEY AUTOINCREMENT,
            nom_utilisateur TEXT    NOT NULL,
            prenom          TEXT,
            email           TEXT,
            role            TEXT
        );
        CREATE TABLE IF NOT EXISTS Projet (
            id_projet       INTEGER PRIMARY KEY AUTOINCREMENT,
            nom_projet      TEXT    NOT NULL,
            description     TEXT,
            date_fin        TEXT,
            id_utilisateur  INTEGER,
            FOREIGN KEY (id_utilisateur) REFERENCES Utilisateur(id_utilisateur)
        );
        CREATE TABLE IF NOT EXISTS Tache (
            id_tache        INTEGER PRIMARY KEY AUTOINCREMENT,
            titre           TEXT    NOT NULL,
            description     TEXT,
            date_creation   TEXT,
            date_echeance   TEXT,
            priorite        TEXT    CHECK(priorite IN ('Basse','Moyenne','Haute','Critique')),
            statut          TEXT,
            id_projet       INTEGER NOT NULL,
            id_utilisateur  INTEGER,
            FOREIGN KEY (id_projet)      REFERENCES Projet(id_projet),
            FOREIGN KEY (id_utilisateur) REFERENCES Utilisateur(id_utilisateur)
        );
        CREATE TABLE IF NOT EXISTS Relance (
            id_relance      INTEGER PRIMARY KEY AUTOINCREMENT,
            date_envoi      TEXT,
            type_relance    TEXT,
            contenu         TEXT,
            id_tache        INTEGER NOT NULL,
            id_utilisateur  INTEGER,
            FOREIGN KEY (id_tache)       REFERENCES Tache(id_tache),
            FOREIGN KEY (id_utilisateur) REFERENCES Utilisateur(id_utilisateur)
        );
    """)
    conn.commit()
    conn.close()


def charger_responsables() -> list:
    conn = _connexion()
    rows = conn.execute("SELECT * FROM Utilisateur ORDER BY nom_utilisateur").fetchall()
    conn.close()
    return [
        {
            "id":    row["id_utilisateur"],
            "nom":   f"{row['prenom'] or ''} {row['nom_utilisateur']}".strip(),
            "email": row["email"] or "",
            "role":  row["role"]  or "Autre",
        }
        for row in rows
    ]


def ajouter_responsable(nom: str, email: str, role: str) -> int:
    parts  = nom.strip().split()
    prenom = " ".join(parts[:-1]) if len(parts) > 1 else ""
    nom_db = parts[-1] if parts else nom
    conn = _connexion()
    cursor = conn.execute(
        "INSERT INTO Utilisateur (nom_utilisateur, prenom, email, role) VALUES (?, ?, ?, ?)",
        (nom_db, prenom, email, role)
    )
    new_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return new_id


def charger_projets() -> list:
    conn = _connexion()
    rows = conn.execute("SELECT * FROM Projet ORDER BY id_projet").fetchall()
    conn.close()
    return [
        {
            "id":          row["id_projet"],
            "nom":         row["nom_projet"],
            "description": row["description"] or "",
            "date_fin":    row["date_fin"]    or "",
        }
        for row in rows
    ]


def ajouter_projet(nom: str, description: str, date_fin: str) -> int:
    conn = _connexion()
    cursor = conn.execute(
        "INSERT INTO Projet (nom_projet, description, date_fin) VALUES (?, ?, ?)",
        (nom, description, date_fin)
    )
    new_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return new_id


def modifier_projet(projet_id: int, nom: str, description: str, date_fin: str):
    conn = _connexion()
    conn.execute(
        "UPDATE Projet SET nom_projet=?, description=?, date_fin=? WHERE id_projet=?",
        (nom, description, date_fin, projet_id)
    )
    conn.commit()
    conn.close()


def supprimer_projet(projet_id: int):
    conn = _connexion()
    conn.execute("""
        DELETE FROM Relance WHERE id_tache IN
        (SELECT id_tache FROM Tache WHERE id_projet = ?)
    """, (projet_id,))
    conn.execute("DELETE FROM Tache WHERE id_projet = ?", (projet_id,))
    conn.execute("DELETE FROM Projet WHERE id_projet = ?", (projet_id,))
    conn.commit()
    conn.close()


def charger_taches(projet_id: int = None) -> list:
    conn = _connexion()
    if projet_id:
        rows = conn.execute(
            "SELECT * FROM Tache WHERE id_projet = ? ORDER BY id_tache", (projet_id,)
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM Tache ORDER BY id_tache").fetchall()
    conn.close()

    taches = []
    for row in rows:
        resp_nom = None
        if row["id_utilisateur"]:
            conn2 = _connexion()
            u = conn2.execute(
                "SELECT nom_utilisateur, prenom FROM Utilisateur WHERE id_utilisateur = ?",
                (row["id_utilisateur"],)
            ).fetchone()
            conn2.close()
            if u:
                resp_nom = f"{u['prenom'] or ''} {u['nom_utilisateur']}".strip()
        taches.append({
            "id":             row["id_tache"],
            "titre":          row["titre"],
            "description":    row["description"] or "",
            "echeance":       row["date_echeance"] or "",
            "priorite":       row["priorite"] or "Moyenne",
            "statut":         row["statut"] or "À faire",
            "project_id":     row["id_projet"],
            "responsable_id": row["id_utilisateur"],
            "responsable":    resp_nom,
        })
    return taches


def ajouter_tache(titre: str, description: str, echeance: str,
                  priorite: str, statut: str,
                  projet_id: int, responsable_id: int = None) -> int:
    conn = _connexion()
    cursor = conn.execute(
        """INSERT INTO Tache
           (titre, description, date_creation, date_echeance, priorite, statut, id_projet, id_utilisateur)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (titre, description, datetime.now().isoformat(),
         echeance, priorite, statut, projet_id, responsable_id)
    )
    new_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return new_id


def modifier_tache(tache_id: int, titre: str, description: str, echeance: str,
                   priorite: str, statut: str, responsable_id: int = None):
    conn = _connexion()
    conn.execute(
        """UPDATE Tache
           SET titre=?, description=?, date_echeance=?, priorite=?, statut=?, id_utilisateur=?
           WHERE id_tache=?""",
        (titre, description, echeance, priorite, statut, responsable_id, tache_id)
    )
    conn.commit()
    conn.close()


def mettre_a_jour_statut(tache_id: int, statut: str):
    conn = _connexion()
    conn.execute("UPDATE Tache SET statut=? WHERE id_tache=?", (statut, tache_id))
    conn.commit()
    conn.close()


def mettre_a_jour_responsable(tache_id: int, responsable_id: int = None):
    conn = _connexion()
    conn.execute(
        "UPDATE Tache SET id_utilisateur=? WHERE id_tache=?", (responsable_id, tache_id)
    )
    conn.commit()
    conn.close()


def supprimer_tache(tache_id: int):
    conn = _connexion()
    conn.execute("DELETE FROM Relance WHERE id_tache = ?", (tache_id,))
    conn.execute("DELETE FROM Tache WHERE id_tache = ?", (tache_id,))
    conn.commit()
    conn.close()


def charger_relances() -> list:
    conn = _connexion()
    rows = conn.execute(
        "SELECT * FROM Relance ORDER BY date_envoi DESC LIMIT 50"
    ).fetchall()
    conn.close()
    relances = []
    for row in rows:
        conn2 = _connexion()
        tache = conn2.execute(
            "SELECT titre FROM Tache WHERE id_tache = ?", (row["id_tache"],)
        ).fetchone()
        conn2.close()
        email_brut = row["contenu"] or ""
        masked = email_brut[:3] + "***" + email_brut[email_brut.find("@"):] if "@" in email_brut else email_brut
        relances.append({
            "email":     masked,
            "taskTitle": tache["titre"] if tache else "Tâche inconnue",
            "date":      (row["date_envoi"] or "")[:10],
            "mode":      row["type_relance"] or "Simulation",
        })
    return relances


def ajouter_relance(tache_id: int, email_destinataire: str, mode: str):
    conn = _connexion()
    conn.execute(
        "INSERT INTO Relance (date_envoi, type_relance, contenu, id_tache) VALUES (?, ?, ?, ?)",
        (datetime.now().isoformat(), mode, email_destinataire, tache_id)
    )
    conn.commit()
    conn.close()