import pandas as pd
import re

# ── CHARGEMENT ──────────────────────────────────────────
df = pd.read_csv("offres_data_merged.csv", encoding="utf-8-sig")

# ── NETTOYAGE VILLE ─────────────────────────────────────
df["Ville_Clean"] = df["Ville"].str.replace(
    r"^\d{2,3}\s*-\s*", "", regex=True
).str.strip().str.title()

# ── EXTRACTION DÉPARTEMENT ──────────────────────────────
df["Code_Dept"] = df["Ville"].str.extract(r"^(\d{2,3})\s*-")
df["Code_Dept"] = df["Code_Dept"].fillna("00")

# ── NETTOYAGE TYPE CONTRAT ──────────────────────────────
def clean_contrat(val):
    if pd.isna(val):
        return "Non précisé"
    val = str(val)
    if "CDI" in val:
        return "CDI"
    elif "CDD" in val:
        return "CDD"
    elif "Intérim" in val or "Interim" in val:
        return "Intérim"
    elif "Alternance" in val or "Apprentissage" in val:
        return "Alternance"
    elif "libérale" in val.lower():
        return "Freelance"
    else:
        return "Autre"

df["Type_Contrat_Clean"] = df["Type_Contrat"].apply(clean_contrat)

# ── PARSING SALAIRE ─────────────────────────────────────
def parse_salaire(val):
    if pd.isna(val) or val == "":
        return None, None, None

    val = str(val)
    montants = re.findall(r"(\d+(?:\.\d+)?)", val)
    if len(montants) < 2:
        return None, None, None

    min_sal = float(montants[0])
    max_sal = float(montants[1])

    if "Mensuel" in val:
        periodicite = "Mensuel"
        min_annuel = min_sal * 12
        max_annuel = max_sal * 12
    elif "Annuel" in val:
        periodicite = "Annuel"
        min_annuel = min_sal
        max_annuel = max_sal
    else:
        periodicite = "Inconnu"
        min_annuel = min_sal
        max_annuel = max_sal

    salaire_moyen = (min_annuel + max_annuel) / 2
    return min_annuel, max_annuel, salaire_moyen

df[["Salaire_Min", "Salaire_Max", "Salaire_Moyen"]] = df["Salaire_Libelle"].apply(
    lambda x: pd.Series(parse_salaire(x))
)

# ── NETTOYAGE MOT CLÉ ───────────────────────────────────
def clean_mot_cle(val):
    if pd.isna(val):
        return "Autre"
    val = str(val)
    if "Data Analyst" in val:
        return "Data Analyst"
    elif "Analyste données" in val or "Analyste BI" in val:
        return "Data Analyst"
    elif "Business Intelligence" in val:
        return "Business Intelligence"
    elif "Power BI" in val:
        return "Power BI"
    elif "Data Engineer" in val:
        return "Data Engineer"
    elif "Data Scientist" in val:
        return "Data Scientist"
    else:
        return "Autre"

df["Profil"] = df["Mot_Cle"].apply(clean_mot_cle)

# ── FILTRE FRANCE UNIQUEMENT ────────────────────────────
df = df[~df["Ville"].str.contains(
    "Luxembourg|Belgique|Suisse",
    case=False, na=False
)]

# ── NETTOYAGE EXPÉRIENCE ────────────────────────────────
def clean_experience(val):
    if pd.isna(val) or val == "":
        return "Non précisé"
    val = str(val)
    if "Débutant" in val or "sans expérience" in val.lower():
        return "Débutant"
    elif "1" in val or "2" in val:
        return "1-2 ans"
    elif "3" in val or "4" in val or "5" in val:
        return "3-5 ans"
    elif "6" in val or "7" in val or "8" in val or "9" in val:
        return "6+ ans"
    else:
        return "Non précisé"

df["Experience_Clean"] = df["Experience"].apply(clean_experience)

# ── NETTOYAGE SECTEUR ───────────────────────────────────
df["Secteur"] = df["Secteur"].fillna("Non précisé")

# ── COLONNES FINALES ────────────────────────────────────
df_final = df[[
    "ID",
    "Titre",
    "Profil",
    "Date_Creation",
    "Entreprise",
    "Type_Contrat_Clean",
    "Experience_Clean",
    "Qualification",
    "Salaire_Min",
    "Salaire_Max",
    "Salaire_Moyen",
    "Ville_Clean",
    "Code_Dept",
    "Secteur",
    "Description"
]].rename(columns={
    "Type_Contrat_Clean" : "Type_Contrat",
    "Experience_Clean"   : "Experience",
    "Ville_Clean"        : "Ville"
})

# ── EXPORT ──────────────────────────────────────────────
df_final.to_csv("offres_data_final.csv", index=False, encoding="utf-8-sig")
print(f"✅ {len(df_final)} offres nettoyées → offres_data_final.csv")
print(f"   Salaires renseignés : {df_final['Salaire_Moyen'].notna().sum()}")
print(f"\n   Répartition profils :")
print(df_final["Profil"].value_counts())
print(f"\n   Répartition contrats :")
print(df_final["Type_Contrat"].value_counts())
print(f"\n   Répartition expérience :")
print(df_final["Experience"].value_counts())