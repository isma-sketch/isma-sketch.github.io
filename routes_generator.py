import json
from database import get_all_cards, init_db

def generate_routes(output='routes.json'):
    init_db()
    routes = {}
    for row in get_all_cards():
        card_id, card_type, group_id, data, locked, created_at = row
        routes[card_id] = {
            'card_type': card_type,
            'group_id': group_id,
            'data': json.loads(data),
            'locked': bool(locked),
            'created_at': created_at
        }
    with open(output, 'w', encoding='utf-8') as f:
        json.dump(routes, f, ensure_ascii=False, indent=2)
    return output
