import requests
from bs4 import BeautifulSoup
from fpdf import FPDF
import os
import asyncio
from crawl4ai import *


def create_pokemon_directory():
    if not os.path.exists('pokemon_pdfs'):
        os.makedirs('pokemon_pdfs')


def get_pokemon_links():
    url = 'https://unboundwiki.com/pokemon/'
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    pokemon_links = []

    # Find all Pokemon links
    for link in soup.find_all('a'):
        href = link.get('href', '')
        if '/pokemon/' in href and href != '/pokemon/' and href != 'https://unboundwiki.com/pokemon/':
            pokemon_links.append(href)

    return pokemon_links

async def extract_pokemon_info_async(url, pokemon_name):
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url=url
        )
        print(result.markdown)
        create_markdown(pokemon_name, result.markdown)


def extract_pokemon_info(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    # Get Pokemon name from URL
    pokemon_name = url.split('/')

    try:
        # Get infobox table
        infobox = soup.find('table', {'class': 'dextable-infobox'})
        if not infobox:
            print(f"Warning: Could not find infobox for {pokemon_name}")
            infobox = soup.find('table')  # Try to find any table as fallback

        # Extract abilities
        abilities = []
        ability_rows = infobox.find_all('tr')
        for row in ability_rows:
            th = row.find('th')
            if th and 'Abilities' in th.text:
                ability_name = row.find('td', {'class': 'thh3'}).text
                ability_desc = row.find_all('td')[1].text
                abilities.append({'name': ability_name, 'description': ability_desc})
                if row.find_next_sibling('tr').find('th') is None:  # Check for second ability
                    ability_name = row.find_next_sibling('tr').find('td', {'class': 'thh3'}).text
                    ability_desc = row.find_next_sibling('tr').find_all('td')[1].text
                    abilities.append({'name': ability_name, 'description': ability_desc})

        # Extract Wild Held Items
        held_items = None
        for row in ability_rows:
            th = row.find('th')
            if th and 'Wild Held Items' in th.text:
                held_items = row.find('td').text

        # Extract Evolution Line with multiple fallback options
        evolution_line = []
        evo_header = soup.find('h2', string='Evolution Line') or soup.find('h2', string=lambda x: x and 'Evolution' in x)

        if evo_header:
            # Try multiple ways to find the evolution table
            evo_table = (evo_header.find_next('table') or 
                        soup.find('table', {'class': 'table'}) or 
                        soup.find('table', {'class': 'grey'}) or
                        soup.find('table'))

            if evo_table:
                tbody = evo_table.find('tbody') or evo_table
                rows = tbody.find_all('tr')

                for row in rows:
                    cells = row.find_all('td')
                    if cells and len(cells) >= 2:
                        pokemon_evo_name = cells[1].text.strip()
                        condition = cells[2].text.strip() if len(cells) >= 3 else "Unknown"
                        if pokemon_evo_name:  # Only add if we found a Pokemon name
                            evo_data = {
                                'pokemon': pokemon_evo_name,
                                'condition': condition
                            }
                            evolution_line.append(evo_data)

        if not evolution_line:
            print(f"Warning: Could not find evolution line for {pokemon_name}")
            evolution_line.append({
                'pokemon': pokemon_name,
                'condition': 'Base form'
            })


        # Extract Moveset (Level Up)
        moveset = []
        level_up_table = soup.find('h2', string='Moveset (Level Up)').find_next('table')
        for row in level_up_table.find('tbody').find_all('tr'):
            cells = row.find_all('td')
            if cells:
                move_data = {
                    'level': cells[0].text.strip(),
                    'move': cells[1].text.strip(),
                    'type': cells[2].text.strip(),
                    'category': cells[3].find('img')['alt'],
                    'power': cells[4].text.strip(),
                    'accuracy': cells[5].text.strip(),
                    'pp': cells[6].text.strip()
                }
                moveset.append(move_data)

        # Extract TM/HM Moves
        tm_moves = []
        tm_table = soup.find('h2', string='Learnset (TM/HM)').find_next('table')
        for row in tm_table.find('tbody').find_all('tr'):
            cells = row.find_all('td')
            if cells:
                move_data = {
                    'move': cells[0].text.strip(),
                    'type': cells[1].text.strip(),
                    'category': cells[2].find('img')['alt'],
                    'power': cells[3].text.strip(),
                    'accuracy': cells[4].text.strip(),
                    'pp': cells[5].text.strip()
                }
                tm_moves.append(move_data)

        # Extract Move Tutor Moves
        tutor_moves = []
        tutor_table = soup.find('h2', string='Move Tutor Moves').find_next('table')
        for row in tutor_table.find('tbody').find_all('tr'):
            cells = row.find_all('td')
            if cells:
                move_data = {
                    'move': cells[0].text.strip(),
                    'type': cells[1].text.strip(),
                    'category': cells[2].find('img')['alt'],
                    'power': cells[3].text.strip(),
                    'accuracy': cells[4].text.strip(),
                    'pp': cells[5].text.strip()
                }
                tutor_moves.append(move_data)

        # Extract Egg Moves
        egg_moves = []
        egg_table = soup.find('h2', string='Egg Moves').find_next('table')
        for row in egg_table.find('tbody').find_all('tr'):
            cells = row.find_all('td')
            if cells:
                move_data = {
                    'move': cells[0].text.strip(),
                    'type': cells[1].text.strip(),
                    'category': cells[2].find('img')['alt'],
                    'power': cells[3].text.strip(),
                    'accuracy': cells[4].text.strip(),
                    'pp': cells[5].text.strip()
                }
                egg_moves.append(move_data)
        
        print('pokemon_name', pokemon_name)

        return {
            'name': pokemon_name[4],
            'url': url,
            'abilities': abilities,
            'wild_held_items': held_items,
            'evolution_line': evolution_line,
            'moveset': moveset,
            'tm_moves': tm_moves,
            'tutor_moves': tutor_moves,
            'egg_moves': egg_moves
        }
    except Exception as e:
        print(f"Error extracting pokemon info for {url}: {e}")
        create_html(pokemon_name[4], str(soup))
        return None

def create_markdown(pokemon_name, content):
    if not os.path.exists('crawl_result'):
        os.makedirs('crawl_result')
    f = open('crawl_result/'+pokemon_name+'.md', "w")
    f.write(str(content))
    f.close()

def create_html(pokemon_name, content):
    if not os.path.exists('pokemon_html'):
        os.makedirs('pokemon_html')
    f = open('pokemon_html/'+pokemon_name+'.html', "w")
    f.write(str(content))
    f.close()

def create_json(pokemon_info):
    import json
    
    if not os.path.exists('pokemon_json'):
        os.makedirs('pokemon_json')
        
    filename = f"pokemon_json/{pokemon_info['name']}.json"
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(pokemon_info, f, indent=2, ensure_ascii=False)
    return filename
    print(pokemon_name)
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, pokemon_name, ln=True)

    pdf.set_font('Arial', '', 12)
    pdf.cell(0, 10, 'Abilities', ln=True)
    for ability in abilities:
        pdf.cell(0, 10, ability['name'], ln=True)
        pdf.cell(0, 10, ability['description'], ln=True)
    pdf.cell(0, 10, 'Wild Held Items', ln=True)
    pdf.cell(0, 10, held_items, ln=True)
    pdf.cell(0, 10, 'Evolution Line', ln=True)
    for evo in evolution_line:
        pdf.cell(0, 10, evo['pokemon'], ln=True)
        pdf.cell(0, 10, evo['condition'], ln=True)
    # pdf.write(5, content)
    # Split content into lines and add to PDF
    # for line in content.split('\n'):
    #     if line.strip():
    #         pdf.multi_cell(0, 10, line.encode('latin-1', 'replace').decode('latin-1'))

    filename = f"pokemon_pdfs/{pokemon_name}.pdf"
    pdf.output(filename)
    return filename


def main():
    print("Starting Pokemon data crawler...")
    create_pokemon_directory()

    pokemon_links = get_pokemon_links()
    total = len(pokemon_links)

    print(f"Found {total} Pokemon to process")

    for i, link in enumerate(pokemon_links, 1):
        print(f"{i}. {link}")
        try:
            pokemon_name = link.split('/')[4]
            asyncio.run(extract_pokemon_info_async(link, pokemon_name))
            print(f"[{i}/{total}] Created markdown for {pokemon_name}")
        except Exception as e:
            print(f"Error processing {link}: {str(e)}")

    print("\nAll Pokemon markdown have been generated in the 'crawl_result' directory!")


if __name__ == "__main__":
    main()
