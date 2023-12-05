# Project Title: JiangHu - A Web Text-Based game
#### Video Demo:  <URL HERE>

#### Description – the purpose of the project and overview of use
In the CS50 course at Harvard University, I learned the basics of writing a lightweight Web API using Python and the Flask framework. 

It reminded me of an era in around 2000s, when was the blooming age of internet. There was an influx of simple text-based text games, such as the horror tower which basically you take an escalator to different levels to explore, and you will be randomly scared.

In particular, this project, inspired by the text-based games of the 2000s, aims to bring back the nostalgic charm of games like 'JiangHu'— a martial arts-themed adventure played on webpage and in live chat rooms. At that time when I was still studying primary school, there was a popular text-based game called 'JiangHu' (literally translated from Chinese meaning as lakes and rivers), meaning a sub-society where Kung Fu (i.e. martial arts) and fame was the social order and rule. The most engaging part of the game was not graphics (which it had none at all), but it appealed to the players spending hours just chatting in the room. I had a really fun and good time when playing the JiangHu.

So when I started my journey in learning computer science, it striked me a lot when I saw how Python language intertwined seamlessly with database dynamics and the Flask web API development framework. A thought blossomed—could I resurrect 'JiangHu' for a Western audience, infusing it with the knowledge acquired during the course? The answer became the driving force behind this project.

As the CS50 journey unfolded, my thoughts coalesced around this project for the final milestone. The primary motive? Pure enjoyment. This game, devoid of a traditional endpoint or 'game over,' is a testament to the joy found in the journey itself. If, during this interactive odyssey, players find themselves entertained, the project fulfills its purpose.

### Development Plan
When I crafted the timeline of the project in late November 2023, I was aware of the deadline of submission as 31st December 2023 or else my progress will be carried forward to next year. 

Crafting a timeline for the project, I navigated the looming deadline, ensuring progression without succumbing to the allure of feature bloat. This meant that I tried to avoid to be a project scope creep as it is tempting to add more and more features in the game as I developed it but I might lack the knowledge and time to develop those attractive features.

The plan meticulously arranges 'pages' and tables, categorizing them by complexity—from the simplest to the more intricate. This tiered approach ensured a feasible and gratifying development journey:

Tier 1 (Easiest): 
Pages/Activities: Ranking, Hospital, Work, Tavern 
Knowledge Applied: Practice basic iteration of database and pass into Jinja environment in HTML, Python time library  

Tier 2: 
Pages/Activities: Mining, Hunting
Knowledge Applied: Updating the database through Python, Parsing JSON files storing static data, Python random library
More complex python functions to simulate

Tier 3: 
Pages/Activities: Smith, Market, Duel
Knowledge Applied: More complex database and JSON parsing to logically allow player interactions

Tier 4: 
Pages/Activities: Register, Login, Logout, Settings
Knowledge Applied: Pages migrated from the problem set (Finance in Week 9 of CS50) for adoption in this project. 
Password changing function is added for settings.

### Getting started - Installation and Technical Requirements 
#### Dependencies
* The dependencies can be found in the 'requirements.txt' file.

#### Executing Program
* Deployment is streamlined through Heroku. Follow the guidelines in the Procfile to successfully execute the web API. I have already exhausted my knoweledge to ensure robust testing. It aimed to achieve flawless functionality.
Of course, feel free to let me know of any issue as I am still learning :)

### Game Elements
#### Register and maintainng a player profile
Creating a player account involves selecting a unique username and crafting a password. Passwords, a mix of letters, numbers, and symbols, must be at least 6 characters long. While password changes are allowed in Settings, the username remains immutable.

#### What you can do in the game and how do you know
The 'Status' page acts as a constant companion, displaying your character's statistics. Note that you can and should always refresh your status in this page, and most of the time when you perform certain actions, you will be directed to this default page.

Level progression hinges on accumulated experiences from various activities. Elevated levels translate to enhanced basic attack and defense numbers, along with a higher ceiling of HP and stamina.

