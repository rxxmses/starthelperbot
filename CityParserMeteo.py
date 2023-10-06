from bs4 import BeautifulSoup

# Открываем файл для чтения
with open("meteo.html", "r", encoding="utf-8") as file:
    content = file.read()

# Создаем объект BeautifulSoup для парсинга
soup = BeautifulSoup(content, "html.parser")

meteo = soup.find("div", class_="meteo-city-regions")
p_meteos = meteo.find_all("div", class_="meteo-city-region")

if p_meteos:
    for index, p_meteo in enumerate(p_meteos, start=1):
        for indexs, p in enumerate(p_meteo, start=1):
            extracted_text = p.get_text()
            ids = p.find("input", {"name": "city"})
            if ids:
                print(ids.get("value"), p.get_text())
            else:
                print(f"\n{extracted_text}\n")