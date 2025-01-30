import os
import time
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


def fetch_vacancies(lang, area=1, max_pages=20):
    vacancies = []
    page = 0

    while page < max_pages:
        url = f"https://api.hh.ru/vacancies?text={lang}&area={area}&per_page=100&page={page}"
        response = requests.get(url).json()

        items = response.get("items", [])
        vacancies.extend(items)

        print(f"Загружено {len(items)} вакансий для {lang} (страница {page + 1})")

        if not items:
            break

        page += 1
        time.sleep(0.5)

    return vacancies


def fetch_sj_vacancies(lang, area=1, max_pages=20):
    vacancies = []
    page = 0

    while page < max_pages:
        url = f"https://api.superjob.ru/2.0/vacancies/?keyword={lang}&town={area}&page={page}"
        headers = {'X-Api-App-Id': os.getenv("SUPERJOB_API_KEY")}  # Ключ из переменной окружения
        response = requests.get(url, headers=headers).json()

        items = response.get("objects", [])
        vacancies.extend(items)

        print(f"Загружено {len(items)} вакансий для {lang} (страница {page + 1})")

        if not items:
            break

        page += 1
        time.sleep(0.5)

    return vacancies


def get_language_salary_stats(languages, area=1, site='hh', max_pages=20):
    stats = {}

    for lang in languages:
        print(f"Обрабатываю {lang}...")
        if site == 'hh':
            vacancies = fetch_vacancies(lang, area, max_pages)
        elif site == 'sj':
            vacancies = fetch_sj_vacancies(lang, area, max_pages)

        vacancies_found = len(vacancies)
        salaries = [predict_rub_salary(vac) for vac in vacancies]
        salaries = [int(s) for s in salaries if s is not None]

        vacancies_processed = len(salaries)
        average_salary = int(sum(salaries) / vacancies_processed) if vacancies_processed > 0 else None

        stats[lang] = {
            "vacancies_found": vacancies_found,
            "vacancies_processed": vacancies_processed,
            "average_salary": average_salary
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