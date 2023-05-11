import argparse
import json
import math
import logging
import statistics

import tmb
import common

class Report:

    def __init__(self, contested_items, inactive_chars : dict, roster: common.Roster, unavailable_chars: dict, duplicated_players: dict, loot: dict, class_diversity: dict):
        self.contested_items = contested_items
        self.inactive_chars = inactive_chars
        
        self.roster = roster
        self.unavailable_chars = unavailable_chars
        self.duplicated_players = duplicated_players

        self.loot = loot
        self.class_diversity = class_diversity

    def IsRaidViable(self):
        return self.roster.IsValid() and self.roster.GetSoaker() and len(self.unavailable_chars) == 0 and len(self.duplicated_players) == 0

    def print(self):
        if self.roster.GetSoaker() is None:
            logging.error("Soaker not found!")
        if self.roster.GetShaman() is None:
            logging.error("Shaman not found")
        for c, char in self.unavailable_chars.items():
            logging.error("Character {}({}) cannot raid this day".format(c, char["discord_id"]))
        for discord_id, c in self.duplicated_players.items():
            logging.error("Player {} would be using two chars!".format(c))
        for c, char in self.roster.items():
            if c in self.inactive_chars and self.inactive_chars[c]:
                logging.warning("Using inactive char: {}".format(c))
        for id, char in self.loot.items():
            item = self.contested_items[id]
            if char:
                logging.info("Item {}({}) is covered by {} with {} prio".format(item["name"], id, char["name"], char["prio"]))
            else:
                logging.warning("Item {}({}) is not covered by any char".format(item["name"], id))
        logging.info(self.class_diversity)

