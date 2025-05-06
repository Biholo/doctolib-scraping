import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from datetime import datetime, date
import urllib.parse

# Configurer les logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def process_practitioner_card(driver, card, params):
    """Traite une carte de praticien et retourne ses informations."""
    try:
        # Scroll vers la carte
        scroll_to_element(driver, card)
        time.sleep(0.5)

        # 1. Extraire les informations de base
        name = card.find_element(By.XPATH, ".//h2[contains(@class, 'dl-text-primary-110')]").text
        specialty = card.find_element(By.XPATH, ".//p[contains(@class, 'G5dSlmEET4Zf5bQ5PR69')]").text
        address_elements = card.find_elements(By.XPATH, ".//div[contains(@class, 'flex flex-wrap gap-x-4')]//p[contains(@class, 'G5dSlmEET4Zf5bQ5PR69')]")
        location = " ".join([elem.text for elem in address_elements])
        doctor_link = card.find_element(By.XPATH, ".//a[contains(@class, 'dl-text-decoration-none')]").get_attribute('href')

        # 2. Récupérer les disponibilités
        availability = []
        try:
            

            end_date = datetime.strptime(params["end_date"], "%d/%m/%Y")
            last_visible_date = None

            while True:

                # Vérifier s'il y a un bouton "Prochain RDV"
                next_rdv_button = card.find_elements(By.XPATH, ".//button[contains(@class, 'dl-button-small-primary')]")
                if next_rdv_button:
                    next_rdv_button[0].click()
                    time.sleep(1)


                # Récupérer tous les créneaux visibles
                slot_buttons = card.find_elements(By.XPATH, ".//button[@data-test-id='slot-button']")
                if not slot_buttons: 
                    next_rdv_text = card.find_elements(By.XPATH, ".//div[contains(@class, 'dl-card-variant-shadow-3')]//button")
                    if next_rdv_text:
                        date_text = next_rdv_text[0].text.replace('Prochain RDV le ', '')
                        availability.append(date_text)
                    break

                # Récupérer la dernière date visible
                date_elements = card.find_elements(By.XPATH, ".//div[contains(@id, 'date-')]")
                logging.info(f"Date elements: {date_elements}")
                if date_elements:
                    last_date_text = date_elements[-1].text
                    logging.info(f"Last date text: {last_date_text}")
                    try:
                        date_parts = last_date_text.split()
                        if len(date_parts) >= 2:
                            logging.info(f"Dernière date visible : {last_date_text}")
                            day = int(date_parts[1])
                            month = get_month_number(date_parts[2])
                            year = datetime.now().year
                            last_visible_date = datetime(year, month, day)
                    except Exception as e:
                        logging.warning(f"Erreur lors de l'extraction de la dernière date visible : {e}")

                # Extraire les créneaux
                for slot in slot_buttons:
                    try:
                        slot_time = slot.find_element(By.XPATH, ".//span[contains(@class, 'dl-button-label')]").text
                        date_id = slot.get_attribute('aria-labelledby').split()[1]
                        date_element = card.find_element(By.ID, date_id)
                        date_text = date_element.text
                        # Si le créneau n'a pas d'heure, on ajoute juste la date
                        if not slot_time:
                            availability.append(date_text)
                        else:
                            availability.append(f"{date_text} {slot_time}")
                    except Exception as e:
                        logging.warning(f"Erreur lors de l'extraction d'un créneau : {e}")
                        continue

                # Vérifier si on doit continuer à chercher plus de dates
                logging.info(f"Last visible date: {last_visible_date} and end_date: {end_date}")
                
                # Convertir en date si ce n'est pas déjà fait
                if not isinstance(last_visible_date, date):
                    if isinstance(last_visible_date, datetime):
                        last_visible_date = last_visible_date.date()
                    else:
                        try:
                            # Si c'est une chaîne de caractères, on la convertit en date
                            last_visible_date = datetime.strptime(last_visible_date, "%d/%m/%Y").date()
                        except:
                            logging.warning(f"Impossible de convertir la date: {last_visible_date}")
                            continue

                if not isinstance(end_date, date):
                    if isinstance(end_date, datetime):
                        end_date = end_date.date()
                    else:
                        try:
                            # Si c'est une chaîne de caractères, on la convertit en date
                            end_date = datetime.strptime(end_date, "%d/%m/%Y").date()
                        except:
                            logging.warning(f"Impossible de convertir la date: {end_date}")
                            continue

                logging.info(f"Last visible date: {last_visible_date} and end_date: {end_date}")
                
                if last_visible_date and last_visible_date < end_date:
                    more_slots_button = card.find_elements(By.XPATH, ".//button[contains(@class, 'dl-icon-button-medium')]")[-1]
                    if more_slots_button:
                        more_slots_button.click()
                        time.sleep(2)
                        continue

                break

        except Exception as e:
            logging.warning(f"Erreur lors de l'extraction des disponibilités : {e}")

        # 3. Visiter le profil pour les informations supplémentaires
        
        logging.info(f"Créneaux trouvés pour {name}:")
        for slot in availability:
            logging.info(f"  - {slot}")
        if not availability:  # On ne visite le profil que si on a trouvé des créneaux
            return None

        driver.get(doctor_link)
        time.sleep(2)

        # Récupérer les informations supplémentaires
        try:
            insurance_type = driver.find_element(By.XPATH, "//div[contains(text(), 'Conventionnement')]").text
        except:
            insurance_type = "Non spécifié"

        try:
            consultation_type = driver.find_element(By.XPATH, "//div[contains(text(), 'Type de consultation')]").text
        except:
            consultation_type = "Non spécifié"

        try:
            price = driver.find_element(By.XPATH, "//div[contains(text(), 'Tarifs')]").text
        except:
            price = "Non spécifié"

        try:
            address_details = driver.find_element(By.XPATH, '//div[@class="dl-profile-address-picker-address-text"]//div[@class="dl-profile-practice-name"]/following-sibling::text()[1]').text
        except:
            address_details = location

    

        logging.info(f"Résultats trouvés pour {name}:")
        logging.info(f"  - Spécialité: {specialty}")
        logging.info(f"  - Lieu: {location}")
        logging.info(f"  - Disponibilités: {availability}")
        logging.info(f"  - Lien: {doctor_link}")
        logging.info(f"  - Type de conventionnement: {insurance_type}")
        logging.info(f"  - Type de consultation: {consultation_type}")
        logging.info(f"  - Prix: {price}")
        logging.info(f"  - Adresse détaillée: {address_details}")

        return {
            "name": name,
            "specialty": specialty,
            "location": location,
            "availability": availability,
            "doctor_link": doctor_link,
            "insurance_type": insurance_type,
            "consultation_type": consultation_type,
            "price": price,
            "address_details": address_details
        }

    except Exception as e:
        logging.error(f"Erreur lors du traitement de la carte du praticien : {e}")
        return None

