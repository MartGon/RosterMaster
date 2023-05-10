
import argparse
import json
import random
import common
import logging
import multiprocessing

import tmb

from rc import RosterChecker

class RosterMaster:

    def __init__(self, charDB_file, tmb_file, contested_items_file, s1_file, s2_file, s3_file):
        self.chars = common.CharacterBD(charDB_file)
        self.contested_items = json.load(open(contested_items_file))
        self.tmb = tmb.ReadDataFromJson(tmb.GetDataFromFile(tmb_file))
        self.s1 = common.Signup(self.chars, s1_file)
        self.s2 = common.Signup(self.chars, s2_file)
        self.s3 = common.Signup(self.chars, s3_file)
        
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

def main():

    parser = argparse.ArgumentParser(prog='RosterMaster', description='Creates a somewhat viable roster taking loot into account', epilog='Call with --help to find a list of available commands')
    parser.add_argument("--characters-db", default="characters-db.csv")
    parser.add_argument("--tmb-file", default="character-json.json")
    parser.add_argument("--s1", default="s1.json")
    parser.add_argument("--s2", default="s2.json")
    parser.add_argument("--s3", default="s3.json")
    parser.add_argument("--contested-items", default="contested-items.json")
    parser.add_argument("-i", default=10000, type=int)
    parser.add_argument("-j", default=8, type=int)
    args = parser.parse_args()

    logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)
    rm = RosterMaster(args.characters_db, args.tmb_file, args.contested_items, args.s1, args.s2, args.s3)
    rc = RosterChecker(args.characters_db, args.tmb_file, args.contested_items, args.s1, args.s2, args.s3)

    # Multithreaded generation
    mgr = multiprocessing.Manager()
    lock = mgr.Lock()
    results = mgr.list()
    def GenerateRoster(iterations):
        i_results = []
        for i in range(0, iterations):
            rosters = rm.GenerateRandomRosters()
            if rosters:
                score, iscores = rc.CalcViabilityScore(rosters)
                res = {"rosters" : rosters, "score" : score, "iscores" : iscores}
                i_results.append(res)

        i_results.sort(key=lambda x : x["score"], reverse=True)
        lock.acquire()
        for i in range(0, 5):
            results.append(i_results[i])
        lock.release()

    iterations = args.i
    threads_amount = args.j
    
    threads = []
    workload = int(iterations / threads_amount)
    print("Each thread will generate: {} rosters", workload)
    for i in range(0, threads_amount):
        thread = multiprocessing.Process(target=GenerateRoster, kwargs={"iterations" : workload})
        thread.start()
        threads.append(thread)

    for thread in threads:
        thread.join()

    # Print results
    print("Sorting results")
    results.sort(key=lambda x : x["score"], reverse=True)
    print("Top 5")
    for i in range(0, 5):
        print("Rosters ", i)
        res = results[i]
        rc.CheckRosters(res["rosters"])
        print()
        input("-------------- Press Enter --------------")

            

if __name__ == "__main__":
    main()