import csv
import json

class WoW:

    roles = ["tank", "healer", "dps"]

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

                    for role in WoW.roles:
                        char[role] = True if row[role] == "MS" or row[role] == "OS" else False

                        if row[role] == "MS":
                            char["MS"] = role

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
    
    def print(self):
        print("{0:<14s}Roster {1}".format("", self.id))
        self.PrintRole("dps")
        self.PrintRole("healer")
        self.PrintRole("tank")

    def PrintRole(self, role):
        print("{0:<16s}{1}".format("", role))
        role_chars = self.GetCharsByRole(role)
        for i in range(0, len(role_chars), 2):
            char = role_chars[i]
            print("{0:<16s}\t".format(char), end='')
            if i + 1 <= len(role_chars):
                char2 = role_chars[i + 1]
                print("{0:<16s}".format(char2), end='')
            print()

    def GetCharsByRole(self, role):
        chars = []
        for c, r in self.roster.items():
            if r == role:
                chars.append(c)
        return chars
    
    def RosterChar(self, char_name, role):

        if role in WoW.roles:
            self.roster[char_name] = role
        else:
            print("Error: Role {} doesn't exist".format(role))
    
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
