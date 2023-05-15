import argparse
import json
import math

import common

class SlackerDetector:

    def __init__(self, charDB_file, s1_file, s2_file, s3_file):
        self.chars = common.CharacterBD(charDB_file)
        self.s1 = common.Signup(self.chars, s1_file)
        self.s2 = common.Signup(self.chars, s2_file)
        self.s3 = common.Signup(self.chars, s3_file)

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
    parser.add_argument("--s1", default="s1.json")
    parser.add_argument("--s2", default="s2.json")
    parser.add_argument("--s3", default="s3.json")
    args = parser.parse_args()

    sd = SlackerDetector(args.characters_db, args.s1, args.s2, args.s3)
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