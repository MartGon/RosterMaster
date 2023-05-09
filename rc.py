import argparse
import json
import math
import logging

import tmb
import common

class Report:

    def __init__(self, contested_items, roster: common.Roster, player_amount, soaker, shaman, unavailable_chars: dict, duplicated_players: dict, loot: dict, class_diversity: dict):
        self.contested_items = contested_items
        self.roster = roster
        self.player_amount = player_amount
        self.soaker = soaker
        self.shaman = shaman
        self.unavailable_chars = unavailable_chars
        self.duplicated_players = duplicated_players
        self.loot = loot
        self.class_diversity = class_diversity

    def print(self):
        if self.soaker is None:
            logging.error("Soaker not found!")
        if self.shaman is None:
            logging.error("Shaman not found")
        for c, char in self.unavailable_chars.items():
            logging.error("Character {}({}) cannot raid this day".format(c, char["discord_id"]))
        for discord_id, c in self.duplicated_players.items():
            logging.error("Player {} would be using two chars!".format(c))
        for id, char in self.loot.items():
            item = self.contested_items[id]
            if char:
                logging.info("Item {}({}) is covered by {} with {} prio".format(item["name"], id, char["name"], char["prio"]))
            else:
                logging.warning("Item {}({}) is not covered by any char".format(item["name"], id))