def scrape_doctolib(params):
    # Initialisation du driver Selenium avec webdriver-manager
    logging.info("Démarrage du scraping Doctolib...")
    
    # Configuration des options Chrome
    chrome_options = Options()
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    
    service = Service()
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    try:
        # Préparation de l'URL de base
        availability_before = ""
        if params.get('start_date'):
            try:
                date_obj = datetime.strptime(params['start_date'], "%d/%m/%Y")
                today = datetime.now()
                days_difference = (date_obj - today).days
                availability_before = f"&availabilitiesBefore={days_difference}"
                logging.info(f"Date de disponibilité configurée : {params['start_date']} (jours: {days_difference})")
            except ValueError as e:
                logging.warning(f"Format de date invalide pour availabilitiesBefore: {params['start_date']}. Erreur: {e}")
        
        encoded_address = urllib.parse.quote(params.get('address', ''))
        encoded_specialty = urllib.parse.quote(params.get('specialty', ''))
        
        all_practitioners = []
        page = 1
        max_results = params.get("max_results", 10)
        
        while True:
            # Construire et visiter l'URL de la page
            search_url = f"https://www.doctolib.fr/search?location={encoded_address}&speciality={encoded_specialty}{availability_before}&page={page}"
            logging.info(f"Traitement de la page {page}")
            
            driver.get(search_url)
            time.sleep(3)

            # Récupérer toutes les cartes de praticiens
            practitioners_elements = driver.find_elements(By.XPATH, "//div[@class='dl-card dl-card-bg-white dl-card-variant-default dl-card-border !p-0 transition-all ease-in-out duration-500 hover:border-primary-110 hover:shadow-md']")
            logging.info(f"{len(practitioners_elements)} praticiens trouvés sur la page {page}")

            # Si moins de 18 praticiens sont trouvés, c'est la dernière page
            if len(practitioners_elements) < 18:
                logging.info("Dernière page atteinte")
                break

            # Traiter chaque carte de praticien
            for card in practitioners_elements:
                practitioner_data = process_practitioner_card(driver, card, params)
                time.sleep(1.5)              
                if practitioner_data and apply_additional_filters(practitioner_data, params):
                    all_practitioners.append(practitioner_data)
                    logging.info(f"Praticien ajouté : {practitioner_data['name']}")
                    
                    if len(all_practitioners) >= max_results:
                        logging.info(f"Nombre maximum de résultats atteint ({max_results})")
                        break
                        
            if len(all_practitioners) >= max_results:
                break

            page += 1

        driver.quit()
        logging.info("Scraping terminé, navigateur fermé.")
        return all_practitioners[:max_results]

    except Exception as e:
        logging.error(f"Erreur pendant le scraping : {e}")
        driver.quit()
        return []


