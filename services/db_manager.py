import csv

def save_to_db(results):
    try:
        with open('practitioners.csv', mode='w', newline='', encoding='utf-8') as file:
            fieldnames = ["name", "availability", "price"]
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)
        
        print("Données sauvegardées avec succès dans practitioners.csv")
    except Exception as e:
        print(f"Erreur lors de la sauvegarde des données: {e}")
