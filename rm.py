
import argparse
import csv
import json
import random

import tmb

class CharacterBD:

    def __init__(self, db_file):

        with open(db_file, newline='') as csvfile:
            reader = csv.DictReader(csvfile, fieldnames=["name", "class", "spec", "tank", "healer", "dps", "r1", "r2", "r3", "discord_id"])
            self.chars = {}

            # Skip 4 header rows
            for i in range(0, 4):
                reader.__next__()

            for row in reader:
                if row["name"]:
                    
                    char = {"name" : row["name"], "class" : row["class"], "discord_id" : row["discord_id"]}

                    for role in ["tank", "healer", "dps"]:
                        char[role] = True if row[role] == "MS" or row[role] == "OS" else False

                    self.chars[row["name"]] = char
                else:
                    return
                
    def __getitem__(self, key):
        return self.chars[key]
    
    def items(self):
        return self.chars.items()
                
    def FindCharacters(self, discord_id):
        chars = {}
        for _, char in self.chars.items():
            if char["discord_id"] == discord_id:
                chars[char["name"]] = char

        return chars
    
    def FindAlts(self, char_name):
        discord_id = self.chars[char_name]["discord_id"]
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
            p = {"discord_id" : player['userid'], "signup" : player["class"]}
            self.players[p["discord_id"]] = p

            if p["signup"] != "Absence":
                self.active_players[p["discord_id"]] = p
    
    def CanPlayerRaid(self, discord_id):
        return discord_id in self.active_players
    
    def GetActiveCharsByRole(self, role):
        chars = {}
        for _, c in self.charDB.chars.items():
            if self.CanPlayerRaid(c["discord_id"]) and c[role]:
                chars[c["name"]] = c
        return chars
    
    def GetActiveChars(self):
        chars = {}
        for _, c in self.charDB.chars.items():
            if self.CanRaid(c["discord_id"]):
                chars[c["name"]] = c
        return chars
    
    def GetActivePlayers(self):
        return self.active_players
    
class Roster:

    def __init__(self, signup : Signup, char_db, tmb, id):
        self.roster = {}

        self.signup = signup
        self.chars = char_db
        self.tmb = tmb
        self.id = id

    def __getitem__(self, key):
        return self.roster[key]
    
    def __contains__(self, key):
        return key in self.roster
    
    def items(self):
        return self.roster.items()
    
    def __str__(self):
        return str(self.roster)
    
    def RosterChar(self, char_name, role):
        self.roster[char_name] = role
    
    def ContainsAlt(self, char_name):
        discord_id = self.chars[char_name]['discord_id']
        res, c = self.ContainsPlayer(discord_id)
        return res and c['name'] != char_name

    def ContainsPlayer(self, discord_id):
        for c, r in self.roster.items():
            if self.chars[c]['discord_id'] == discord_id:
                return True, c
        return False

    def IsValid(self):
        return len(self.roster) == 10

class RosterMaster:

    def __init__(self, charDB_file, tmb_file, contested_items_file, r1_file, r2_file, r3_file):
        self.chars = CharacterBD(charDB_file)
        self.contested_items = json.load(open(contested_items_file))
        self.tmb = tmb.ReadDataFromJson(tmb.GetDataFromFile(tmb_file))
        self.s1 = Signup(self.chars, r1_file)
        self.s2 = Signup(self.chars, r2_file)
        self.s3 = Signup(self.chars, r3_file)
        
    def GenerateRandomRosters(self):

        rosters = [Roster(self.s1, self.chars, self.tmb, 0), Roster(self.s2, self.chars, self.tmb, 1), Roster(self.s3, self.chars, self.tmb, 2)]
        signups = [self.s1, self.s2, self.s3]

        self.AssignByRole(rosters, "tank", 2)
        self.AssignByRole(rosters, "healer", 2)
        self.AssignByRole(rosters, "dps", 6)

        return rosters

    def AssignByRole(self, rosters: "list[Roster]", role: str, min_amount: int):

        # Start with roster with the fewer signups
        rosters.sort(key=lambda x : len(x.signup.GetActivePlayers()))

        for r in rosters:
            chars = r.signup.GetActiveCharsByRole(role)
            chars_copy = chars.copy()

            # Remove players already rostered
            for p in chars_copy:
                # Remove character if in other rosters
                for roster in rosters:
                    if p in roster and p in chars:
                        chars.pop(p)

                # Remove char from this roster if in another char already
                if r.ContainsPlayer(self.chars[p]['discord_id']) and p in chars:
                    chars.pop(p)
            
            # Assign n of this role to this roster
            for j in range(0, min_amount):
                char_list = [t for t in chars]
                if len(char_list) > 0:
                    char_index = random.randrange(0, len(char_list))
                    char = char_list[char_index]
                    chars.pop(char)

                    r.RosterChar(char, role)

                    alts = self.chars.FindAlts(char)
                    for alt in alts:
                        if alt in chars:
                            chars.pop(alt)

    def CalcViabilityScore(self, rosters: "list[Roster]"):
        score = 0

        for i in range(0, len(rosters)):
            r = rosters[i]
            if self.CheckDoubleAlt(r):
                print("Double alt found in roster ", i)

        return score

    def CheckDoubleAlt(self, roster: Roster):
        
        for c, _  in roster.items():
            discord_id = self.chars[c]["discord_id"]
            for c2, _  in roster.items():
                if c != c2 and self.chars[c2]["discord_id"] == discord_id:
                    return True
                
        return False

    def GetItemPrio(self, char_name, item_id):
        for _, char in self.tmb.items():
            if char.data["name"] == char_name and item_id in char.wishlist and not char.wishlist[item_id]["is_received"]:
                return char.wishlist[item_id]["order"]
        return -1
    
    def GetItemUsers(self, item_id):
        users = []
        for _, c in self.chars.items():
            if self.GetItemPrio(c["name"], item_id) > 0:
                users.append(c)

        return users

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

    for i in range(0, 100):
        rosters = rm.GenerateRandomRosters()
        if rosters:

            for roster in rosters:
                print(roster)

            score = rm.CalcViabilityScore(rosters)
            print("Rosters score:", score)

if __name__ == "__main__":
    main()