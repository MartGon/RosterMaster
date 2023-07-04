import argparse
import json
import math

import common

class SlackerDetector:

    def __init__(self, charDB_file, sfp : str):
        self.chars = common.CharacterBD(charDB_file)
        self.signups = common.Signup.LoadSignups(self.chars, sfp)

    def GetActivesPerSignup(self):
        actives = {}
        
        signups = self.signups
        players = self.chars.GetPlayers()
        for discord_id, char_name in players.items():
            for s in signups:
                if s.HasPlayerSignedUp(discord_id):
                    if s.title in actives:
                        actives[s.title].append(char_name)
                    else:
                        actives[s.title] = [char_name]
        return actives

    def GetSlackersPerSignup(self):
        slackers = {}
        
        signups = self.signups
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
        
        signups = self.signups
        players = self.chars.GetPlayers()
        for discord_id, char_name in players.items():
            for s in signups:
                has_quit = self.chars[char_name]['has_quit']
                is_core = self.chars.GetMain(discord_id)
                if (s.HasPlayerSignedUp(discord_id) or has_quit or is_core is None) and discord_id in slackers:
                    slackers.pop(discord_id)
        
        return slackers
    
    def GetInactivePlayers(self):

        players = self.chars.GetPlayers()
        signups = self.signups
        for s in signups:
            ap = s.GetActivePlayers()
            for p in ap:
                if p in players:
                    players.pop(p)
        return players
    
    def GetActivePlayers(self) -> dict:

        players_db = self.chars.GetPlayers()

        players = {}
        signups = self.signups
        for s in signups:
            ap = s.GetActivePlayers()
            for id, name in ap.items():
                players[id] = players_db[id]

        return players
    
    def GetUnavailableActivesPerSignup(self) -> dict:
        
        unavailable_players = {}

        signups = self.signups
        players = self.GetActivePlayers()
        for discord_id, char_name in players.items():
            for s in signups:
                if discord_id not in s.active_players:
                    if s.title in unavailable_players:
                        unavailable_players[s.title].append(char_name)
                    else:
                        unavailable_players[s.title] = [char_name]
        return unavailable_players
    
    def GetActiveChars(self) -> dict:
        
        active_chars = {}
        active_players = self.GetActivePlayers()

        for id, _ in active_players.items():
            chars = self.chars.FindCharacters(id)
            for name, char in chars.items():
                active_chars[name] = char

        return active_chars


def main():

    parser = argparse.ArgumentParser(prog='SlcakerDetector', description='Checks for player that didnt sign up', epilog='Call with --help to find a list of available commands')
    parser.add_argument("--characters-db", default="characters-db.csv")
    parser.add_argument("--sfp", default="s%i.json")
    args = parser.parse_args()

    sd = SlackerDetector(args.characters_db, args.sfp)
    players = sd.GetActivePlayers()
    print("The following players ({}) have signed up for at least one raid this week".format(len(players)))
    for id, name in players.items():
        print(name)
    print()

    print("The following players have signed up for at least one raid, but cannot raid on this day")
    unavailable_players = sd.GetUnavailableActivesPerSignup()
    for signup, unavailable_players in unavailable_players.items():
        print(signup)
        for char_name in unavailable_players:
            print(char_name)
        print()

    sd = SlackerDetector(args.characters_db, args.sfp)
    chars = sd.GetActiveChars()
    print("These are the active chars ({}) which have signed up for at least one raid this week".format(len(chars)))
    for name, char in chars.items():
        print(name)
    print()

    # actives = sd.GetActivesPerSignup()
    # for signup, actives in actives.items():
    #     print(signup)
    #     #print("The following players have not signed up")
    #     for char_name in actives:
    #         print(char_name)
    #     print()

    # slackers = sd.GetSlackersPerSignup()
    # for signup, slackers in slackers.items():
    #     print(signup)
    #     #print("The following players have not signed up")
    #     for char_name in slackers:
    #         print(char_name)
    #     print()

    # print("The following players are not raiding in any day")
    # slackers = sd.GetInactivePlayers()
    # for _, slacker in slackers.items():
    #     print(slacker)
    # print()

    print("The following players have not signed up for any raid")
    slackers = sd.GetSlackers()
    for _, slacker in slackers.items():
        print("@{} ".format(sd.chars[slacker]['discord_user']))

if __name__ == "__main__":
    main()