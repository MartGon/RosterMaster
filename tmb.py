import json

class Character:

    def __init__(self, char_json):
        self.name = char_json["name"]
        self.recv = Character.extract_items_info(char_json["received"], ["received_at", "is_offspec", "officer_note"])
        self.wishlist = Character.extract_items_info(char_json["wishlist"], ["is_received", "order"])
        self.prios = Character.extract_items_info(char_json["prios"], ["is_received", "order"])

    def extract_items_info(recv_json, pivot_keys):
        recv = {}
        for i in recv_json:
            item = {"name" : i["name"], "id" : i["id"]}
            for pk in pivot_keys:
                if pk in i["pivot"]:
                    item[pk] = i["pivot"][pk]

            recv[i["id"]] = item
        return recv

def ReadDataFromJson(json_data):

    characters = {}
    items = {}

    res = json.loads(json_data)

    for character in res:
        characters[character["name"]] = (Character(character))
    
    calculate_update_prios(characters)

    return characters, items

def GetDataFromFile(json_path):
    return open(json_path).read()

def calculate_update_prios(characters):
    
    for name, char in characters.items():
        for itemId, item in char.prios.items():
            item["updated_prio"] = get_updated_prio(characters, itemId, char)

def get_updated_prio(characters, itemId, char):
    prio = 0
    if not itemId in char.prios or itemId in char.recv:
        return prio
    
    updated_prio = 1
    checked_prio = 1
    while char.prios[itemId]['order'] > checked_prio:

        for name, c in characters.items():
            if itemId in c.prios:
                c_prio = c.prios[itemId]["order"]
                if checked_prio == c_prio and c != char:
                    if not itemId in c.recv:
                        updated_prio = updated_prio + 1
                    checked_prio = checked_prio + 1

    return updated_prio