import argparse
import json
import math
import logging
import statistics

import tmb
import common

class Report:

    def __init__(self, roster_checker, roster: common.Roster, benched_chars : list, covered_buffs : dict, unavailable_chars: dict, duplicated_players: dict, loot: dict, class_diversity: dict):
        self.roster_checker = roster_checker

        self.roster = roster
        self.benched_chars = benched_chars
        self.covered_buffs = covered_buffs
        self.unavailable_chars = unavailable_chars
        self.duplicated_players = duplicated_players

        self.loot = loot
        self.class_diversity = class_diversity

    def IsRaidViable(self):
        soaker_req = not self.roster.signup.RequiresSoaker() or self.roster.GetSoaker()
        return self.roster.IsValid() and soaker_req and len(self.unavailable_chars) == 0 and len(self.duplicated_players) == 0

    def print(self):

        # Print roster
        print()
        print("{0:<14s}Review {1}".format("", self.roster.signup.title))
        self.roster.print()

        # Print info
        short_run = self.roster.signup.IsShortRun()
        if short_run:
            logging.info("Short run: {}".format(short_run))
        if self.roster.signup.RequiresSoaker() and self.roster.GetSoaker() is None:
            logging.error("Soaker not found!")
        if self.roster.GetShaman() is None:
            logging.error("Shaman not found")
        for c, char in self.unavailable_chars.items():
            logging.error("Character {}({}) cannot raid this day".format(c, char["discord_id"]))
        for _, c in self.duplicated_players.items():
            logging.error("Player {} would be using two chars!".format(c))
        for c, char in self.roster.items():
            if c in self.roster_checker.inactive_chars and self.roster_checker.inactive_chars[c]:
                logging.warning("Using inactive char: {}".format(c))
        for id, char in self.loot.items():
            item = self.roster_checker.contested_items[id]
            if char:
                logging.info("Item {}({}) is covered by {} with {} prio".format(item["name"], id, char["name"], char["prio"]))
            else:
                logging.warning("Item {}({}) is not covered by any char".format(item["name"], id))
        logging.debug(self.class_diversity)
        print()

        covered_buffs = []
        for buff, is_covered in self.covered_buffs['buffs'].items():
            if is_covered:
                covered_buffs.append(buff)
        logging.info("Buffs covered {}".format(covered_buffs))
        covered_debuffs = []
        for debuff, is_covered in self.covered_buffs['debuffs'].items():
            if is_covered:
                covered_debuffs.append(debuff)
        logging.info("Debuffs covered {}".format(covered_debuffs))

        if self.roster.signup.RequiresMotalStrike():
            covered, c = self.roster_checker.IsBuffCovered(self.roster, self.roster_checker.raid_comp_data['debuffs']['mortal-strike'])
            logging.info("Mortal strike provided by {}".format(c))

        logging.info("Benched chars {}".format(self.benched_chars))

        buff_score, debuff_score = self.roster_checker.CalcBuffCoverageScore(self.roster)
        logging.info("Buff score: {} Debuff scoqre: {} Total: {}".format(buff_score, debuff_score, buff_score + debuff_score))

        print()

