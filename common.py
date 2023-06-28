import csv
import json

class WoW:

    roles = ["tank", "healer", "dps"]

class CharacterBD:

    def __init__(self, db_file):

        with open(db_file, newline='') as csvfile:
            reader = csv.DictReader(csvfile, fieldnames=["name", "class", "spec", "offspec", "tank", "healer", "dps", "r1", "r2", "r3", "is_main", "has_quit", "discord_user", "discord_id"])
            self.chars = {}

            # Skip 4 header rows
            for i in range(0, 4):
                reader.__next__()

            for row in reader:
                if row["name"]:
                    
                    char = {"name" : row["name"].strip(), "class" : row["class"], "spec" : row["spec"], "offspec" : row["offspec"], "has_quit" : True if row["has_quit"] == 'TRUE' else False,
                    "is_main" : True if row["is_main"] == 'TRUE' else False, "discord_user" : row["discord_user"].strip(), "discord_id" : row["discord_id"]}

                    for role in WoW.roles:
                        char[role] = True if row[role] == "MS" or row[role] == "OS" else False

                        if row[role] == "MS":
                            char["MS"] = role
                        elif row[role] == "OS":
                            char["OS"] = role

                    self.chars[row["name"].strip()] = char
                else:
                    return
                
    def __getitem__(self, key: str) -> dict:
        return self.chars[key]
    
    def __contains__(self, key: str):
        return key in self.chars
    
    def items(self):
        return self.chars.items()
                
    def FindCharacters(self, discord_id: str):
        chars = {}
        for _, char in self.chars.items():
            if char["discord_id"] == discord_id:
                chars[char["name"]] = char

        return chars
    
    def GetDiscordId(self, char_name: str):
        return self.chars[char_name]['discord_id']
    
    def FindAlts(self, char_name: str):
        discord_id = self.chars[char_name]["discord_id"]
        chars = self.FindCharacters(discord_id)
        chars.pop(char_name)
        return chars
    
    def GetPlayers(self):
        players = {}
        for char_name, char in self.chars.items():
            players[char['discord_id']] = char_name
        return players
    
    def GetMain(self, discord_id: str):
        for _, char in self.chars.items():
            if char["discord_id"] == discord_id and char["is_main"]:
                return char["name"]
        return None
    
    def GetMainByAlt(self, char_name: str):
        discord_id = self.chars[char_name]["discord_id"]
        return self.GetMain(discord_id)
    
class Signup:

    def __init__(self, charDB, file):
        self.charDB = charDB

        data = json.load(open(file, encoding='utf8'))
        self.date = data["date"]
        self.time = data["time"]
        self.title = data["title"]

        self.players = {}
        self.active_players = {}
        for player in data["signups"]:
            p = {"discord_id" : player['userid'], "signup" : player["class"], "spec" : player["spec"]}
            self.players[p["discord_id"]] = p

            if p["signup"] != "Absence":
                self.active_players[p["discord_id"]] = p

    def HasPlayerSignedUp(self, discord_id):
        return discord_id in self.players
    
    def CanPlayerRaid(self, discord_id):
        return discord_id in self.active_players
    
    def GetActiveCharsByRole(self, role):
        chars = {}
        for _, c in self.charDB.chars.items():
            if self.CanPlayerRaid(c["discord_id"]) and c[role]:
                chars[c["name"]] = c
        return chars
    
    def GetActiveChars(self) -> dict: 
        chars = {}
        for _, c in self.charDB.chars.items():
            if self.CanRaid(c["discord_id"]):
                chars[c["name"]] = c
        return chars
    
    def GetActivePlayers(self):
        return self.active_players

    def IsShortRun(self):
        title = self.title.lower()
        return "algalon" in title or "wed" in title
    
    def RequiresSoaker(self):
        return "ulduar" in self.title.lower()
    
    def RequiresMotalStrike(self):
        return "togc" in self.title.lower()
    
    def IsBenched(self, discord_id):
        return self.players[discord_id]["signup"] == "Bench"
    
class Roster:

    def __init__(self, signup : Signup, char_db, tmb, id):
        self.roster = {} # K = Char name, R = Role

        self.signup = signup
        self.chars = char_db
        self.tmb = tmb
        self.id = id

    def __getitem__(self, key):
        return self.roster[key]
    
    def __contains__(self, key):
        return key in self.roster
    
    """
    Returns K = Char name, R = Role
    """
    def items(self):
        return self.roster.items()
    
    def __str__(self):
        return str(self.roster)
    
    def print(self):
        print("{0:<6s}Roster {1}".format("", self.signup.title))
        self.PrintRole("dps")
        self.PrintRole("healer")
        self.PrintRole("tank")
        soaker = self.GetSoaker()
        print("Soaker: {}".format(soaker))

    def PrintRole(self, role):
        print("{0:<16s}{1}".format("", role))
        role_chars = self.GetCharsByRole(role)
        for i in range(0, len(role_chars), 2):
            char = role_chars[i]
            print("{0:<16s}\t".format(char), end='')
            if i + 1 < len(role_chars):
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
    
    def ContainsAlt(self, char_name: str):
        discord_id = self.chars[char_name]['discord_id']
        res, c = self.ContainsPlayer(discord_id)
        return res and c['name'] != char_name

    def ContainsPlayer(self, discord_id: str):
        for c, r in self.roster.items():
            if self.chars[c]['discord_id'] == discord_id:
                return r != "bench", c
        return False
    
    def ContainsChar(self, char: str):
        return char in self.roster and self.roster[char] != "bench"
    
    def GetPlayerAmount(self):
        return len(self.roster)

    def IsValid(self):
        return len(self.roster) == 10
    
    def GetSoaker(self):
        for c, r in self.roster.items():
            char = self.chars[c]
            if char['class'] == "Rogue" or (char['class'] == "Priest" and r == "dps"):
                return char['name']
        
        return None
    
    def GetShaman(self):
        for c, r in self.items():
            char = self.chars[c]
            if char["class"] == "Shaman":
                return char
        return None
