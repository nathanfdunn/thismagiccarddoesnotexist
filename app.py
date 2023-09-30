from flask import Flask, make_response, render_template, request, Response, stream_with_context
import json
import card_utils
import random
app = Flask(__name__)
import base64


from mtg_card_table import MTGCard


@app.route('/card/<guid>', methods=['GET', 'DELETE'])
def card(guid):
    card = MTGCard.get(guid)
    can_delete = request.cookies.get('user_id') and request.cookies.get('user_id') == card.creator_id
    if app.debug:
        can_delete = True
    
    # can_delete = True
    if request.method == 'DELETE' and can_delete:
        card.is_deleted = True
        card.save()
        return Response('Card deleted successfully', status=200)
    
    return render_template('card.html', card=card, active_page='card', can_delete=can_delete)

@app.route('/card/<guid>/edit', methods=['GET'])
def edit(guid):
    card = MTGCard.get(guid)
    # TODO what if there are non ascii chars??
    # b64payload = base64.b64encode(json.dumps(card.json_values).encode('UTF-8')).decode('ASCII')
    return render_template('create_card.html', active_page='edit', existing_card=(card.json_values))

@app.route('/card/<guid>/copy', methods=['GET'])
def copy(guid):
    card = MTGCard.get(guid)
    # TODO what if there are non ascii chars??
    # b64payload = base64.b64encode(json.dumps(card.json_values).encode('UTF-8')).decode('ASCII')
    return render_template('create_card.html', active_page='copy', existing_card=(card.json_values))

import uuid


@app.route('/', methods=['GET'])
def index():
    last_ten_cards = [card for card in MTGCard.get_latest(n=300) if card.should_show]
    print('heres what we got ', last_ten_cards)
    user_id = request.cookies.get('user_id') or str(uuid.uuid4())
    response = make_response(render_template('index.html', cards=last_ten_cards, active_page='home'))
    response.set_cookie('user_id', user_id)
    return response

@app.route('/about', methods=['GET'])
def about():
    return render_template('about.html', active_page='about')


#     description = request.json.get('card-description')
#     print('editing card', description)
#     # Add your card editing logic here
#     return Response('Card edited successfully', status=200)

import time
@app.route('/create', methods=['GET', 'POST'])
def create():
    if request.method == 'POST':
        description = request.json.get('card-description')
        base = request.json.get('base')
        mode = request.json.get('mode')
        print('generating new card', description)

        user_id = request.cookies.get('user_id')

        raw_generator = card_utils.generate_card_final(description, base, user_id, mode)
        # if app.debug:
        #     def debug_generator():
        #         time.sleep(.5)
        #         card = MTGCard.init_new_row(description, None, None)
        #         yield card, 'Skeleton'
        #         time.sleep(.5)
        #         card.card_name = str(uuid.uuid4())
        #         card.rules_text = description
        #         card.save()
        #         yield card, 'Outlined'
        #         time.sleep(.5)
        #         card.art_url = 'http://res.cloudinary.com/hkzbfes0n/image/upload/v1695476355/ykgbgqbyr13cfecgrr0k.jpg'
        #         card.save()
        #         yield card, 'Artwork'
        #         time.sleep(.5)
        #         card.final_rendered_url = 'http://res.cloudinary.com/hkzbfes0n/image/upload/v1695476355/ykgbgqbyr13cfecgrr0k.jpg'
        #         card.is_finished_generating = True
        #         card.save()
        #         yield card, 'Rendered'
        #         time.sleep(.5)
        #     raw_generator = debug_generator()

        

        def generator():
            try:
                for card, status in raw_generator:
                    yield json.dumps({'status': status, 'card': card.json_values}) + '\n\n'
            except Exception as e:
                import traceback
                error = traceback.format_exc() if os.environ.get('IS_DEBUG') else str(e)
                yield json.dumps({'status': 'Error', 'error': error}) + '\n\n'

        return Response(stream_with_context(generator()), content_type='text/event-stream')

        # image_url = card.final_rendered_url
       
        # return render_template('card.html', image_url=image_url)

    else:
        # example=random.choice(ideas)
        return render_template('create_card.html', active_page='create')
        # return f'''
        #     <form method="POST">
        #         <textarea id="card-description" name="card-description" cols="60" rows="4"
        #             >{example}</textarea>
        #         <br>
        #         <input type="submit">
        #     </form>
        # '''

if __name__ == '__main__':
    import os
    os.environ['IS_DEBUG'] = 'TRUE'
    app.run(debug=True, threaded=True)