class RosterChecker:

    def __init__(self, raid_comp_data, charDB_file, inactive_chars, tmb_file, contested_items_file, sfp):
        self.raid_comp_data = json.load(open(raid_comp_data))
        self.chars = common.CharacterBD(charDB_file)
        self.inactive_chars = json.load(open(inactive_chars))
        self.contested_items = json.load(open(contested_items_file))
        self.tmb = tmb.ReadDataFromJson(tmb.GetDataFromFile(tmb_file))
        self.signups = common.Signup.LoadSignups(self.chars, sfp)

    def ReadRosters(self, roster_file):

        rosters = []
        with open(roster_file, 'r') as f:
            dps = True
            signup_indices = [int(a) for a in f.readline().strip('\n').split(' ')]
            for line in f:
                if "Tank" in line or "Heals" in line:
                    dps = False
                    continue

                if "Bench" in line:
                    break

                chars = line.split()
                for i in range(0, len(chars)):
                    char = chars[i].strip()

                    signup_index = math.floor(i / 2)
                    if signup_index >= len(rosters):
                        rosters.append(common.Roster(self.signups[signup_indices[signup_index]], self.chars, self.tmb, 0))    
                    roster = rosters[signup_index]

                    role = "dps" if dps else "healer" if i & 1 else "tank"
                    roster.RosterChar(char, role)

        return rosters
    
    def SaveRostersToFile(self, rosters: "list[common.Roster]", out: str, mode: str = 'w'):

        with open(out, mode) as f:

            # Print header
            for r in rosters:
                f.write("{}\t\t\t".format(r.signup.title))
            f.write('\n')

            # Print grp header
            for r in rosters:
                f.write("G1\tG2\t\t")
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

    def PrintPingMessages(self, rosters: "list[common.Roster]"):

        for r in rosters:
            print(r.signup.title)

            for c, r in r.items():
                print('@' + self.chars[c]['discord_user'] + ' ')
            print()

    def AreRostersValid(self, rosters: "list[common.Roster]"):
        for r in rosters:
            if not r.IsValid():
                return False
        return True

    def CheckRosters(self, rosters: "list[common.Roster]"):
        
        rosters.sort(key=lambda x : x.id)
        for r in rosters:
            report = self.GenerateReport(r, rosters)
            report.print()

            for c, r in r.items():
                if not self.HasCharSignedUp(self.signups, c):
                    logging.warning("Using Character {} which didn't sing up".format(c))

        self.CheckDuplicates(rosters)

        score, iscores = self.CalcViabilityScoreAlt(rosters)
        print("Score: ", score)
        print("Individual scores", iscores)

    def GenerateReport(self, r: common.Roster, rosters: "list[common.Roster]") -> Report:
        covered_buffs = self.GetCoveredBuffs(r)
        unavailable_chars = self.GetUnavailableChars(r)
        duplicated_players = self.GetDuplicatedPlayers(r)
        loot = self.GetLootCoverage(r)
        class_diversity = self.GetClassDiversity(r)
        benched_chars = self.GetCharsInBench(r, rosters)

        return Report(self, r, benched_chars, covered_buffs, unavailable_chars, duplicated_players, loot, class_diversity)

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

    def GetCoveredBuffs(self, roster: common.Roster) -> dict:
        
        covered_buffs = {}
        for name, buff in self.raid_comp_data["buffs"].items():
            covered_buffs[name] = self.IsBuffCovered(roster, buff)[0]

        covered_debuffs = {}
        for name, debuff in self.raid_comp_data["debuffs"].items():
            covered_debuffs[name] = self.IsBuffCovered(roster, debuff)[0]

        return {"buffs" : covered_buffs, "debuffs" : covered_debuffs}

    def IsBuffCovered(self, roster: common.Roster, buff: dict) -> bool:
        for c, r in roster.items():
            spec = self.GetCharSpec(self.chars[c], r)
            if spec in buff['provided_by'] and r != "bench":
                return True, c
            
        return False, None
    
    def CalcBuffCoverageScore(self, roster: common.Roster):
        covered_buffs = self.GetCoveredBuffs(roster)
        buff_score = 0
        for bname, is_covered in covered_buffs["buffs"].items():
            if is_covered:
                buff_score = buff_score + self.raid_comp_data["buffs"][bname]["score"]

        debuff_score = 0
        for bname, is_covered in covered_buffs["debuffs"].items():
            if is_covered:
                debuff_score = debuff_score + self.raid_comp_data["debuffs"][bname]["score"]

        return buff_score, debuff_score
    
    def GetCharSpec(self, char: dict, role: str) -> str:
        class_ = char["class"]
        class_spec = char['spec'] if char["MS"] == role else char['offspec']
        return class_ + ":" + class_spec
    
    def HasCharSignedUp(self, signups: "list[common.Signup]", char: str):
        for s in signups:
            char_data = self.chars[char]
            discord_id = char_data['discord_id']
            if discord_id in s.active_players:
                spec = s.active_players[discord_id]['spec']
                if char_data['spec'] in spec:
                    return True
                
        return False

    def HasCharBeenRostered(self, rosters: "list[common.Roster]", char: str):
        
        for r in rosters:
            if r.ContainsChar(char):
                return True
            
        return False

    def CalcRoleScore(self, r: common.Roster, role: str):
        role_chars = r.GetCharsByRole(role)
        role_score = 0
        for c in role_chars:
            spec = self.GetCharSpec(self.chars[c], role)
            role_score = role_score + self.raid_comp_data[role + "-rating"][spec]

        return role_score

    def CalcViabilityScore(self, rosters: "list[common.Roster]"):
        score = 0

        # Global score
        iscores = []
        for i in range(0, len(rosters)):
            
            r = rosters[i]
            report = self.GenerateReport(r, rosters)

            # Calc base score
            iscore = self.CalcBaseViabilityScore(rosters, r, report)

            # Is there a shaman?
            if r.GetShaman():
                iscore = iscore + 100

            # Reward class diversity
            for role in report.class_diversity:
                for _class, count in report.class_diversity[role].items():
                    if _class != "Warlock" and _class != "Death Knight":
                        mod = (10 - count) * 2.5
                        iscore = iscore + mod

            # Consider melee and caster balance
            iscore = max(iscore, 0)            
            iscores.append(iscore)

        score = statistics.harmonic_mean(iscores)
        return score, iscores
    
    def CalcViabilityScoreAlt(self, rosters: "list[common.Roster]"):
        score = 0

        # Global score
        iscores = []
        for i in range(0, len(rosters)):
            r = rosters[i]
            report = self.GenerateReport(r, rosters)

            # Calc base score
            iscore = self.CalcBaseViabilityScore(rosters, r, report)
            if iscore <= 0:
                iscores.append(0)
                continue

            # Calc buff/debuff coverage
            buff_score, debuff_score = self.CalcBuffCoverageScore(r)
            iscore = iscore + buff_score + debuff_score

            # Calc roles score
            tank_score = self.CalcRoleScore(r, "tank")
            healer_score = self.CalcRoleScore(r, "healer")
            iscore = iscore + tank_score + healer_score
            logging.debug("Tank score: {} Healer score: {}".format(tank_score, healer_score))

            # Consider melee and caster balance
            iscore = max(iscore, 0)            
            iscores.append(iscore)

        score = statistics.harmonic_mean(iscores)
        return score, iscores
    
    def CalcBaseViabilityScore(self, rosters: "list[common.Roster]", r: common.Roster, report: Report):
        iscore = 0
        # Can we even raid with this roster?
        if report.IsRaidViable():
            iscore = 1000
        else:
            return 0

        # Is item covered?
        for id, char in report.loot.items():
            if char:
                iscore = iscore + self.raid_comp_data["misc"]["item-covered"]

        # Requires mortal strike and is covered
        if r.signup.RequiresMotalStrike() and self.IsBuffCovered(r, self.raid_comp_data["debuffs"]["mortal-strike"]):
            iscore = iscore + self.raid_comp_data["misc"]["mortal-strike-covered"]

        for c, role in r.items():
            char = self.chars[c]

            # Reward using main spec
            if char["MS"] == role:
                iscore = iscore + self.raid_comp_data["misc"]["main-spec"]

            # Reward using main chars on a short run
            if r.signup.IsShortRun():
                if char["is_main"]:
                    iscore = iscore + self.raid_comp_data["misc"]["main-in-short-run"]

            # Punish using char that dindt  sing up
            if not self.HasCharSignedUp(self.signups, c):
                iscore = iscore - self.raid_comp_data["misc"]["unsigned-char"]

            # Punish using inactive chars
            if c in self.inactive_chars:
                iscore = iscore + self.raid_comp_data["misc"]["inactive-char"]
        
            # Punish using benched players
            if r.signup.IsBenched(char["discord_id"]):
                iscore = iscore + self.raid_comp_data["misc"]["benched-char"]

        # Punish same class healers/tanks
        healers = r.GetCharsByRole('healer')
        if self.chars[healers[0]]['class'] == self.chars[healers[1]]['class']:
            iscore = iscore + self.raid_comp_data["misc"]["same-healer"]
        tanks = r.GetCharsByRole('tank')
        if self.chars[tanks[0]]['class'] == self.chars[tanks[1]]['class']:
            iscore = iscore + self.raid_comp_data["misc"]["same-tank"]

        return iscore

    def GetCharsInBench(self, r: common.Roster, rosters: "list[common.Roster]"):
        benched_chars = []

        for discord_id, p in r.signup.active_players.items():
            
            # Bench cannot contain alts from a given player
            if r.ContainsPlayer(discord_id):
                continue

            player_chars = self.chars.FindCharacters(discord_id)
            for char_name, _ in player_chars.items():
                if not self.HasCharBeenRostered(rosters, char_name) and self.HasCharSignedUp(self.signups, char_name):
                    benched_chars.append(char_name)

        return benched_chars

