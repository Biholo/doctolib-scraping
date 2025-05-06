from flask import Flask, request, jsonify
from services.scraper import scrape_doctolib
from services.db_manager import save_to_db

app = Flask(__name__)

@app.route('/scrape', methods=['POST'])
def scrape():
    try:
        # Récupérer les arguments envoyés dans le body de la requête
        data = request.json
        # Exemple des paramètres attendus :
        # {
        #     "max_results": 10,
        #     "start_date": "01/06/2025",
        #     "end_date": "30/06/2025",
        #     "specialty": "dermatologue",
        #     "insurance_type": "secteur 1",
        #     "consultation_type": "sur place",
        #     "price_min": 50,
        #     "price_max": 150,
        #     "address": "rue de Vaugirard",
        #     "include_zones": ["75015", "Boulogne"]
        # }
        
        # Appeler la fonction de scraping avec les paramètres
        result = scrape_doctolib(data)
        
        # Sauvegarder les résultats dans la base de données ou fichier
        save_to_db(result)
        
        return jsonify({"message": "Scraping réussi", "data": result}), 200
    
    except Exception as e:
        return jsonify({"message": "Erreur pendant le scraping", "error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
