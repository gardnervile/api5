import os
import time
import requests
from dotenv import load_dotenv
from terminaltables import AsciiTable


def extract_hh_salary(salary):
    if not salary or salary.get("currency") != "RUR":
        return None
    return salary.get("from"), salary.get("to")


def extract_sj_salary(vacancy):
    if vacancy.get("currency") != "rub":
        return None
    return vacancy.get("payment_from"), vacancy.get("payment_to")


def calculate_average_salary(salary_from, salary_to):
    if salary_from and salary_to:
        return (salary_from + salary_to) / 2
    elif salary_from:
        return salary_from * 1.2
    elif salary_to:
        return salary_to * 0.8
    return None


def predict_rub_salary(vacancy):
    salary_data = extract_hh_salary(vacancy["salary"]) if "salary" in vacancy else extract_sj_salary(vacancy)
    return calculate_average_salary(*salary_data) if salary_data else None


def fetch_hh_vacancies(lang, area=1):
    vacancies = []
    base_url = "https://api.hh.ru/vacancies"

    params = {
        "text": lang,
        "area": area,
        "per_page": 100,
        "page": 0
    }

    response = requests.get(base_url, params=params)
    response.raise_for_status()
    decoded_response = response.json()

    if 'error' in decoded_response:
        raise requests.exceptions.HTTPError(decoded_response['error'])

    total_pages = decoded_response.get("pages", 1)
    total_vacancies = decoded_response.get("found", 0)
    vacancies.extend(decoded_response.get("items", []))

    for page in range(1, total_pages):
        params["page"] = page
        response = requests.get(base_url, params=params)
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

    while True:
        response = requests.get(base_url, params=params, headers=headers)
        response.raise_for_status()
        decoded_response = response.json()

        if 'error' in decoded_response:
            raise requests.exceptions.HTTPError(decoded_response['error'])

        vacancies.extend(decoded_response.get("objects", []))

        print(f"Загружено {len(decoded_response.get('objects', []))} вакансий для {lang} (страница {params['page'] + 1})")

        if not decoded_response.get("more"):
            break

        params["page"] += 1
        time.sleep(0.5)

    return vacancies, decoded_response.get("total", 0)


def get_language_salary_stats(languages, site, area=1, headers=None):
    stats = {}

    for lang in languages:
        print(f"Обрабатываю {lang} на {site}...")

        if site == 'hh':
            vacancies, total_vacancies = fetch_hh_vacancies(lang, area)
        elif site == 'sj':
            vacancies, total_vacancies = fetch_sj_vacancies(lang, area, headers)
        else:
            continue

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