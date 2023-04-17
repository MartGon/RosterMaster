import argparse
import json
import math
import colorama

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

    def CheckRosters(self):
        for r in self.rosters:
            r.print()
            print("{0:<14s}Review {1}".format("", r.id))

            self.CheckSoaker(r)
            self.CheckContestedItems(r)
            self.CheckSignups(r)
            self.CheckSamePerson(r)
            print()
            
    def CheckSoaker(self, roster: common.Roster):
        soaker = roster.GetSoaker()
        if soaker is None:
            print("{}Error!!! Soaker not found!{}".format(common.bcolors.FAIL, common.bcolors.ENDC))

    def CheckContestedItems(self, roster: common.Roster):
        r = roster

        for id, item in self.contested_items.items():
            users = self.GetItemUsersInRoster(int(id), r)

            if len(users) > 0:
                print("Item {}({}) is covered by {} with {} prio".format(item["name"], id, users[0]["name"], users[0]["prio"]))
            else:
                print("{}WARNING!!! Item {}({}) is not covered by any char {}".format(common.bcolors.WARNING, item["name"], id, common.bcolors.ENDC))

    def CheckSignups(self, roster: common.Roster):
        active_players = roster.signup.GetActivePlayers()
        for char in roster.roster:
            discord_id = self.chars.GetDiscordId(char)
            if discord_id not in active_players:
                print("{}Error!!! Character {}({}) cannot raid this day {}".format(common.bcolors.FAIL, char, discord_id, common.bcolors.ENDC))

    def CheckSamePerson(self, roster: common.Roster):
        for c, _  in roster.items():
            discord_id = self.chars[c]["discord_id"]
            for c2, _  in roster.items():
                if c != c2 and self.chars[c2]["discord_id"] == discord_id:
                    print("{}Error!!! Player {} would be using two chars! {}".format(common.bcolors.FAIL, c, common.bcolors.ENDC))
                    return True
                
        return False

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
    
    def GetItemUsersInRoster(self, item_id, roster):
        users = []
        for c in roster.roster:
            prio = self.GetItemPrio(c, item_id)
            if prio > 0:
                users.append({"name" : c, "prio" : prio})

        users.sort(key=lambda x : x["prio"])
        return users


# Check if a character has already been listed in any of the other rosters

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
    rc.CheckRosters()

if __name__ == "__main__":
    main()