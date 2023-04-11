
import argparse
import csv
import json
import tmb

class CharacterBD:

    def __init__(self, db_file):

        with open(db_file, newline='') as csvfile:
            reader = csv.DictReader(csvfile, fieldnames=["name", "class", "spec", "tank", "healer", "dps", "r1", "r2", "r3", "discord-id"])
            self.chars = {}

            # Skip 4 header rows
            for i in range(0, 4):
                reader.__next__()

            for row in reader:
                if row["name"]:
                    
                    char = {"name" : row["name"], "class" : row["class"], "discord-id" : row["discord-id"]}

                    for role in ["tank", "healer", "dps"]:
                        char[role] = True if row[role] == "MS" or row[role] == "OS" else False

                    self.chars[row["name"]] = char
                else:
                    return
                
    def __getitem__(self, key):
        return self.chars[key]
                
    def FindCharacters(self, discord_id):
        chars = {}
        for _, char in self.chars.items():
            if char["discord-id"] == discord_id:
                chars[char["name"]] = char

        return chars
    
    def FindAlts(self, char_name):
        discord_id = self.chars[char_name]["discord-id"]
        chars = self.FindCharacters(discord_id)
        chars.pop(char_name)
        return chars
    
class Signup:

    def __init__(self, charDB, file):
        self.charDB = charDB

        data = json.load(open(file))
        self.date = data["date"]
        self.time = data["time"]
        self.title = data["title"]

        self.players = {}
        self.active_players = {}
        for player in data["signups"]:
            p = {"discord-id" : player['userid'], "signup" : player["class"]}
            self.players[p["discord-id"]] = p

            if p["signup"] != "Absence":
                self.active_players[p["discord-id"]] = p
    
    def CanRaid(self, discord_id):
        return discord_id in self.active_players
    
    def GetActiveByRole(self, role):
        chars = {}
        for _, c in self.charDB.chars.items():
            if self.CanRaid(c["discord-id"]) and c[role]:
                chars[c["name"]] = c
        return chars
    

class RosterMaster:

    def __init__(self, charDB_file, tmb_file, contested_items_file, r1_file, r2_file, r3_file):
        self.chars = CharacterBD(charDB_file)
        self.contested_items = json.load(open(contested_items_file))
        self.tmb = tmb.ReadDataFromJson(tmb.GetDataFromFile(tmb_file))
        self.s1 = Signup(self.chars, r1_file)
        self.s2 = Signup(self.chars, r2_file)
        self.s3 = Signup(self.chars, r3_file)
        
    def GenerateRosters(self):
        char = self.chars["Ragnaorc"]
        print(char["name"])
        print(self.s1.GetActiveByRole("tank"))
        print(len(self.s1.GetActiveByRole("tank")))
        print(self.contested_items)

def main():

    parser = argparse.ArgumentParser(prog='RosterMaster', description='Creates a somewhat viable roster taking loot into account', epilog='Call with --help to find a list of available commands')
    parser.add_argument("--characters-db", default="characters-db.csv")
    parser.add_argument("--tmb-file", default="character-json.json")
    parser.add_argument("--r1", default="r1.json")
    parser.add_argument("--r2", default="r2.json")
    parser.add_argument("--r3", default="r3.json")
    parser.add_argument("--contested-items", default="contested-items.json")
    args = parser.parse_args()

    rm = RosterMaster(args.characters_db, args.tmb_file, args.contested_items, args.r1, args.r2, args.r3)
    rm.GenerateRosters()

if __name__ == "__main__":
    main()