def apply_additional_filters(practitioner, params):
    # Filtre par période de disponibilité
    if not is_available(practitioner["availability"], params["start_date"], params["end_date"]):
        logging.info(f"Praticien {practitioner['name']} filtré : disponibilité non valide.")
        return False
    
    # Filtre par type d'assurance
    # if not is_valid_insurance(practitioner["insurance_type"], params["insurance_type"]):
    #     logging.info(f"Praticien {practitioner['name']} filtré : type d'assurance non valide.")
    #     return False
    
    # Filtre par type de consultation
    # if not is_valid_consultation(practitioner["consultation_type"], params["consultation_type"]):
        # logging.info(f"Praticien {practitioner['name']} filtré : type de consultation non valide.")
        # return False
    
    # Filtre par plage de prix
    # if not is_valid_price(practitioner["price"], params["price_min"], params["price_max"]):
        # logging.info(f"Praticien {practitioner['name']} filtré : prix non valide.")
        # return False
    
    # Filtre géographique par adresse (si applicable)
    if not is_valid_address(practitioner["name"], params["include_zones"]):
        logging.info(f"Praticien {practitioner['name']} filtré : adresse non valide.")
        return False
    
    return True

def is_available(availability_list, start_date, end_date):
    # Vérifie si les dates de disponibilité correspondent à la période demandée
    if not availability_list:
        return False
        
    start_date = datetime.strptime(start_date, "%d/%m/%Y")
    end_date = datetime.strptime(end_date, "%d/%m/%Y")
    
    # Pour chaque disponibilité dans la liste
    for availability in availability_list:
        try:
            # Le format est "jour mois heure" (ex: "mardi 6 mai 16:30")
            date_parts = availability.split()
            if len(date_parts) >= 3:
                day = int(date_parts[1])  # Le jour
                month = get_month_number(date_parts[2])  # Le mois
                year = datetime.now().year  # L'année en cours
                
                # Créer la date complète
                available_date = datetime(year, month, day)
                
                # Vérifier si la date est dans la plage demandée
                if start_date <= available_date <= end_date:
                    return True
        except Exception as e:
            logging.warning(f"Erreur lors de la vérification de la disponibilité {availability}: {e}")
            continue
    
    return False

def get_month_number(month_name):
    """Convertit le nom du mois en français en numéro de mois."""
    months = {
        'janvier': 1, 'février': 2, 'mars': 3, 'avril': 4, 'mai': 5, 'juin': 6,
        'juillet': 7, 'août': 8, 'septembre': 9, 'octobre': 10, 'novembre': 11, 'décembre': 12
    }
    return months.get(month_name.lower(), 1)  # Retourne 1 (janvier) par défaut si le mois n'est pas trouvé

def is_valid_insurance(practitioner_insurance, required_insurance):
    # Filtrer par type d'assurance (secteur 1, secteur 2, non conventionné)
    if practitioner_insurance and required_insurance:
        return practitioner_insurance.lower() == required_insurance.lower()
    return True  # Pas de filtre si pas spécifié

def is_valid_consultation(practitioner_type, required_type):
    # Filtrer par type de consultation (visio ou sur place)
    if practitioner_type and required_type:
        return practitioner_type.lower() == required_type.lower()
    return True  # Pas de filtre si pas spécifié

def is_valid_price(practitioner_price, min_price, max_price):
    # Vérifier si le prix est dans la plage spécifiée
    try:
        price = float(practitioner_price.replace("€", "").strip())
        return min_price <= price <= max_price
    except ValueError:
        logging.warning(f"Prix invalide pour {practitioner_price}")
        return False

def is_valid_address(practitioner_name, include_zones):
    # Filtrer par adresse ou zones spécifiques
    if include_zones:
        for zone in include_zones:
            if zone.lower() in practitioner_name.lower():
                return True
        return False
    return True

def scroll_to_element(driver, element):
    """Fait défiler la page jusqu'à l'élément spécifié."""
    try:
        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", element)
        time.sleep(0.5)  # Attendre que le scroll soit terminé
    except Exception as e:
        logging.warning(f"Erreur lors du scroll vers l'élément : {e}")

def scroll_to_bottom(driver):
    """Fait défiler la page jusqu'en bas."""
    try:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(0.5)  # Attendre que le scroll soit terminé
    except Exception as e:
        logging.warning(f"Erreur lors du scroll vers le bas : {e}")