# Alg. Notes
# Config file for score system

#TODO: Print benched players in out filel
def main():

    parser = argparse.ArgumentParser(prog='RosterChecker', description='Checks the viability of a given set of rosters', epilog='Call with --help to find a list of available commands')
    parser.add_argument("--raid-comp-data", default="raid-comp-data.json")
    parser.add_argument("--characters-db", default="characters-db.csv")
    parser.add_argument("--inactive-chars", default='inactive-chars.json')
    parser.add_argument("--tmb-file", default="character-json.json")
    parser.add_argument("--contested-items", default="contested-items.json")
    parser.add_argument("--sfp", default="s%i.json")
    parser.add_argument("-r", default="r.txt")
    parser.add_argument("-o", default="out.txt")
    parser.add_argument("-v", default=logging.INFO)
    parser.add_argument("-s", default=0)
    args = parser.parse_args()

    logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)

    rc = RosterChecker(args.raid_comp_data, args.characters_db, args.inactive_chars, args.tmb_file, args.contested_items, args.sfp)
    rosters = rc.ReadRosters(args.r)
    rc.CheckRosters(rosters)
    if args.s:
        rc.SaveRostersToFile(rosters, args.o)
    input("-------------- Press Enter --------------")
    rc.PrintPingMessages(rosters)

if __name__ == "__main__":
    main()