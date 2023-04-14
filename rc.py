import argparse
import json
import math

import tmb
import common

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



# Check if there's a soaker
# Check if contested items are covered
# Check if that player can raid in a given day
# Check that there are not two chars of the player in the same raid    

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

    rc = RosterChecker(args.characters_db, args.tmb_file, args.contested_items, args.r1, args.r2, args.r3)
    rc.ReadRosters(args.r)
    for r in rc.rosters:
        r.print()

if __name__ == "__main__":
    main()