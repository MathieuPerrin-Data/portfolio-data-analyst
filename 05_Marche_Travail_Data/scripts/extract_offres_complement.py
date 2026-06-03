import requests
import pandas as pd
from datetime import datetime

CLIENT_ID     = "PAR_portfolio_6336251725ff943c575ec023172014e11c5ce530296ccf07894144ff78c26290"
CLIENT_SECRET = "da410bf6462c83d275af10ae8b70f594c4b5d5a5ede3da026d9f14b7008e05fd"
TOKEN_URL     = "https://entreprise.francetravail.fr/connexion/oauth2/access_token?realm=%2Fpartenaire"
API_URL       = "https://api.francetravail.io/partenaire/offresdemploi/v2/offres/search"

def get_token():
    response = requests.post(
        TOKEN_URL,
        data={
            "grant_type":    "client_credentials",
            "client_id":     CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "scope":         "api_offresdemploiv2 o2dsoffre"
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    return response.json()["access_token"]

def get_offres(token, mot_cle, start=0):
    headers = {"Authorization": f"Bearer {token}"}
    params  = {
        "motsCles"      : mot_cle,
        "range"         : f"{start}-{start+149}",
        "sort"          : "1",
        "publieeDepuis" : "31"
    }
    response = requests.get(API_URL, headers=headers, params=params)
    if response.status_code == 200:
        return response.json()
    print(f"Erreur {response.status_code} : {response.text}")
    return None

# Mots clés manquants uniquement
mots_cles = [
    "Data Analyst",
    "Data Engineer",
    "Analyste BI",
    "Analyste données"
]

token  = get_token()
offres = []

for mot_cle in mots_cles:
    print(f"Extraction : {mot_cle}")
    start = 0
    while True:
        data = get_offres(token, mot_cle, start)
        if not data or "resultats" not in data:
            print(f"  → Aucun résultat ou erreur")
            break
        resultats = data["resultats"]
        if not resultats:
            print(f"  → 0 offre supplémentaire")
            break
        print(f"  → {len(resultats)} offres extraites (start={start})")
        for offre in resultats:
            offres.append({
                "ID"             : offre.get("id", ""),
                "Titre"          : offre.get("intitule", ""),
                "Mot_Cle"        : mot_cle,
                "Date_Creation"  : offre.get("dateCreation", "")[:10],
                "Entreprise"     : offre.get("entreprise", {}).get("nom", ""),
                "Type_Contrat"   : offre.get("typeContratLibelle", ""),
                "Experience"     : offre.get("experienceLibelle", ""),
                "Qualification"  : offre.get("qualificationLibelle", ""),
                "Salaire_Libelle": offre.get("salaire", {}).get("libelle", ""),
                "Ville"          : offre.get("lieuTravail", {}).get("libelle", ""),
                "Code_Postal"    : offre.get("lieuTravail", {}).get("codePostal", ""),
                "Departement"    : offre.get("lieuTravail", {}).get("libelle", "")[:2],
                "Secteur"        : offre.get("secteurActiviteLibelle", ""),
                "Teletravail"    : offre.get("experienceCommentaire", ""),
                "Description"    : offre.get("description", "")[:500]
            })
        start += 150
        if start >= 3000:
            break

if offres:
    df = pd.DataFrame(offres)
    df = df.drop_duplicates(subset=["ID"])
    filename = f"offres_complement_{datetime.now().strftime('%Y%m%d')}.csv"
    df.to_csv(filename, index=False, encoding="utf-8-sig")
    print(f"✅ {len(df)} offres exportées → {filename}")
else:
    print("❌ Aucune offre extraite")