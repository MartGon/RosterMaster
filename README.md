# RosterMaster
## Description

RosterMaster is a tool that officers from *World of Warcraft Classic* guilds can use to organize rosters for 10 man raids. By aggregating different data sources, this tool can check the validity of rosters and calculate a score based on several factors, such as buff/debuff coverage, loot distribution, melee/caster balance, presence of key roles, etc. It can also be used to review signups, to ensure that everyone has marked their attendance to raids and generate list of available charcaters for that week. Finally, RosterMaster can also generate valid rosters, by exploring a given amount of randomly generated (but vaild) rosters and selecting the top five with the highest score obtained.

# ![sample-roster.png](https://raw.githubusercontent.com/MartGon/RosterMaster/main/docs/imgs/sample-roster.png)

## How to use

### Requirements

In order to use RosterMaster properly, you'll need to provide some files containing information regarding your guild's characters, signups, etc:

- **characters-db.csv:** File holding data about your guild's characters. This is mandatory in order to take into account key information such as which role each character can perform in a raid, or which character belongs to each player. You can make a copy and use [this template](https://docs.google.com/spreadsheets/d/1ENci7iaiQBf3z80y5ekUsGJzfWegMKhsQgPt28v4olE/edit?usp=drive_link) in order to fill the file with the correct format. Once ready, you can download it as CSV.

- **s[0-9].json:** Signup files. Each file has information regarding player's sign up for a given raid: whether or not they can join the raid, which character they'd like to join with, which role they can perform with that character, etc. These files can be generated easily if you use the [raid-helper bot](https://raid-helper.dev/) in your guild's discord server. Using this bot, you just need to navigate to *Web view* &rarr; *JSON* and save this file as *s[x].json* replacing *[x]* for the number corresponding to that signup.

- **r.txt:** Used by the RosterChecker module only. Holds data with the manually crafted rosters you'd like to check for validity. The content of a roster file corresponding to the image above, would be:

    ```
    0 1
    Mike	John		Joe	Candice
    Sarah	Yanny		Rose	Frank
    Alex	Laurel		Zoeh	Axel
    Tanks	Healers		Tanks	Healers
    Alice	Pablo		Mia	Taylor
    Bob	Jordan		Simon	Tina
    ```
    where the numbers in the first row correspond to the signup file each roster is gonna be validated agaisnt. In this case, the first roster (where Alice and Bob would play as tanks) would be validated agaisnt the file *s1.json*. The second roster would be validated agaisnt the signup file *s2.json*

- **contested-items.json:** Used by the RosterChecker and RosterGenerator module. File with data about which characters need specific contested items. It affects the calculated score for each roster. If at least one character which needs an specific item is present in a raid, the global score and the score obtained by that roster increases. The global score for a given set of rosters would be maximized if there's at least one character present in each raid which can use the item. E.g. this file could contain:

    ```
    "47995" : {
        "name" : "Scepter of Imprisoned Souls", "needed_by" : ["Alex", "Zoeh"]
    },
    "48032" : {
        "name" : "Lightbane Focus", "needed_by" : ["Alex", "Zoeh", "Rose"]
    }
    ```

- **(Optional) characters-json.json:** If your guild uses [That's My Bis](https://thatsmybis.com/), you can export the *Giant JSON Blob* so it can be used by the RosterChecker and RosterGenerator modules to check information about contested loot. It's just another source of the same data provided by the file described in the previous point.

### Modules

RosterMaster it's composed of three modules, each one with different utilities:

- **RosterChecker (rc.py):** Given some manually crafted rosters in a **r.txt** file, it evaluates if they're valid by checking that key roles are covered, whether a player can raid in a given day, if a player would mistakenly be using more than one character in the same raid, etc. It also calculates a score based on metrics such buff/debuff coverage, contested loot and whether rostered characters are using their main spec or not. It also prints a report giving key information about the roster, such as contested items covered or a list of benched characters. Here's an example report:

    ```
    Roster Wednesday 21:30
                dps
    Mike               John         
    Sarah              Yanny         
    Alex               Laurel           
                healer
    Pablo              Simon
                tank
    Alice              Bob       
    INFO: Item Scepter of Imprisoned Souls(47995) is covered by Alex
    INFO: Item Lightbane Focus(48032) is covered by Alex

    INFO: Buffs covered ['bloodlust', 'stamina', 'atk-pwr', 'haste%', 'spell-pwr', 'stats', 'str+agi', 'mp5', 'spell-crit', 'stats%', 'intellect', 'dmg%', 'melee-crit', 'spell-haste', 'armor', 'spirit', 'mit%', 'health']
    INFO: Debuffs covered ['major-arp', 'crit', 'minor-arp', 'spell-crit', 'spell-hit', 'bleed', 'spell-dmg']
    INFO: Buff score: 227 Debuff scoqre: 59 Total: 286

    INFO: Mortal strike provided by Mike
    INFO: Benched chars ['Michael']

    Score:  1899
    ```

    If rosters are not valid, the individual and global score would be 0.

- **SlackerDetector (sd.py):** This module can be used to generate a list of players that have not signed up to any of the raids, that is, they haven't indicated yet whether they're joining or not, hence the name. This is useful to know, as you'd like to start manually making rosters once everyone has reported which days they can raid. It also provides a list of active characters in a given week, so it's easier to manually distribute them to each raid.

- **RosterGenerator (rm.py):** This module can generate valid rosters given signup data. It explores a set number of randomly generated rosters and calculates the score of each one of them.  Then it takes the top 5, prints them to console and saves them to an output file. The result is usually a bit far from perfect, but they can still be used as base to work on manually later.

### About

Made after I became an officer of Peaky Grinders-Gehennas.