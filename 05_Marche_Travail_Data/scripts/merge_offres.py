import pandas as pd

# Charger les deux fichiers bruts
df1 = pd.read_csv("offres_data_20260406.csv", encoding="utf-8-sig")
df2 = pd.read_csv("offres_complement_20260406.csv", encoding="utf-8-sig")

# Fusionner
df = pd.concat([df1, df2], ignore_index=True)

# Supprimer les doublons sur ID
df = df.drop_duplicates(subset=["ID"])

print(f"Total offres fusionnées : {len(df)}")
print(f"Répartition Mot_Cle :")
print(df["Mot_Cle"].value_counts())

# Exporter
df.to_csv("offres_data_merged.csv", index=False, encoding="utf-8-sig")
print("✅ Exporté → offres_data_merged.csv")