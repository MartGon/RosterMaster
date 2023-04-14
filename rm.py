
import argparse
import json
import random
import common

import tmb

class RosterMaster:

    def __init__(self, charDB_file, tmb_file, contested_items_file, r1_file, r2_file, r3_file):
        self.chars = common.CharacterBD(charDB_file)
        self.contested_items = json.load(open(contested_items_file))
        self.tmb = tmb.ReadDataFromJson(tmb.GetDataFromFile(tmb_file))
        self.s1 = common.Signup(self.chars, r1_file)
        self.s2 = common.Signup(self.chars, r2_file)
        self.s3 = common.Signup(self.chars, r3_file)
        
    def GenerateRandomRosters(self):

        rosters = [common.Roster(self.s1, self.chars, self.tmb, 0), common.Roster(self.s2, self.chars, self.tmb, 1), common.Roster(self.s3, self.chars, self.tmb, 2)]

        self.AssignByRole(rosters, "tank", 2)
        self.AssignByRole(rosters, "healer", 2)
        self.AssignByRole(rosters, "dps", 6)

        return rosters

    def GenerateRandomRostersV2(self):
        pass

    def AssignByRole(self, rosters: "list[common.Roster]", role: str, min_amount: int):

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

                    # Remove this player's alts from selectable chars
                    alts = self.chars.FindAlts(char)
                    for alt in alts:
                        if alt in chars:
                            chars.pop(alt)

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

    def CheckDoubleAlt(self, roster: common.Roster):
        
        for c, _  in roster.items():
            discord_id = self.chars[c]["discord_id"]
            for c2, _  in roster.items():
                if c != c2 and self.chars[c2]["discord_id"] == discord_id:
                    return True
                
        return False

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