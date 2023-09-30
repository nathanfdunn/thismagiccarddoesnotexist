from typing import Literal
import requests as r
from mtg_card_table import MTGCard

import os
import pickle

def get_login_cookies():
    if os.getenv('IS_DEBUG'):
        try:
            print("Attempting to read login cookies from file...")
            with open('login_cookies.pkl', 'rb') as f:
                cookies = pickle.load(f)
            print("Successfully read login cookies from file.")
            return cookies
        except FileNotFoundError:
            print("File not found. Unable to read login cookies from file.")

    print("Attempting to get login cookies from website...")
    login_get = r.get('https://mtg.design/login')
    token = login_get.content.decode('utf-8').split('name="_token"')[1].split('"')[1].split('"')[0]

    login = r.post(
        'https://mtg.design/login',
        params = {
            '_token': token,
            'email': 'nathanfdunn@gmail.com',
            'password': '8@2jRCyTfJdw9cJ',
            'remember': 'off'
        },
        cookies=login_get.cookies
    )
    print("Successfully got login cookies from website.")
    
    if os.getenv('IS_DEBUG'):
        print("Attempting to write login cookies to file...")
        with open('login_cookies.pkl', 'wb') as f:
            pickle.dump(login.cookies, f)
        print("Successfully wrote login cookies to file.")

    return login.cookies

def test():
    res = render_mtg_card(
        temp_dir='/Users/nathandunn/Projects/this-magic-card-does-not-exist/images',
        card=MTGCard(
            card_name='Oozemeister',
            mana_cost='{0}',
            rules_text='1: say hello',
            card_type='Planeswalker',
            flavor_text='Yummy...',
            rarity='Rare',
            power=1,
            toughness=1,
            explanation='none',
            art_url=''
        )
    )
    # with open('/Users/nathandunn/Projects/this-magic-card-does-not-exist/images/test.png', 'wb') as file:
    #     file.write(res)


# TODO could be more advanced about hybrid accents
def get_color_ident(mana_cost):
    ret = 'C'
    for color in 'UWGRB':
        if color.lower() in mana_cost.lower():
            if ret != 'C':
                ret = 'Gld'
            else:
                ret = color
    return ret, ret

def render_mtg_card(
        temp_dir: str,
        card: MTGCard
        # card_name: str = 'Missing', 
        # mana_cost: str = '',
        # rules_text: str = '',
        # card_type: Literal['Artifact', 'Creature', 'Land', "Instant", 'Sorcery', 'Enchantment', 'Planeswalker'] = 'Artifact',
        # flavor_text: str = '',
        # rarity: Literal['Common', 'Uncommon', 'Rare', 'Mythic Rare'] = 'Common',
        # power: int = 0,
        # toughness: int = 0,
        # # art_description: str = '',
        # explanation: str = '',
        # art_url: str = '',
) -> str:
    print('rendering', card.card_name)

    # TODO could take into account color indicator, etc.
    template, accent = get_color_ident(card.mana_cost)

    pw_text2, pw_text3 = '', ''
    if card.card_type == 'Planeswalker':
        abilities = card.rules_text.split('\n', 2)
        while len(abilities) < 3:
            abilities.append('')
        for i, ability in enumerate(list(abilities)):
            if ability and ': ' not in ability:
                # abilities[i] = ': ' + ability
                ability = ': ' + ability
            if ability.startswith('+'):
                ability = ability.removeprefix('+')
            
            abilities[i] = ability
        card.rules_text, pw_text2, pw_text3 = abilities

    resp = r.get(
        'https://mtg.design/render',
        cookies = get_login_cookies(),
        params = {
            'card-number': '1',
            'card-total': '1',
            'card-set': 'SET',
            'language': 'EN',
            'card-title': card.card_name,
            'type': card.card_type,
            'text-size': '38',
            'rarity': card.rarity[0],    # TODO support land and stuff
            'artist': 'Bing Image Creator + Dalle-2',
            'power': str(card.power),
            'toughness': str(card.toughness),
            # 'loyalty': '8',
            'mana-cost': card.mana_cost,
            'artwork': card.art_url,
            'designer': 'thismagiccarddoesnotexist.com',
            'card-border': 'black',
            # 'land-overlay': 'C',
            'watermark': '0',
            'card-layout': 'regular',
            'set-symbol': '0',
            'pw-size': '3',
            'rules-text': card.rules_text,
            'pw-text2': pw_text2,
            'pw-text3': pw_text3,

            'flavor-text': card.flavor_text,
            'card-template': template,
            'card-accent': accent,        # RG works, but not GR..probs based on left and right sides of the card
            'stars': '0',
            'edit': 'xmqf05',
        }
    )

    if resp.status_code == 200:
        print('success??')
        # with open('response_body.jpeg', 'wb') as f:
        #     f.write(resp.content)
        render_save_loc = temp_dir + '/rendered_card.jpeg'
        print('saving render to', render_save_loc)
        with open(render_save_loc, 'wb') as file:
            file.write(resp.content)
        return render_save_loc
    else:
        print("Failed to retrieve image. Status code:", resp.status_code)
        print("Response headers:", resp.headers)
        with open('response_content.html', 'w') as file:
            file.write(resp.content.decode())
        raise Exception('Failed to render card')

if __name__ == '__main__':
    os.environ['IS_DEBUG'] = 'true'
    test()
