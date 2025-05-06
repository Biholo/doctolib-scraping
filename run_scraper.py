import argparse
import logging
from services.scraper import scrape_doctolib

# Configuration de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def parse_arguments():
    # Configuration de argparse pour récupérer les arguments depuis la ligne de commande
    parser = argparse.ArgumentParser(description="Lance le scraping des praticiens sur Doctolib.")
    
    parser.add_argument('--specialty', type=str, required=True, help="Spécialité médicale (ex: dermatologue, généraliste)")
    parser.add_argument('--address', type=str, required=True, help="Adresse ou localisation de recherche")
    parser.add_argument('--start_date', type=str, required=True, help="Date de début de disponibilité (format: JJ/MM/AAAA)")
    parser.add_argument('--end_date', type=str, required=True, help="Date de fin de disponibilité (format: JJ/MM/AAAA)")
    parser.add_argument('--insurance_type', type=str, choices=['secteur 1', 'secteur 2', 'non conventionné'], help="Type d'assurance")
    parser.add_argument('--consultation_type', type=str, choices=['visio', 'sur place'], help="Type de consultation")
    parser.add_argument('--price_min', type=float, default=0, help="Plage de prix minimum (€)")
    parser.add_argument('--price_max', type=float, default=200, help="Plage de prix maximum (€)")
    parser.add_argument('--include_zones', type=str, nargs='*', help="Zones géographiques supplémentaires à inclure (ex: 75015, rue de Vaugirard)")
    parser.add_argument('--max_results', type=int, default=10, help="Nombre maximum de résultats à afficher")
    
    return parser.parse_args()

def main():
    # Récupérer les arguments de la ligne de commande
    args = parse_arguments()
    
    # Convertir les arguments en dictionnaire pour les passer au scraper
    params = {
        "specialty": args.specialty,
        "address": args.address,
        "start_date": args.start_date,
        "end_date": args.end_date,
        "insurance_type": args.insurance_type,
        "consultation_type": args.consultation_type,
        "price_min": args.price_min,
        "price_max": args.price_max,
        "include_zones": args.include_zones,
        "max_results": args.max_results
    }
    
    # Lancer le scraping
    logging.info("Lancement du scraper avec les paramètres suivants :")
    logging.info(f"Spécialité : {args.specialty}, Localisation : {args.address}")
    
    result = scrape_doctolib(params)
    
    if result:
        logging.info(f"{len(result)} praticiens trouvés correspondant aux critères.")
        for practitioner in result:
            logging.info(f"Nom : {practitioner['name']}, Disponibilité : {practitioner['availability']}, Prix : {practitioner['price']}")
    else:
        logging.info("Aucun praticien trouvé ou erreur lors du scraping.")

if __name__ == '__main__':
    main()
