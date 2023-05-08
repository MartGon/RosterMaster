import argparse
import json
import math

import common

class SlackerDetector:

    def __init__(self, charDB_file, r1_file, r2_file, r3_file):
        self.chars = common.CharacterBD(charDB_file)
        self.s1 = common.Signup(self.chars, r1_file)
        self.s2 = common.Signup(self.chars, r2_file)
        self.s3 = common.Signup(self.chars, r3_file)

    def GetSlackersPerSignup(self):
        slackers = {}
        
        signups = [self.s1, self.s2, self.s3]
        players = self.chars.GetPlayers()
        for discord_id, char_name in players.items():
            for s in signups:
                if not s.HasPlayerSignedUp(discord_id):
                    if s.title in slackers:
                        slackers[s.title].append(char_name)
                    else:
                        slackers[s.title] = [char_name]
        return slackers
    
    def GetSlackers(self):
        slackers = self.chars.GetPlayers()
        
        signups = [self.s1, self.s2, self.s3]
        players = self.chars.GetPlayers()
        for discord_id, char_name in players.items():
            for s in signups:
                if s.HasPlayerSignedUp(discord_id) and discord_id in slackers:
                    slackers.pop(discord_id)
        
        return slackers
    
    def GetInactivePlayers(self):

        players = self.chars.GetPlayers()
        signups = [self.s1, self.s2, self.s3]
        for s in signups:
            ap = s.GetActivePlayers()
            for p in ap:
                if p in players:
                    players.pop(p)
        return players

def main():

    parser = argparse.ArgumentParser(prog='SlcakerDetector', description='Checks for player that didnt sign up', epilog='Call with --help to find a list of available commands')
    parser.add_argument("--characters-db", default="characters-db.csv")
    parser.add_argument("--r1", default="r1.json")
    parser.add_argument("--r2", default="r2.json")
    parser.add_argument("--r3", default="r3.json")
    args = parser.parse_args()

    sd = SlackerDetector(args.characters_db, args.r1, args.r2, args.r3)
    slackers = sd.GetSlackersPerSignup()
    for signup, slackers in slackers.items():
        print(signup)
        #print("The following players have not signed up")
        for char_name in slackers:
            print(char_name)
        print()

    print("The following players have not signed up for any raid")
    slackers = sd.GetSlackers()
    for _, slacker in slackers.items():
        print(slacker)

    print()
    print("The following players are not raiding in any day")
    slackers = sd.GetInactivePlayers()
    for _, slacker in slackers.items():
        print(slacker)


if __name__ == "__main__":
    main()