class RosterChecker:

    def __init__(self, charDB_file, tmb_file, contested_items_file, r1_file, r2_file, r3_file):
        self.chars = common.CharacterBD(charDB_file)
        self.contested_items = json.load(open(contested_items_file))
        self.tmb = tmb.ReadDataFromJson(tmb.GetDataFromFile(tmb_file))
        self.s1 = common.Signup(self.chars, r1_file)
        self.s2 = common.Signup(self.chars, r2_file)
        self.s3 = common.Signup(self.chars, r3_file)

    def ReadRosters(self, roster_file):

        self.rosters = [common.Roster(self.s1, self.chars, self.tmb, 0), common.Roster(self.s2, self.chars, self.tmb, 1), common.Roster(self.s3, self.chars, self.tmb, 2)]
        with open(roster_file, 'r') as f:
            dps = True
            for line in f:
                if "Tank" in line or "Heals" in line:
                    dps = False
                    continue

                chars = line.split()
                for i in range(0, len(chars)):
                    char = chars[i]

                    roster_index = math.floor(i / 2)
                    roster = self.rosters[roster_index]

                    role = "dps" if dps else "healer" if i & 1 else "tank"
                    roster.RosterChar(char, role)

    def CheckRosters(self):
        for r in self.rosters:
            r.print()
            
            report = self.GenerateReport(r)
            print("{0:<14s}Review {1}".format("", r.id))
            report.print()
            print()

        self.CheckDuplicates(self.rosters)

    def GenerateReport(self, r: common.Roster):
        player_amount = r.GetPlayerAmount()
        soaker = r.GetSoaker()
        shaman = r.GetShaman()
        unavailable_chars = self.GetUnavailableChars(r)
        duplicated_players = self.GetDuplicatedPlayers(r)
        loot = self.GetLootCoverage(r)
        class_diversity = None

        return Report(self.contested_items, r, player_amount, soaker, shaman, unavailable_chars, duplicated_players, loot, class_diversity)

    def GetUnavailableChars(self, roster: common.Roster):
        active_players = roster.signup.GetActivePlayers()
        unavailable_chars = {}
        for char in roster.roster:
            discord_id = self.chars.GetDiscordId(char)
            if discord_id not in active_players:
                unavailable_chars[char] = self.chars[char]
        
        return unavailable_chars

    def GetLootCoverage(self, roster: common.Roster):
        r = roster

        loot = {}
        for id, item in self.contested_items.items():
            users = self.GetItemUsersInRoster(int(id), r)
            if len(users) > 0:
                loot[id] = users[0]
            else:
                loot[id] = None

        return loot

    def GetDuplicatedPlayers(self, roster: common.Roster):
        duplicated_players = {}
        for c, _  in roster.items():
            discord_id = self.chars[c]["discord_id"]
            for c2, _  in roster.items():
                if c != c2 and self.chars[c2]["discord_id"] == discord_id:
                    duplicated_players[discord_id] = c
        
        return duplicated_players

    def GetItemPrio(self, char_name, item_id):
        for _, char in self.tmb.items():
            can_receive = item_id in char.wishlist and not char.wishlist[item_id]["is_received"]
            if char.data["name"].lower() == char_name.lower() and can_receive:
                return char.wishlist[item_id]["order"]
        return -1
    
    def GetItemUsers(self, item_id):
        users = []
        for c in self.char.items():
            if self.GetItemPrio(c["name"], item_id) > 0:
                users.append(c)

        return users
    
    def GetItemUsersInRoster(self, item_id, roster: common.Roster):
        users = []
        for c in roster.roster:
            prio = self.GetItemPrio(c, item_id)
            if prio > 0:
                users.append({"name" : c, "prio" : prio})

        users.sort(key=lambda x : x["prio"])
        return users
    
    def GetDuplicates(self, rosters: "list[common.Roster]"):
        
        duplicates = {}
        size = len(rosters)
        for i in range(0, size):
            for j in range(i + 1, size):
                
                r1 = rosters[i]
                r2 = rosters[j]
                for c1, char1 in r1.items():
                    for c2, _ in r2.items():
                        if c1 == c2 :
                            duplicates[c1] = char1
        return duplicates

    def CheckDuplicates(self, rosters: "list[common.Roster]"):
        
        chars = self.GetDuplicates(rosters)
        if len(chars) > 0:
            for c, char in chars.items():
                logging.error("Character {} has been rostered twice!".format(c))
            return True

        return False
    
    def GetClassDiversity(self, roster: common.Roster):
        pass

    def CalcViabilityScore(self, rosters: "list[common.Roster]"):
        score = 0

        # Global score
        # Are the players who need contested items rostered, if they can raid?

        for i in range(0, len(rosters)):
            r = rosters[i]
            
            # Individual score
            # 1. Is Valid? (Has enough players)
            # 2. Has a soaker? Could create a custom role for this, auto assigned for every rogue and priest with a dps spec
            # 2a. Has a shaman? Pretty much needed
            # 3. Constested loot distribution. Two players need the same loot?
            # 4. Class diversity? (Could be expanded to buff/debuff coverage)
            # 5. (Extra) Has a MS effect to zug Freya?

        return score
    
    def IsViable(self, r: common.Roster):
        unavailable_chars = self.GetUnavailableChars(r)
        is_viable = r.GetShaman() is not None and r.GetSoaker() is not None and r.IsValid() is not None
        
        return is_viable and len(unavailable_chars) == 0
    
        


# Calc some kind of class diversity score. Could go deeper and calc buffs
# Calc score taking into account if a char is using its MS or OS
# Could also increase score if using a main char

def main():

    parser = argparse.ArgumentParser(prog='RosterChecker', description='Checks the viability of a given set of rosters', epilog='Call with --help to find a list of available commands')
    parser.add_argument("--characters-db", default="characters-db.csv")
    parser.add_argument("--tmb-file", default="character-json.json")
    parser.add_argument("--contested-items", default="contested-items.json")
    parser.add_argument("--r1", default="r1.json")
    parser.add_argument("--r2", default="r2.json")
    parser.add_argument("--r3", default="r3.json")
    parser.add_argument("-r", default="r.txt")
    args = parser.parse_args()

    logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)

    rc = RosterChecker(args.characters_db, args.tmb_file, args.contested_items, args.r1, args.r2, args.r3)
    rc.ReadRosters(args.r)
    rc.CheckRosters()

if __name__ == "__main__":
    main()