class RosterChecker:

    def __init__(self, charDB_file, inactive_chars, tmb_file, contested_items_file, r1_file, r2_file, r3_file):
        self.chars = common.CharacterBD(charDB_file)
        self.inactive_chars = json.load(open(inactive_chars))
        self.contested_items = json.load(open(contested_items_file))
        self.tmb = tmb.ReadDataFromJson(tmb.GetDataFromFile(tmb_file))
        self.s1 = common.Signup(self.chars, r1_file)
        self.s2 = common.Signup(self.chars, r2_file)
        self.s3 = common.Signup(self.chars, r3_file)

    def ReadRosters(self, roster_file):

        rosters = [common.Roster(self.s1, self.chars, self.tmb, 0), common.Roster(self.s2, self.chars, self.tmb, 1), common.Roster(self.s3, self.chars, self.tmb, 2)]
        with open(roster_file, 'r') as f:
            dps = True
            for line in f:
                if "Tank" in line or "Heals" in line:
                    dps = False
                    continue

                chars = line.split()
                for i in range(0, len(chars)):
                    char = chars[i].trim()

                    roster_index = math.floor(i / 2)
                    roster = rosters[roster_index]

                    role = "dps" if dps else "healer" if i & 1 else "tank"
                    roster.RosterChar(char, role)

        return rosters
    
    def SaveRostersToFile(self, rosters: "list[common.Roster]", out: str, mode = 'w'):

        with open(out, mode) as f:

            # Print header
            for r in rosters:
                f.write("{}\t".format(r.signup.title))
            f.write('\n')

            # Print dps
            for i in range(0, 3):
                for r in rosters:
                    dps = r.GetCharsByRole("dps")
                    f.write("{}\t{}\t\t".format(dps[i*2], dps[i*2+1]))
                f.write('\n')

            # print header
            for i in range(0, 3):
                f.write("Tanks\tHeals\t\t")
            f.write('\n')

            # Print tanks and healers
            for i in range(0, 2):
                for r in rosters:
                    tanks = r.GetCharsByRole("tank")
                    heals = r.GetCharsByRole("healer")
                    f.write("{}\t{}\t\t".format(tanks[i], heals[i]))
                f.write('\n')
            
            f.write('\n')

    def CheckRosters(self, rosters: "list[common.Roster]"):
        
        rosters.sort(key=lambda x : x.id)
        for r in rosters:
            r.print()
            report = self.GenerateReport(r)
            print("{0:<14s}Review {1}".format("", r.signup.title))
            report.print()
            print()

        self.CheckDuplicates(rosters)

        score, iscores = self.CalcViabilityScore(rosters)
        print("Score: ", score)
        print("Individual scores", iscores)

    def GenerateReport(self, r: common.Roster):
        unavailable_chars = self.GetUnavailableChars(r)
        duplicated_players = self.GetDuplicatedPlayers(r)
        loot = self.GetLootCoverage(r)
        class_diversity = self.GetClassDiversity(r)

        return Report(self.contested_items, self.inactive_chars, r, unavailable_chars, duplicated_players, loot, class_diversity)

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

    def GetItemPrio(self, char_name, item_id):
        for _, char in self.tmb.items():
            can_receive = item_id in char.wishlist and not char.wishlist[item_id]["is_received"]
            if char.data["name"].lower() == char_name.lower() and can_receive:
                return char.wishlist[item_id]["order"]
        
        item = self.contested_items[str(item_id)]
        if char_name in item["needed_by"]:
            return 20

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
    
    def GetDuplicatedPlayers(self, roster: common.Roster):
        duplicated_players = {}
        for c, _  in roster.items():
            discord_id = self.chars[c]["discord_id"]
            for c2, _  in roster.items():
                if c != c2 and self.chars[c2]["discord_id"] == discord_id:
                    duplicated_players[discord_id] = c
        
        return duplicated_players

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
        class_diversity = {"dps": {}, "tank": {}, "healer": {}}
        for c, role  in roster.items():
            class_ = self.chars[c]["class"]
            if class_ not in class_diversity[role]:
                class_diversity[role][class_] = 1
            else:
                class_diversity[role][class_] = class_diversity[role][class_] + 1

        return class_diversity

    def CalcViabilityScore(self, rosters: "list[common.Roster]"):
        score = 0

        # Global score
        iscores = []
        for i in range(0, len(rosters)):
            
            r = rosters[i]
            report = self.GenerateReport(r)

            iscore = 0
            # Can we even raid with this roster?
            if report.IsRaidViable():
                iscore = 1000

            # Is there a shaman?
            if r.GetShaman():
                iscore = iscore + 100

            # Is item covered?
            for id, char in report.loot.items():
                if char:
                    iscore = iscore + 250

            # Reward class diversity
            for role in report.class_diversity:
                for _class, count in report.class_diversity[role].items():
                    if _class != "Warlock" and _class != "Death Knight":
                        mod = (10 - count) * 2.5
                        iscore = iscore + mod

            # Reward using main spec
            for c, role in r.items():
                if self.chars[c]["MS"] == role:
                    iscore = iscore + 10

            # Punish using inactive chars
            for c, role in r.items():
                if c in self.inactive_chars:
                    iscore = iscore - 50

            # Consider melee and caster balance
            
            iscores.append(iscore)

        score = statistics.harmonic_mean(iscores)
        return score, iscores
    
# Alg. Notes
# Punish same healer
# Reward healers based on performance. Pala-DPriest is the best combination
# Buff/Debuff approach
# Punish if using char that didn't sign up (Inconvenient)

def main():

    parser = argparse.ArgumentParser(prog='RosterChecker', description='Checks the viability of a given set of rosters', epilog='Call with --help to find a list of available commands')
    parser.add_argument("--characters-db", default="characters-db.csv")
    parser.add_argument("--inactive-chars", default='inactive-chars.json')
    parser.add_argument("--tmb-file", default="character-json.json")
    parser.add_argument("--contested-items", default="contested-items.json")
    parser.add_argument("--s1", default="s1.json")
    parser.add_argument("--s2", default="s2.json")
    parser.add_argument("--s3", default="s3.json")
    parser.add_argument("-r", default="r.txt")
    parser.add_argument("-o", default="out.txt")
    args = parser.parse_args()

    logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)

    rc = RosterChecker(args.characters_db, args.inactive_chars, args.tmb_file, args.contested_items, args.s1, args.s2, args.s3)
    rosters = rc.ReadRosters(args.r)
    rc.CheckRosters(rosters)
    rc.SaveRostersToFile(rosters, args.o)

if __name__ == "__main__":
    main()