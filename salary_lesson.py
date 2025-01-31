import os
import time
import urllib.parse
import requests
from dotenv import load_dotenv
from terminaltables import AsciiTable


def predict_rub_salary(vacancy):
    if "salary" in vacancy:
        salary = vacancy["salary"]
        if not salary or salary.get("currency") != "RUR":
            return None
        salary_from = salary.get("from")
        salary_to = salary.get("to")
    else:
        salary_from = vacancy.get("payment_from")
        salary_to = vacancy.get("payment_to")
        currency = vacancy.get("currency")
        if currency != "rub":
            return None

    if salary_from and salary_to:
        return (salary_from + salary_to) / 2
    elif salary_from:
        return salary_from * 1.2
    elif salary_to:
        return salary_to * 0.8
    return None



def fetch_hh_vacancies(lang, area=1):
    vacancies = []
    base_url = "https://api.hh.ru/vacancies"

    params = {
        "text": lang,
        "area": area,
        "per_page": 100,
        "page": 0
    }

    try:
        response = requests.get(f"{base_url}?{urllib.parse.urlencode(params)}")
        response.raise_for_status()
        decoded_response = response.json()

        if 'error' in decoded_response:
            raise requests.exceptions.HTTPError(decoded_response['error'])

        total_pages = decoded_response.get("pages", 1)
        total_vacancies = decoded_response.get("found", 0)

        for page in range(total_pages):
            params["page"] = page
            url = f"{base_url}?{urllib.parse.urlencode(params)}"

            response = requests.get(url)
            response.raise_for_status()
            decoded_response = response.json()

            if 'error' in decoded_response:
                raise requests.exceptions.HTTPError(decoded_response['error'])

            hh_vacancy_items = decoded_response.get("items", [])
            vacancies.extend(hh_vacancy_items)

            print(f"Загружено {len(hh_vacancy_items)} вакансий для {lang} (страница {page + 1} из {total_pages})")

            if not hh_vacancy_items:
                break

            time.sleep(0.5)

    except requests.exceptions.RequestException as e:
        print(f"Ошибка при загрузке вакансий с HH: {e}")

    return vacancies, total_vacancies


def fetch_sj_vacancies(lang, area=1, headers=None):
    vacancies = []
    base_url = "https://api.superjob.ru/2.0/vacancies/"

    params = {
        "keyword": lang,
        "town": area,
        "page": 0,
        "count": 100
    }

    try:
        response = requests.get(f"{base_url}?{urllib.parse.urlencode(params)}", headers=headers)
        response.raise_for_status()
        decoded_response = response.json()

        if 'error' in decoded_response:
            raise requests.exceptions.HTTPError(decoded_response['error'])

        total_vacancies = decoded_response.get("total", 0)
        total_pages = (total_vacancies // params["count"]) + (1 if total_vacancies % params["count"] else 0)

        for page in range(total_pages):
            params["page"] = page
            url = f"{base_url}?{urllib.parse.urlencode(params)}"

            response = requests.get(url, headers=headers)
            response.raise_for_status()
            decoded_response = response.json()

            if 'error' in decoded_response:
                raise requests.exceptions.HTTPError(decoded_response['error'])

            js_vacancy_items = decoded_response.get("objects", [])
            vacancies.extend(js_vacancy_items)

            print(f"Загружено {len(js_vacancy_items)} вакансий для {lang} (страница {page + 1} из {total_pages})")

            if not js_vacancy_items:
                break

            time.sleep(0.5)

    except requests.exceptions.RequestException as e:
        print(f"Ошибка при загрузке вакансий с SuperJob: {e}")

    return vacancies, total_vacancies


def fetch_all_vacancies(lang, site, area=1, headers=None):
    if site == 'hh':
        return fetch_hh_vacancies(lang, area)
    elif site == 'sj':
        return fetch_sj_vacancies(lang, area, headers)
    return [], 0


def get_language_salary_stats(languages, site, area=1, headers=None):
    stats = {}

    for lang in languages:
        print(f"Обрабатываю {lang} на {site}...")
        vacancies, total_vacancies = fetch_all_vacancies(lang, site, area, headers)

        salaries = [predict_rub_salary(vac) for vac in vacancies]
        salaries = [int(s) for s in salaries if s]
        
        stats[lang] = {
            "vacancies_found": total_vacancies,
            "vacancies_processed": len(salaries),
            "average_salary": int(sum(salaries) / len(salaries)) if salaries else None
        }

    return stats


def print_table(stats, site):
    table_data = []
    table_data.append([f'{site} Moscow', 'Вакансий найдено', 'Обработано вакансий', 'Средняя зарплата'])
    
    for lang, data in stats.items():
        table_data.append([
            lang,
            data["vacancies_found"],
            data["vacancies_processed"],
            data["average_salary"] if data["average_salary"] else "Нет данных"
        ])

    table = AsciiTable(table_data)
    print(table.table)


def main():
    load_dotenv()
    headers = {'X-Api-App-Id': os.getenv("SUPERJOB_API_KEY")}

    languages = ["Python", "Java", "Javascript", "C++", "C#", "Go", "Swift", "Kotlin", "Ruby", "PHP"]

    hh_stats = get_language_salary_stats(languages, site='hh', headers=headers)
    sj_stats = get_language_salary_stats(languages, site='sj', headers=headers)

    print_table(hh_stats, "HeadHunter")
    print_table(sj_stats, "SuperJob")


if __name__ == "__main__":
    main()
