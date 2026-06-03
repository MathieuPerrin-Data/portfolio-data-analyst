import pandas as pd
import re

# ── CHARGEMENT ──────────────────────────────────────────
df = pd.read_csv("offres_data_merged.csv", encoding="utf-8-sig")

# ── EXTRACTION CODE DÉPARTEMENT DEPUIS VILLE BRUTE ─────
# Faire l'extraction AVANT le nettoyage de la ville
df["Code_Dept"] = df["Ville"].str.extract(r"^(\d{2,3})\s*-")
df["Code_Dept"] = df["Code_Dept"].fillna("00")

# ── NETTOYAGE VILLE ─────────────────────────────────────
def clean_ville(val):
    if pd.isna(val):
        return "Non précisé"
    val = str(val)

    # Supprimer préfixe département "XX - "
    val = re.sub(r"^\d{2,3}\s*-\s*", "", val)

    # Supprimer CEDEX
    val = re.sub(r"\s*Cedex\s*\d*", "", val, flags=re.IGNORECASE)

    # Normaliser arrondissements
    val = re.sub(r"\s+\d{1,2}(er|ème|e|E)\s*arrondissement",
                 "", val, flags=re.IGNORECASE)
    val = re.sub(r"\s+\d{1,2}(er|ème|e|E)$", "", val)
    val = re.sub(r"\s+\d{2}$", "", val)

    # Nettoyer
    val = val.strip().title()

    # Remplacer valeurs non géographiques
    non_geo = ["France", "Ile-De-France", "Île-De-France",
               "Paris (Dept.)", "Nord", "Aude",
               "Val-D'Oise", "Val-De-Marne", "Hauts-De-Seine",
               "Seine-Saint-Denis", "Loire-Atlantique",
               "Côtes-D'Armor"]
    if val in non_geo:
        return "Non précisé"

    return val

df["Ville"] = df["Ville"].apply(clean_ville)

# ── CORRECTION CODE DÉPARTEMENT ────────────────────────
# Correspondance nom département → code
dept_map = {
    "Val-D'Oise"        : "95",
    "Val-De-Marne"      : "94",
    "Hauts-De-Seine"    : "92",
    "Seine-Saint-Denis" : "93",
    "Loire-Atlantique"  : "44",
    "Côtes-D'Armor"     : "22",
    "Nord"              : "59",
    "Aude"              : "11"
}

# Correspondance ville → code département
ville_dept = {
    "Paris"      : "75",
    "Lyon"       : "69",
    "Marseille"  : "13",
    "Bordeaux"   : "33",
    "Toulouse"   : "31",
    "Nantes"     : "44",
    "Strasbourg" : "67",
    "Rennes"     : "35",
    "Lille"      : "59",
    "Nice"       : "06",
    "Montpellier": "34",
    "Grenoble"   : "38",
    "Aix-En-Provence" : "13"
}

def fix_dept(row):
    dept = str(row["Code_Dept"]).strip()
    ville_brute = str(row["Ville_Brute"]).strip() if "Ville_Brute" in row else ""
    ville = str(row["Ville"]).strip()

    # Déjà un code valide
    if dept != "00" and dept != "nan":
        return dept

    # Chercher dans dept_map
    for k, v in dept_map.items():
        if k.lower() in ville_brute.lower():
            return v

    # Chercher dans ville_dept
    for k, v in ville_dept.items():
        if k.lower() in ville.lower():
            return v

    return "00"

# Garder la ville brute pour le matching
df["Ville_Brute"] = df["Ville"].copy()
df["Code_Dept"] = df.apply(fix_dept, axis=1)
df = df.drop(columns=["Ville_Brute"])

# ── AJOUT RÉGION ────────────────────────────────────────
def get_region(dept):
    dept = str(dept).strip().zfill(2)
    regions = {
        "Île-de-France"          : ["75","77","78","91","92","93","94","95"],
        "Auvergne-Rhône-Alpes"   : ["01","03","07","15","26","38","42","43",
                                    "63","69","73","74"],
        "PACA"                   : ["04","05","06","13","83","84"],
        "Occitanie"              : ["09","11","12","30","31","32","34","46",
                                    "48","65","66","81","82"],
        "Nouvelle-Aquitaine"     : ["16","17","19","23","24","33","40","47",
                                    "64","79","86","87"],
        "Bretagne"               : ["22","29","35","56"],
        "Hauts-de-France"        : ["02","59","60","62","80"],
        "Grand Est"              : ["08","10","51","52","54","55","57","67",
                                    "68","88"],
        "Normandie"              : ["14","27","50","61","76"],
        "Pays de la Loire"       : ["44","49","53","72","85"],
        "Centre-Val de Loire"    : ["18","28","36","37","41","45"],
        "Bourgogne-Franche-Comté": ["21","25","39","58","70","71","89","90"],
        "DOM-TOM"                : ["971","972","973","974","976"]
    }
    for region, depts in regions.items():
        if dept in depts:
            return region
    if dept == "00":
        return "Non précisé"
    return "Autre région"