Coins are only currency and are the lifeblood of the JiangHu economy, open avenues for interaction and progression. The market allows players to engage in the age-old tradition of trading. Coins become the bridge for acquiring essential items (such as forging equipment), forging alliances, and even making a successful businessman.

Beyond mere coins, fame emerges as a distinctive asset, granting players a taste of privilege and respect. In the evolving world of JiangHu, fame is not merely a statistic but it's a passport to exclusive privileges, granting you to various 'buffs' in future, such as faster rate to accumulate stamina, access to exclusive features, and more.

#### Stamina - basic requirement for activities 

Stamina serves as the cornerstone for exploring the wild facets of JiangHu. Whether working, hunting, or mining, stamina fuels these ventures. The only path to stamina recovery is resting in the tavern, accumulating 1 stamina for every minute of repose.

For instance, you need 'stamina' to work and earn extra coins, to go hunting/mining where you can get the raw materials and useful items which make you stronger.

A tip is that when you rest, it bars you from doing other activities. But you can always get up when you are ready to go!

#### Mining, Hunting- get the loot and make weapons and armours in Smith

As the name suggests, mining yields random ores crucial for crafting weapons, a safe activity fueled solely by stamina. You don't need to worry about HP reduction or even fighting with a random enemy.

Conversely, hunting poses risks, introducing the prospect of an encounter with stronger foes. In general, animals are easier than enemies. Both type of targets offer you experiences, random loot, and/or coins, and more precious fame. You are welcome to explore different option by yourself. Be wise with your choices as you progress your ability. There is a fair chance of losing the fight with a random enemy who beats you to death. 

Anyway, if you are unlucky and dead, simply go straight ahead to 'Hospital' to revive yourself. Mindful that there might be some punishments which are self-explanatory in the game.

#### Smith - a place to forge your weapons and armours
You will see the ful list of weapons/armours and their respective requirements to forge them. However, they present different pathways - recognize that each choice is a crossroad. Deliberate you decision as it affects extensively your growth!

#### Market - a public place where you can make offer to buy and sell items you got from the game

The Market in JiangHu is not just a transactional space; it's a vibrant hub where the tapestry of interactions weaves the very essence of the game.

The Market presents a golden opportunity for players to part with items in excess, crafting a symbiotic cycle where coins change hands, and treasures find new homes. It's not just about commerce; it's about camaraderie. Forge connections, gain friendship, and barter for the necessary items that propel your journey forward.

#### Duel - a place where the player can initiate a actual fight with a random player
As the most pivotal feature, the Duel is where players can showcase the fruits of their labor. It's a proving ground—a canvas where the strength of your character is on full display. Hours invested in making your character formidable find their culmination here.

While the Duel promises thrill, it's not without risk. Even in the sanctuary of the tavern, you can't evade the challenges initiated by others. It's a constant reminder that in JiangHu, the path to greatness is fraught with challenges, and even in moments of reprieve, adversity may come knocking.

Every Duel is a story, a tale that reverberates in JiangHu's history. The outcomes, whether triumphant or humbling, become part of the collective lore. The Duel is not just about winning; it's about the journey, the camaraderie, and the indomitable spirit that defines the true heroes of JiangHu.

### Future expansion ideas (no road map yet)
1. Add a live chat room
1. Add individual / co-op mission for players
1. Add adventure to collect pieces of treasure map

#### Author
Contributor name: Kelvin Wong 
Contact: kelvinwong05@gmail.com

#### Version History
2. 0.1
  - Initial Release (4/12/2023)

#### License
This project is released under the [Unlicense](https://unlicense.org/), meaning there are no restrictions on how you can use or distribute it.

#### Acknowledgments
* [CS502023 Teaching Team](https://cs50.harvard.edu/x/2023/): Truly grateful for the inspiration and guidance :gift_heart: . A heartfelt THANK YOU for such a well-organised course for free. 
This project marks the beginning of my coding journey, and now you made me believe in my ability to create something meaning on my own!
