from cs50 import SQL
import csv
import datetime
import pytz
import requests
import subprocess
import urllib
import uuid
import os
import json
import random

from flask import redirect, render_template, session
from functools import wraps

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///game.db")

def apology(message, code=400):
    """Render message as an apology to user."""
    def escape(s):
        """
        Escape special characters.

        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [("-", "--"), (" ", "-"), ("_", "__"), ("?", "~q"),
                         ("%", "~p"), ("#", "~h"), ("/", "~s"), ("\"", "''")]:
            s = s.replace(old, new)
        return s
    return render_template("apology.html", top=code, bottom=escape(message)), code


def login_required(f):
    """
    Decorate routes to require login.

    http://flask.pocoo.org/docs/0.12/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function

def get_ores():
    """
    Perform mining action and return name of ore and quantity
    """
    # Construct the current full path to json file
    ores_file_path = os.path.join(os.getcwd(), "static", "ores.json")

    with open(ores_file_path, "r") as f:
        ores = json.load(f) # list of dictionaries
        chosen_ore = random.choices(ores, weights=[ore['probability'] for ore in ores])[0] # random choices returns a list even only one element will be chosen
        quantity = random.choices(chosen_ore['quantity'])[0] # random choice of quantity
        ore = chosen_ore['name']
        return [ore, quantity]

def find_animal():
    """
    Find random animal and return name, hp, attack, defense, exp, fame, loot, quantity
    """
    # Construct the current full path to json file
    animals_file_path = os.path.join(os.getcwd(), "static", "animals.json")

    with open(animals_file_path, "r") as f:
        animals = json.load(f) # list of dictionaries
        chosen_animal = random.choices(animals, weights=[animal['probability'] for animal in animals])[0] # random choices returns a list even only one element will be chosen
        animal, loot, exp, hp, attack, defense, fame = chosen_animal['name'], chosen_animal['loot'], chosen_animal['exp'], chosen_animal['hp'], chosen_animal['attk'], chosen_animal['defence'], chosen_animal['fame']
        quantity = random.choices(chosen_animal['quantity'])[0] # random choice of quantity
        return [animal, hp, attack, defense, exp, fame, loot, quantity]

def find_enemy():
    """
    Find random enemy and return name, hp, attack, defense, exp, fame, loot, quantity
    """
    # Construct the current full path to json file
    enemies_file_path = os.path.join(os.getcwd(), "static", "enemies.json")

    with open(enemies_file_path, "r") as f:
        enemies = json.load(f) # list of dictionaries
        chosen_enemy = random.choices(enemies, weights=[enemy['probability'] for enemy in enemies])[0] # random choices returns a list even only one element will be chosen
        enemy, loot, exp, hp, attack, defense, fame = chosen_enemy['name'], chosen_enemy['loot'], chosen_enemy['exp'], chosen_enemy['hp'], chosen_enemy['attk'], chosen_enemy['defence'], chosen_enemy['fame']
        quantity = random.choices(chosen_enemy['quantity'])[0] # random choice of quantity
        return [enemy, hp, attack, defense, exp, fame, loot, quantity]

def get_attacker_data(profile):
    """
    Generate attacker data from user_status of db
    """
    return [profile['hp'], profile['attk'], profile['def']]


def fight(attacker, defender):
    """
    Calculate the winner based on attacker & defender's lists of hp, attack and defense stat.
    """
    attk_hp, attk_attk, attk_def = attacker[0], attacker[1], attacker[2]
    def_hp, def_attk, def_def = defender[0], defender[1], defender[2]
    counter = 0

    # Repeat until someone hp is zero
    while (attk_hp > 0) and (def_hp > 0):
    # Round 1
        if attk_attk > def_def:
            def_hp = def_hp - (attk_attk - def_def)
        else:
            if attk_def >= def_attk:
                break
        if def_attk > attk_def:
            attk_hp = attk_hp - (def_attk - attk_def)
        counter += 1

    # Update HP of both players
    attacker[0] = attk_hp
    defender[0] = def_hp

    # Declare winner
    if attk_hp > 0 and def_hp <= 0:   # Attacker is winner and Defender is loser
        attacker.append("win")
        defender.append("dead")
    elif def_hp > 0 and attk_hp <= 0: # Defender is winner and Attacker is loser
        attacker.append("dead")
        defender.append("win")
    else:                             # Tie
        attacker.append("tie")
        defender.append("tie")

    return attacker, defender  # Return a tuple of attacker/defender hp, attack, defense and status