# ── NETTOYAGE TYPE CONTRAT ──────────────────────────────
def clean_contrat(val):
    if pd.isna(val):
        return "Non précisé"
    val = str(val)
    if "CDI" in val:        return "CDI"
    elif "CDD" in val:      return "CDD"
    elif "Intérim" in val:  return "Intérim"
    elif "Alternance" in val or "Apprentissage" in val:
        return "Alternance"
    elif "libérale" in val.lower(): return "Freelance"
    else: return "Autre"

df["Type_Contrat"] = df["Type_Contrat"].apply(clean_contrat)

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
        min_sal *= 12
        max_sal *= 12
    salaire_moyen = (min_sal + max_sal) / 2
    return min_sal, max_sal, salaire_moyen

df[["Salaire_Min","Salaire_Max","Salaire_Moyen"]] = df["Salaire_Libelle"].apply(
    lambda x: pd.Series(parse_salaire(x))
)

# Filtrer salaires aberrants
df.loc[df["Salaire_Moyen"] < 15000,
       ["Salaire_Min","Salaire_Max","Salaire_Moyen"]] = None
df.loc[df["Salaire_Moyen"] > 200000,
       ["Salaire_Min","Salaire_Max","Salaire_Moyen"]] = None
mask = df["Salaire_Max"] < df["Salaire_Min"]
df.loc[mask, ["Salaire_Min","Salaire_Max","Salaire_Moyen"]] = None

# ── NETTOYAGE MOT CLÉ ───────────────────────────────────
def clean_mot_cle(val):
    if pd.isna(val): return "Autre"
    val = str(val)
    if "Data Analyst" in val:                        return "Data Analyst"
    elif "Analyste données" in val or "Analyste BI" in val: return "Data Analyst"
    elif "Business Intelligence" in val:             return "Business Intelligence"
    elif "Power BI" in val:                          return "Power BI"
    elif "Data Engineer" in val:                     return "Data Engineer"
    elif "Data Scientist" in val:                    return "Data Scientist"
    else:                                            return "Autre"

df["Profil"] = df["Mot_Cle"].apply(clean_mot_cle)

# ── NETTOYAGE EXPÉRIENCE ────────────────────────────────
def clean_experience(val):
    if pd.isna(val) or val == "": return "Non précisé"
    val = str(val)
    if "Débutant" in val or "sans expérience" in val.lower(): return "Débutant"
    elif "1" in val or "2" in val: return "1-2 ans"
    elif "3" in val or "4" in val or "5" in val: return "3-5 ans"
    elif "6" in val or "7" in val or "8" in val or "9" in val: return "6+ ans"
    else: return "Non précisé"

df["Experience"] = df["Experience"].apply(clean_experience)

# ── NETTOYAGE SECTEUR ───────────────────────────────────
df["Secteur"] = df["Secteur"].fillna("Non précisé")

# ── FILTRE FRANCE UNIQUEMENT ────────────────────────────
df = df[~df["Ville"].str.contains(
    "Luxembourg|Belgique|Suisse", case=False, na=False
)]

# ── AJOUT RÉGION ────────────────────────────────────────
df["Region"] = df["Code_Dept"].apply(get_region)

# ── COLONNES FINALES ────────────────────────────────────
df_final = df[[
    "ID", "Titre", "Profil", "Date_Creation",
    "Entreprise", "Type_Contrat", "Experience",
    "Qualification", "Salaire_Min", "Salaire_Max",
    "Salaire_Moyen", "Ville", "Code_Dept", "Region",
    "Secteur", "Description"
]]

# ── EXPORT ──────────────────────────────────────────────
df_final.to_csv("offres_data_final.csv", index=False, encoding="utf-8-sig")
print(f"✅ {len(df_final)} offres → offres_data_final.csv")
print(f"Salaires renseignés : {df_final['Salaire_Moyen'].notna().sum()}")
print(f"Salaire médian      : {df_final['Salaire_Moyen'].median():.0f}€")
print(f"\nRépartition Profil :")
print(df_final["Profil"].value_counts())
print(f"\nRépartition Region :")
print(df_final["Region"].value_counts())
print(f"\nCode_Dept 00 restants : {(df_final['Code_Dept'] == '00').sum()}")