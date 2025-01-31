import os
import time
import urllib.parse
import requests
from dotenv import load_dotenv
from terminaltables import AsciiTable


def predict_rub_salary(vacancy):
    salary = vacancy.get("salary")
    if not salary or salary.get("currency") != "RUR":
        return None

    salary_from = salary.get("from")
    salary_to = salary.get("to")

    if salary_from and salary_to:
        return (salary_from + salary_to) / 2
    elif salary_from:
        return salary_from * 1.2
    elif salary_to:
        return salary_to * 0.8
    return None


def fetch_hh_vacancies(lang, area=1, max_pages=20):
    vacancies = []
    base_url = "https://api.hh.ru/vacancies"

    for page in range(max_pages):
        params = {
            "text": lang,
            "area": area,
            "per_page": 100,
            "page": page
        }
        url = f"{base_url}?{urllib.parse.urlencode(params)}"
        response = requests.get(url).json()

        items = response.get("items", [])
        vacancies.extend(items)

        print(f"Загружено {len(items)} вакансий для {lang} (страница {page + 1})")

        if not items:
            break

        time.sleep(0.5)

    return vacancies


def fetch_sj_vacancies(lang, area=1, max_pages=20):
    vacancies = []
    base_url = "https://api.superjob.ru/2.0/vacancies/"
    headers = {'X-Api-App-Id': os.getenv("SUPERJOB_API_KEY")}

    for page in range(max_pages):
        params = {
            "keyword": lang,
            "town": area,
            "page": page
        }
        url = f"{base_url}?{urllib.parse.urlencode(params)}"
        response = requests.get(url, headers=headers).json()

        items = response.get("objects", [])
        vacancies.extend(items)

        print(f"Загружено {len(items)} вакансий для {lang} (страница {page + 1})")

        if not items:
            break

        time.sleep(0.5)

    return vacancies


def fetch_all_vacancies(lang, site, area=1, max_pages=20):
    if site == 'hh':
        return fetch_hh_vacancies(lang, area, max_pages)
    elif site == 'sj':
        return fetch_sj_vacancies(lang, area, max_pages)
    return []


def get_language_salary_stats(languages, site, area=1, max_pages=20):
    stats = {}

    for lang in languages:
        print(f"Обрабатываю {lang} на {site}...")
        vacancies = fetch_all_vacancies(lang, site, area, max_pages)

        salaries = [predict_rub_salary(vac) for vac in vacancies]
        salaries = [int(s) for s in salaries if s is not None]
        
        stats[lang] = {
            "vacancies_found": len(vacancies),
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

    languages = ["Python", "Java", "Javascript", "C++", "C#", "Go", "Swift", "Kotlin", "Ruby", "PHP"]

    hh_stats = get_language_salary_stats(languages, site='hh', max_pages=20)
    sj_stats = get_language_salary_stats(languages, site='sj', max_pages=20)

    print_table(hh_stats, "HeadHunter")
    print_table(sj_stats, "SuperJob")


if __name__ == "__main__":
    main()