def bonus(userid):
    """
    Apply the bonus attack/defense based on equipped weapon/armour of userid
    """
    # Initiatize the bonus and parse user equipment
    bonus_attk = 0
    bonus_def = 0
    user_equip = db.execute("SELECT weapon, armour FROM user_status WHERE userid = ?", userid)
    user_weapon = user_equip[0]['weapon']
    user_armour = user_equip[0]['armour']

    # Look up from database the weapon and armour bonus
    # Construct the current full path to json file
    weapons_file_path = os.path.join(os.getcwd(), "static", "weapons.json")
    armours_file_path = os.path.join(os.getcwd(), "static", "armours.json")

    # bonus_attk = json file(weapon)
    with open(weapons_file_path, "r") as f:
        weapons_list = json.load(f)
    for weapon in weapons_list:
        if user_weapon == weapon['name'] :
            bonus_attk = weapon['attk_bonus']
            break

    # bonus_def = json file(armour)
    with open(armours_file_path, "r") as f:
        armours_list = json.load(f)
    for armour in armours_list:
        if user_armour == armour['name'] :
            bonus_def = armour['def_bonus']
            break

    return bonus_attk, bonus_def        # Return a tuple

def refresh(playerid):
    """
    Refresh player's level by exp, and set limit hp, stamina, basic attack and defence.
    """
    # Query the player profile
    profile = db.execute("SELECT hp, stamina, exp FROM user_status WHERE userid = ?", playerid)
    profile = profile[0]
    player_exp = profile['exp']
    player_level = db.execute("SELECT level FROM users WHERE id = ?", playerid)
    player_level = player_level[0]['level']

    # Initialize the new level as the same level in profile
    new_level = player_level

    # Construct the current full path to json file
    levels_file_path = os.path.join(os.getcwd(), "static", "levels.json")

    with open(levels_file_path, "r") as f:
        levels = json.load(f)

        # Create a loop to query the highest level possible
        for level in levels:

            # Skip the level(s) that the player already acquired
            if level['level'] > player_level:

                # Update only if level-up by exp.
                if player_exp > level['exp']:

                    # Keep track of the latest new_level for iterating next level in loop
                    new_level = level['level']

                    # Reset hp, stamina, basic attack and defence if upgrade to a new level 
                    new_hp, new_stamina, new_attk = level['hp'], level['stamina'], level['attk']
                    new_def = level['def']

                    # Reset hp, stamina, basic attack and defence and update to new level
                    db.execute("UPDATE user_status SET hp = ?, stamina = ?, attk = ?, def = ? WHERE userid = ?", new_hp, new_stamina, new_attk, new_def, playerid)
                    db.execute("UPDATE users SET level = ? WHERE id = ?", new_level, playerid)

                # Break the loop if reaching the highest level in loop
                else:
                    # If no upgrade is done, also reset HP / stamina if exceeds max. amount allowed
                    if profile['hp'] > level['hp']:
                        db.execute("UPDATE user_status SET hp = ? WHERE userid = ?", level['hp'], playerid)
                    if profile['stamina'] > level['stamina']:
                        db.execute("UPDATE user_status SET stamina = ? WHERE userid = ?", level['stamina'], playerid)
                    break            
    return True

def get_weapon_requirements(weapon_name):

    # Construct the current full path to json file
    weapons_file_path = os.path.join(os.getcwd(), "static", "weapons.json")

    with open(weapons_file_path, "r") as f:
        smith_weapons = json.load(f)
        for item in smith_weapons:
            if weapon_name == item['name']:
                weapon_requirements = item['materials']
                return weapon_requirements

def get_armour_requirements(armour_name):

    # Construct the current full path to json file
    armours_file_path = os.path.join(os.getcwd(), "static", "armours.json")

    with open(armours_file_path, "r") as f:
        smith_armours = json.load(f)
        for item in smith_armours:
            if armour_name == item['name']:
                armour_requirements = item['materials']
                return armour_requirements

def separate_coin_requirements(equip_requirements):
    new_requirements = {}
    for key, value in equip_requirements.items():
        if key == 'coins':
            coins = value
        else:
            new_requirements[key] = value
    return new_requirements, coins

def has_sufficient_materials(player_inventory, equip_requirements):
    for material, quantity_required in equip_requirements.items():
        # Check if the material is present in the player's inventory
        if material not in player_inventory:
            return False

        # Check if the player has enough of the material
        if player_inventory[material] < quantity_required:
            return False

    # If the loop completes, the player has sufficient materials
    return True

