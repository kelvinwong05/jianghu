import os
import ast

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import apology, login_required, get_ores, find_animal, find_enemy, get_attacker_data, fight, bonus, refresh, get_weapon_requirements, get_armour_requirements,separate_coin_requirements, has_sufficient_materials
from datetime import datetime
import random
import json

# Configure application
app = Flask(__name__)

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///game.db")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/", methods=["GET"])
@login_required
def index():
    """Show user status and history"""

    # Query user status and current time from database
    profile = db.execute("SELECT exp, stamina, coins, hp, attk, def FROM user_status WHERE userid = ?", session["user_id"])
    profile = profile[0]
    user = db.execute("SELECT username, status, fame, level FROM users WHERE id = ?", session["user_id"])
    user = user[0]
    user_regtime = db.execute("SELECT registration_time FROM users WHERE id = ?", session["user_id"])
    user_regtime = user_regtime[0]
    current_time = datetime.now()

    # Update level based on exp.
    refresh(session["user_id"])

    # Pass level, status, stamina, money, hp, attk, def, and fame to html table (done)
    # Pass the bonus attack and defence info to html table
    user_bonus = bonus(session["user_id"])

    return render_template("index.html", profile=profile, current_time=current_time, user=user, user_regtime=user_regtime, user_bonus=user_bonus)


@app.route("/ranking", methods=["GET", "POST"])
@login_required
def ranking():
    """Show all users ranking, only top 10"""

    # Query ranking status from database
    rankings = db.execute("SELECT username, level, fame, registration_time FROM users ORDER BY fame DESC LIMIT 5")
    return render_template("ranking.html", rankings=rankings)


@app.route("/market", methods=["GET", "POST"])
@login_required
def market():
    """
    Sell items to open market
    """
    items = db.execute("SELECT name, category, quantity FROM items WHERE userid = ?", session["user_id"])
    market_list = db.execute("SELECT username, name, coins, category, quantity FROM market JOIN users ON users.id = market.userid")
    profile = db.execute("SELECT coins FROM user_status WHERE userid = ?", session["user_id"])
    profile = profile[0]

    if request.method == "POST":
        # Get the inputs of selling item
        if request.form.get("sell"):
            sell = request.form.get("sell")
            sell = ast.literal_eval(sell)
            item = sell[0]
            category = sell[1]
            quantity = int(request.form.get("quantity"))
            price = request.form.get("price")

            # Validate the quantity
            actual_quantity = db.execute("SELECT quantity FROM items WHERE userid = ? AND name = ?", session["user_id"], item)
            actual_quantity = actual_quantity[0]['quantity']
            if actual_quantity < quantity:
                return apology("You cannot sell more than you have!", 400)

            # Put the offer on market at the same time update seller's item list
            db.execute("INSERT INTO market (userid, name, coins, quantity, category) VALUES (?, ?, ?, ?, ?)", session["user_id"], item, price, quantity, category)
            db.execute("UPDATE items SET quantity = quantity - ? WHERE userid = ? AND name = ?", quantity, session["user_id"], item)

            # Print success message and redirect to market page
            flash("You have successfully sell an item!")
            return redirect("/")

        elif request.form.get("buy"):
            # When accept an offer, delete item from market list, deduct coins, and then update buyer's item list
            # Convert the string to a dictionary
            buy = request.form.get("buy")
            buy = ast.literal_eval(buy)

            # Deduct coins from buyer
            db.execute("UPDATE user_status SET coins = coins - ? WHERE userid = ?", buy['coins'], session["user_id"])

            # Update buyer's item list
            check_item = db.execute("SELECT * FROM items WHERE userid = ? AND name = ?", session["user_id"], buy['name'])
            if len(check_item) == 0:
                db.execute("INSERT into items (userid, name, category, quantity) VALUES (?, ?, ?, ?)", session["user_id"], buy['name'], buy['category'], buy['quantity'])
            else:
                db.execute("UPDATE items SET quantity = quantity + ? WHERE userid = ? AND name = ?", buy['quantity'], session["user_id"], buy['name'])

            # Update seller's coins and delete from market offer
            db.execute("UPDATE user_status SET coins = coins + ? WHERE userid = ?", buy['coins'], buy['userid'])
            db.execute("DELETE FROM market WHERE userid = ? AND name = ?", buy["userid"], buy['name'])
            flash("You have successfully bought an item!")
            return redirect("/market")

        else:
            # Redirect user to home page
            return redirect("/")

    else:
        return render_template("market.html", items=items, market=market_list, profile=profile, id=session["user_id"])


@app.route("/hunting", methods=["GET", "POST"])
@login_required
def hunting():
    """Perform hunting activities"""
    user_status = db.execute("SELECT status FROM users WHERE id = ?", session["user_id"])
    status = user_status[0]['status']
    user_profile = db.execute("SELECT stamina, coins, hp, attk, def FROM user_status WHERE userid = ?", session["user_id"])
    profile = user_profile[0]

    if request.method == "POST":
        # Check the user stamina
        if profile['stamina'] < 5:
            return apology("You have insufficent stamina!", 400)
        else:
            # Update user's stamina
            db.execute("UPDATE user_status SET stamina = stamina - 5 WHERE userid = ?", session["user_id"])

            # Check the type of hunting
            if request.form.get("hunting"):
                # Generate random animal and return a list of stat in the order of name, hp, attack, defense, exp, fame, loot, quantity
                animal = find_animal()
                attacker = get_attacker_data(profile) # Polish the attacker (i.e. player)'s stat for the fight to get a list of hp, attk and def
                defender = animal[1:4]

            elif request.form.get("enemy"):
                # Generate random enemy and return a list of stat in the order of name, hp, attack, defense, exp, fame, loot, quantity
                enemy = find_enemy()
                attacker = get_attacker_data(profile) # Polish the attacker (i.e. player)'s stat for the fight to get a list of hp, attk and def
                defender = enemy[1:4]

            # Apply bonus to attacker
            equip_bonus = bonus(session["user_id"])  # return a tuple of attk and def bonus
            attacker[1] = attacker[1] + equip_bonus[0]
            attacker[2] = attacker[2] + equip_bonus[1]

            # Fight calculations (attk, def, hp)
            result = fight(attacker, defender)

            # Display result
            player_result = result[0][3]

            # If player is the winner
            if player_result == "win":
                new_hp = result[0][0]
                try:
                    new_exp = animal[4]
                    new_fame = animal[5]
                    loot = animal[6]
                    new_quantity = animal[7]
                except:
                    new_exp = enemy[4]
                    new_fame = enemy[5]
                    loot = enemy[6]
                    new_quantity = enemy[7]

                # Update hp and exp, and fame (if any)
                db.execute("UPDATE user_status SET hp = ?, exp = exp + ? WHERE userid = ?", new_hp, new_exp, session["user_id"])
                db.execute("UPDATE users SET fame = fame + ? WHERE id = ?", new_fame, session["user_id"])

                # Update user's item list
                if new_quantity != 0:
                    check_item = db.execute("SELECT * FROM items WHERE userid = ? AND name = ?", session["user_id"], loot)
                    if len(check_item) == 0:
                        db.execute("INSERT into items (userid, name, category, quantity) VALUES (?, ?, ?, ?)", session["user_id"], loot, "normal", new_quantity)
                    else:
                        db.execute("UPDATE items SET quantity = quantity + ? WHERE userid = ? AND name = ?", new_quantity, session["user_id"], loot)
                    try:
                        flash("Congratulations! You have beaten {} and gained {} {} as loot! You also gained {} exp and {} fame.".format(animal[0], new_quantity, loot, new_exp, new_fame))
                    except:
                        flash("Congratulations! You have beaten {} and gained {} {} as loot! You also gained {} exp and {} fame.".format(enemy[0], new_quantity, loot, new_exp, new_fame))
                else:
                    try:
                        flash("Congratulations! You have beaten {} and gained {} exp and {} fame.".format(animal[0], new_exp, new_fame))
                    except:
                        flash("Congratulations! You have beaten {} and gained {} exp and {} fame.".format(enemy[0], new_exp, new_fame))

            # If player is loser, set player status to 'dead' and update hp
            elif player_result == "dead":
                db.execute("UPDATE users SET status = 'dead' WHERE id = ?", session["user_id"])
                flash("You did fight hard but your opponent {} is too strong....You lost and is dead now!".format(animal[0]))
            elif player_result == "tie":
                flash("You have fought with your opponent {} for a day and a night... You two were exhausted and decided to fight next time!".format(animal[0]))
            refresh(session["user_id"])
            return redirect("/")

    else:
        return render_template("hunting.html", profile=profile, status=status)


@app.route("/mining", methods=["GET", "POST"])
@login_required
def mining():
    """
    Perform mining activities
    """
    # Query the user profile
    user_profile = db.execute("SELECT stamina, coins FROM user_status WHERE userid = ?", session["user_id"])
    profile = user_profile[0]
    user_status = db.execute("SELECT status FROM users WHERE id = ?", session["user_id"])
    status = user_status[0]['status']

    if request.method == "POST":
    # Check the user stamina
        if profile['stamina'] < 5:
            return apology("You have insufficent stamina!", 400)
    # Generate random result from get_ore, returning a list of name and quantity get.
        else:
            # Deduct the stamina
            db.execute("UPDATE user_status SET stamina = stamina - 5 WHERE userid = ?", session["user_id"])
            result = get_ores()
            if result[0] == 'stone':
                # Gain 1 coin and print a message
                db.execute("UPDATE user_status SET coins = coins + 1 WHERE userid = ?", session["user_id"])
                flash("You dug really deep....and got some useless stones - but you managed to sell them at 1 coin!")
                return redirect("/")
            else:
                # Update the user inventory
                if result[1] == 0:
                    flash("Awww! You saw {} but you couldn't reach them!".format(result[0]))
                    return redirect("/mining")
                else:
                    flash("Congratulations! You just got {} {} !".format(result[1], result[0]))
                    check = db.execute("SELECT * FROM items WHERE userid = ? AND name = ?", session["user_id"], result[0])
                    if len(check) == 0:
                        db.execute("INSERT INTO items (userid, name, category, quantity) VALUES (?, ?, ?, ?)", session["user_id"], result[0], "normal", result[1])
                    else:
                        db.execute("UPDATE items SET quantity = quantity + ? WHERE userid = ? AND name = ?", result[1], session["user_id"], result[0])
                    return redirect("/")
    else:
        print(user_status)
        return render_template("mining.html", profile=profile, status=status)


@app.route("/smith", methods=["GET", "POST"])
@login_required
def smith():
    """
    Make Weapons and Armours
    """
    # Query the profile and items on hand
    user_items = db.execute("SELECT name, quantity, category FROM items WHERE userid = ?", session["user_id"])
    profile = db.execute("SELECT stamina, coins FROM user_status WHERE userid = ?", session["user_id"])
    profile = profile[0]

    # Prepare player inventory for validation
    player_inventory = {}
    for item in user_items:
        player_inventory[item['name']] = item['quantity']

    # Construct the current full path to json file
    weapons_file_path = os.path.join(os.getcwd(), "static", "weapons.json")
    armours_file_path = os.path.join(os.getcwd(), "static", "armours.json")

    # Query the weapons and armours list
    with open(weapons_file_path, "r") as f:
        smith_weapons = json.load(f)

    with open(armours_file_path, "r") as g:
        smith_armours = json.load(g)

    # Query requirements including materials and associated quantity and coins for making the requested weapon
    if request.method == "POST":
        if request.form.get("weapon"):
            weapon_request = request.form.get("weapon")

            # Get the requirements based on the input posted
            weapon_requirements = get_weapon_requirements(weapon_request)

            # Separate coin requirements and store the coin requirement for future use
            requirements = separate_coin_requirements(weapon_requirements)
            coins = requirements[1]
            weapon_requirements = requirements[0]

            # Validate coins requirement
            user_coins = db.execute("SELECT coins FROM user_status WHERE userid = ?", session['user_id'])
            user_coins = user_coins[0]['coins']
            if user_coins < coins:
                return apology("You have not enough coins", 400)

            # Validate player inventory against weapons requirement
            result = has_sufficient_materials(player_inventory, weapon_requirements)
            if result == False:
                return apology("You have not enough materials to make the weapon!", 400)
            else:
                flash("You just made a weapon!")

            # Update coins and deduct the materials from items and player
                new_coins = db.execute("UPDATE user_status SET coins = coins - ? WHERE userid = ?", coins, session['user_id'])
                for material, quantity in weapon_requirements.items():
                    db.execute("UPDATE items SET quantity = quantity - ? WHERE userid = ? AND name = ?",
                            quantity, session['user_id'], material)

            # Add weapon to item
                for item in user_items:
                    if item['name'] == weapon_request:
                        db.execute("UPDATE items SET quantity = quantity + 1 WHERE userid = ? AND name = ?",
                                session['user_id'], weapon_request)
                        return redirect("/")
                #  Otherwise just insert the item to inventory
                db.execute("INSERT INTO items (userid, name, category, quantity) VALUES (?, ?, 'weapon', 1)",
                            session['user_id'], weapon_request)
                return redirect("/")

        # Do the same for armour
        elif request.form.get("armour"):
            armour_request = request.form.get("armour")

            # Get the requirements based on the input posted
            armour_requirements = get_armour_requirements(armour_request)

            # Separate coin requirements and store the coin requirement for future use
            requirements = separate_coin_requirements(armour_requirements)
            coins = requirements[1]
            armour_requirements = requirements[0]

            # Validate coins requirement
            user_coins = db.execute("SELECT coins FROM user_status WHERE userid = ?", session['user_id'])
            user_coins = user_coins[0]['coins']
            if user_coins < coins:
                return apology("You have not enough coins", 400)

            # Validate player inventory against weapons requirement
            result = has_sufficient_materials(player_inventory, armour_requirements)
            if result == False:
                return apology("You have not enough materials to make the weapon!", 400)
            else:
                flash("You just made an armour!")

                # Update coins and deduct the materials from items and player
                new_coins = db.execute("UPDATE user_status SET coins = coins - ? WHERE userid = ?", coins, session['user_id'])
                for material, quantity in armour_requirements.items():
                    db.execute("UPDATE items SET quantity = quantity - ? WHERE userid = ? AND name = ?",
                            quantity, session['user_id'], material)

                # Add weapon to item
                for item in user_items:
                    if item['name'] == armour_request:
                        db.execute("UPDATE items SET quantity = quantity + 1 WHERE userid = ? AND name = ?",
                                session['user_id'], weapon_request)
                        return redirect("/")
                #  Otherwise just insert the item to inventory
                db.execute("INSERT INTO items (userid, name, category, quantity) VALUES (?, ?, 'weapon', 1)",
                            session['user_id'], weapon_request)
                return redirect("/")

    else:
        return render_template("smith.html", profile=profile, user_items=user_items, weapons=smith_weapons, armours =smith_armours)


@app.route("/hospital", methods=["GET", "POST"])
@login_required
def hospital():
    """Allow player to use $ to heal hp"""

    # Query and display user's status and hp
    user = db.execute("SELECT status, fame FROM users WHERE id = ?", session["user_id"])
    status = user[0]['status']
    user_profile = db.execute("SELECT stamina, hp, coins FROM user_status WHERE userid = ?", session["user_id"])
    profile = user_profile[0]

    if request.method == "POST":
    # Show the options applicable (done in hospital.html)
        method = request.form.getlist("method")[0]
        # If dead and choose revive
        if method == 'revive':
            # Update user's fame and reset status, hp and stamina
            db.execute("UPDATE users SET fame = fame - 1, status = 'active'  WHERE id = ?", session["user_id"])
            db.execute("UPDATE user_status SET hp = 100, stamina = 0 WHERE userid = ?", session["user_id"])
            flash("You are revived!")
            return redirect("/")
        # If alive and choose one of the options
        elif method == 'acupuncture':
            # Check if enough cash, if failed, return apology
            if profile['coins'] < 5:
                return apology("You have insufficent coins!", 400)
            # Else update user's hp and cash
            else:
                db.execute("UPDATE user_status SET hp = hp + 5, coins = coins - 5 WHERE userid = ?", session["user_id"])
        # Repeat for other options
        elif method == 'guasha':
            if profile['coins'] < 20:
                return apology("You have insufficent coins!", 400)
            else:
                db.execute("UPDATE user_status SET hp = hp + 25, coins = coins - 20 WHERE userid = ?", session["user_id"])
        elif method == 'herbal':
            if profile['coins'] < 50:
                return apology("You have insufficent coins!", 400)
            else:
                db.execute("UPDATE user_status SET hp = hp + 80, coins = coins - 50 WHERE userid = ?", session["user_id"])
        else:
            flash("Invalid action. Choose again.")
            return redirect("/hospital")
        flash("You have successfully healed!")
        return redirect("/hospital")
    else:
        refresh(session["user_id"])
        return render_template("hospital.html", status=status, profile=profile)


@app.route("/work", methods=["GET", "POST"])
@login_required
def work():
    """Allow player to work to gain $"""

    # Query and display user's status, coins and stamina
    user = db.execute("SELECT status FROM users WHERE id = ?", session["user_id"])
    status = user[0]['status']
    user_profile = db.execute("SELECT stamina, coins FROM user_status WHERE userid = ?", session["user_id"])
    profile = user_profile[0]

    if request.method == "POST":
        work = request.form.getlist("work")[0]
        # Check user's stamina
        if work == 'casual':
            if profile['stamina'] < 5:
                return apology("You have insufficent stamina!", 400)
            # Else update stamina and coins
            else:
                db.execute("UPDATE user_status SET stamina = stamina - 5, coins = coins + 5 WHERE userid = ?", session["user_id"])
        # Repeat for other options
        elif work == 'catering':
            if profile['stamina'] < 20:
                return apology("You have insufficent stamina!", 400)
            else:
                db.execute("UPDATE user_status SET stamina = stamina - 20, coins = coins + 25 WHERE userid = ?", session["user_id"])
        elif work == 'escort':
            if profile['stamina'] < 50:
                return apology("You have insufficent stamina!", 400)
            else:
                db.execute("UPDATE user_status SET stamina = stamina - 50, coins = coins + 80 WHERE userid = ?", session["user_id"])
        else:
            flash("Invalid action. Choose again.")
            return redirect("/")
        flash("Congratulations! You worked and received salary!")
        return redirect("/")
    else:
        return render_template("work.html", profile=profile, status=status)


@app.route("/tavern", methods=["GET", "POST"])
@login_required
def tavern():
    """Allow player to rest, change equipment and view items"""

    # Get the file path of tavern photo
    tavern_file_path = os.path.join(os.getcwd(), "static", "tavern.jpg")

    # Query user info from database
    user = db.execute("SELECT status, fame FROM users WHERE id = ?", session["user_id"])
    status = user[0]['status']
    user_profile = db.execute("SELECT stamina, weapon, armour, time_in FROM user_status WHERE userid = ?", session["user_id"])
    profile = user_profile[0]

    # Query user items and equip from database
    user_items = db.execute("SELECT name, quantity FROM items WHERE userid = ? AND category = ?", session["user_id"], "normal")
    user_items_weapons = db.execute("SELECT name, quantity FROM items WHERE userid = ? AND category = ?", session["user_id"], "weapon")
    user_items_armours = db.execute("SELECT name, quantity FROM items WHERE userid = ? AND category = ?", session["user_id"], "armour")

    if request.method == "POST":
        # Checking-in
        if request.form.get("checkin"):
            # Check status
            if status == 'active':
                time_in = datetime.now()
                db.execute("UPDATE users SET status = ? WHERE id = ?", "busy", session["user_id"])
                # Log the time
                db.execute("UPDATE user_status SET time_in = ? WHERE userid = ?", time_in, session["user_id"])
                flash("You start to take rest!")
                return render_template("tavern.html", status=status, profile=profile, user_items_weapons=user_items_weapons, user_items_armours=user_items_armours, user_items=user_items)
            else:
                return apology("You already checked in to take rest!", 400)

        # Checking out to gain stamina
        if request.form.get("checkout"):
            # Check status
            if status == 'busy':
                time_out = datetime.now()
                time_in = db.execute("SELECT time_in FROM user_status WHERE userid = ?", session["user_id"])
                time_in = datetime.strptime(time_in[0]['time_in'], "%Y-%m-%d %H:%M:%S")
            # Calculate time difference (in minute)
                time = (time_out - time_in).total_seconds() // 60
            # Update Stamina, factor in the fame
                fame = user[0]['fame']
                if fame >= 10:
                    stamina_gain = time * (fame // 10)
                else:
                    stamina_gain = time
                db.execute("UPDATE user_status SET stamina = stamina + ? WHERE userid = ?", stamina_gain, session["user_id"])
                db.execute("UPDATE users SET status = ? WHERE id = ?", "active", session["user_id"])
                return render_template("tavern.html", status=status, profile=profile, user_items_weapons=user_items_weapons, user_items_armours=user_items_armours, user_items=user_items)
            else:
                return apology("You did not check-in!", 400)

        # Allow equip a new weapon and update inventory
        if request.form.get("weapon"):
            # Update user status (put on new equipment)
            new_weapon = request.form.get("weapon")
            old_weapon_list = db.execute("SELECT weapon FROM user_status WHERE userid = ?", session["user_id"])
            old_weapon = old_weapon_list[0]['weapon']
            db.execute("UPDATE user_status SET weapon = ? WHERE userid = ?", new_weapon, session["user_id"])

            # Update user item inventory (reduce quantity by 1)
            db.execute("UPDATE items SET quantity = quantity - 1 WHERE userid = ? AND name = ?", session["user_id"], new_weapon)
            # if quantity = 0, then remove the row (done in SQL trigger)

            # Update the equip item list (add back old equipment)
            # If no item equipped, then no need to update
            weapons_list = [item['name'] for item in user_items_weapons]
            if old_weapon is None:
                flash("You just equipped a new weapon!")
                return render_template("tavern.html", profile=profile, user_items_weapons=user_items_weapons, user_items_armours=user_items_armours, user_items=user_items)
            # If no item exist, insert the item
            elif old_weapon not in weapons_list:
                db.execute("INSERT INTO items (userid, name, category, quantity) VALUES (?, ?, ?, ?)", session["user_id"], old_weapon, "weapon", 1)
            # If there is same item, then add quantity by 1
            else:
                db.execute("UPDATE items SET quantity = quantity + 1 WHERE userid = ? AND name = ?", session["user_id"], old_weapon)
            flash("You have successfully changed a weapon!")
            return render_template("tavern.html", profile=profile, user_items_weapons=user_items_weapons, user_items_armours=user_items_armours, user_items=user_items)


        # Allow equip a new armour and update inventory
        if request.form.get("armour"):
            # Update user status (put on new equipment)
            new_armour = request.form.get("armour")
            old_armour_list = db.execute("SELECT armour FROM user_status WHERE userid = ?", session["user_id"])
            old_armour = old_armour_list[0]['armour']
            db.execute("UPDATE user_status SET armour = ? WHERE userid = ?", new_armour, session["user_id"])

            # Update user item inventory (reduce quantity by 1)
            db.execute("UPDATE items SET quantity = quantity - 1 WHERE userid = ? AND name = ?", session["user_id"], new_armour)
            # if quantity = 0, then remove the row (done in SQL trigger)

            # Update the equip item list
            # If no item equipped, then no need to update
            armours_list = [item['name'] for item in user_items_armours]
            if not old_armour:
                flash("You just equipped a new armour!")
                return render_template("tavern.html", profile=profile, user_items_weapons=user_items_weapons, user_items_armours=user_items_armours, user_items=user_items)
            # If no item exist, insert the item
            elif old_armour not in armours_list:
                db.execute("INSERT INTO items (userid, name, category, quantity) VALUES (?, ?, ?, ?)", session["user_id"], old_armour, "armour", 1)
            else:
                db.execute("UPDATE items SET quantity = quantity + 1 WHERE userid = ? AND name = ?", session["user_id"], old_armour)
            flash("You have successfully changed an armour!")
            return render_template("tavern.html", profile=profile, user_items_weapons=user_items_weapons, user_items_armours=user_items_armours, user_items=user_items)
    else:
        refresh(session["user_id"])
        return render_template("tavern.html", profile=profile, user_items_weapons=user_items_weapons, user_items_armours=user_items_armours, user_items=user_items, status=status, tavern_photo=tavern_file_path)


@app.route("/duel", methods=["GET", "POST"])
@login_required
def duel():
    """
    Find a random player to duel
    """
    # Get Duel Photo file path
    duel_file_path = os.path.join(os.getcwd(), "static", "duel.jpg")

    # Valide and use 50 stamina to find opponent player
    profile = db.execute("SELECT userid, stamina, hp, attk, def, weapon, armour FROM user_status WHERE userid = ?", session["user_id"])
    profile = profile[0]

    # Parse the history database
    history = db.execute("SELECT killer, deceased, fight_time, description FROM history LIMIT 20")

    if request.method == "POST":
        if profile['stamina'] < 50:
            return apology("You have not enough stamina!", 400)
        else:
            # Query a list of opponents and a random opponent profile except the player itself
            opponentids = db.execute("SELECT id FROM users WHERE id != ? AND status != 'dead' ", session["user_id"])
            try:
                opponentid = random.choices(opponentids)[0]['id']
            except:
                if IndexError:
                    flash("All players in JiangHu have been killed..., Try next time!")
                    return redirect("/")

            # Update Stamina now
            db.execute("UPDATE user_status SET stamina = stamina - 50 WHERE userid = ?", session["user_id"])

            # Get opponent profile
            opponent_profile = db.execute("SELECT userid, stamina, hp, attk, def, weapon, armour FROM user_status WHERE userid = ?", opponentid)
            opponent_profile = opponent_profile[0]

            # Get player and opponent duel profiles
            player_duel_profile = get_attacker_data(profile)
            opponent_duel_profile = get_attacker_data(opponent_profile)

            # Apply bonus attk and def to player and opponent before fight
            player_bonus = bonus(session["user_id"])
            player_duel_profile[1] += player_bonus[0]
            player_duel_profile[2] += player_bonus[1]
            opponent_bonus = bonus(opponentid)
            opponent_duel_profile[1] += opponent_bonus[0]
            opponent_duel_profile[2] += opponent_bonus[1]

            # Simulate the fight, return winner and loser status and hp
            result = fight(player_duel_profile, opponent_duel_profile)
            new_player_hp = result[0][0]
            new_player_status = result[0][3]
            new_opponent_hp = result[1][0]
            new_opponent_status = result[1][3]

            # Initiatize and store data to put into history database
            fight_time = datetime.now()

            # If the result is tie, print result and return
            if new_player_status == 'tie':
                flash("You and opponent had a long fight for 500 rounds - But no one can win or lose!")
                return render_template("duel.html")

            # If player wins, update opponent's status to 'dead'
            elif new_player_status == 'win':

                # Set loser status (winner does not require change) and store the result in history
                db.execute("UPDATE users SET status = 'dead' WHERE id = ?", opponentid)
                killer = db.execute("SELECT username FROM users WHERE id = ?", session["user_id"])
                killer = killer[0]['username']
                deceased = db.execute("SELECT username FROM users WHERE id = ?", opponentid)
                deceased = deceased[0]['username']

                # Deduct player's fame if opponent has zero or positive fame
                opponent_fame = db.execute("SELECT fame FROM users WHERE id = ?", opponentid)
                opponent_fame = opponent_fame[0]['fame']
                if opponent_fame >= 0:
                    db.execute("UPDATE users SET fame = fame - 10 WHERE id = ?", session["user_id"])
                    flash("You cruelly killed an ordinary player with no mercy...Your bad fame is widespread in JiangHu!")

                    # Update history
                    description = "A Cruel Murder"

                # Else increase winner's fame by 10
                else:
                    db.execute("UPDATE users SET fame = fame + 10 WHERE id = ?", session["user_id"])
                    flash("You just killed an evil player...Your good fame is widespread in JiangHu!")

                    # Update history
                    description = "A Revenge from Justice"

            # If player loses, update his status to 'dead'
            elif new_player_status == 'dead':

                # Set loser status (winner does not require change) and store the result in history
                db.execute("UPDATE users SET status = 'dead' WHERE id = ?", session["user_id"])
                killer = db.execute("SELECT username FROM users WHERE id = ?", opponentid)
                killer = killer[0]['username']
                deceased = db.execute("SELECT username FROM users WHERE id = ?", session["user_id"])
                deceased = deceased[0]['username']
                flash("You initiated a fight, but no...It wasn't even a fight at all, you immediately got killed by your opponent!")

                # Update history
                description = "A Reckless Provacation"

            # Update player and opponent's newhp, regardless of result
            db.execute("UPDATE user_status SET hp = ? WHERE userid = ?", new_player_hp, session["user_id"])
            db.execute("UPDATE user_status SET hp = ? WHERE userid = ?", new_opponent_hp, opponentid)

            # Store the history in database
            db.execute("INSERT INTO history (killer, deceased, fight_time, description) VALUES (?, ?, ?, ?)", killer, deceased, fight_time, description)
            return render_template("duel.html")
    else:
        return render_template("duel.html", history=history, duel_photo = duel_file_path)


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":
        # Get the registration date and time
        registration_time = datetime.now()

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("username must not be blank", 400)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 400)

        # Ensure re-typed password submitted
        elif not request.form.get("confirmation"):
            return apology("must retype the password", 400)

        # Ensure no same username was used
        username = request.form.get("username")
        user = db.execute("SELECT * FROM users WHERE username = ?", username)
        if len(user) > 0:
            return apology("The username already exists!", 400)

        # Ensure re-typed password matches
        password = request.form.get("password")
        repassword = request.form.get("confirmation")
        if password != repassword:
            return apology("must re-type the same password!", 400)

        # Check if the new password meets length requirement and contains some letters, numbers and symbols
        if len(password) < 6:
            return apology("password must be at least 6 characters long", 400)
        letter_count = 0
        number_count = 0
        symbol_count = 0
        for char in password:
            if char.isdigit():
                number_count += 1
            elif char.isalpha():
                letter_count += 1
            else:
                symbol_count += 1
        if (letter_count == 0) or (number_count == 0) or (symbol_count == 0):
            return apology(
                "password must contain letter(s), number(s) and symbol(s)", 400
            )

        # Pass all validation, add to user database
        db.execute(
            "INSERT INTO users (username, hash, registration_time) VALUES (?, ?, ?)",
            username,
            generate_password_hash(password, method="pbkdf2", salt_length=16),
            registration_time,
        )

        # Create a profile in user status as well
        new_user = db.execute("SELECT id FROM users WHERE username = ?", username)
        print(new_user)
        user_id = new_user[0]["id"]
        db.execute(
            "INSERT INTO user_status (userid) VALUES (?)",
            user_id,
        )
        return redirect("/")

    else:
        return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 400)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 400)

        # Query database for username
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(
            rows[0]["hash"], request.form.get("password")
        ):
            return apology("invalid username and/or password", 400)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    """Allow user to change password"""
    if request.method == "POST":
        # Ensure password was submitted
        if (
            not request.form.get("oldpassword")
            or not request.form.get("newpassword")
            or not request.form.get("confirmation")
        ):
            return apology("password(s) must not be blank", 400)

        # Retrieve old password from database
        oldpassword = request.form.get("oldpassword")
        rows = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"])
        print(rows)

        # Ensure old password is correct
        if not check_password_hash(rows[0]["hash"], oldpassword):
            return apology("invalid old password", 400)

        # Check if new password is the same as old password and same as re-typed
        newpassword = request.form.get("newpassword")
        if newpassword == oldpassword:
            return apology("new password must not be the same as old password", 400)
        if newpassword != request.form.get("confirmation"):
            return apology("must re-type the same new password", 400)

        # Check the new password meet length requirement and contains some letters, numbers and symbols
        if len(newpassword) < 6:
            return apology("new password must be at least 6 characters long", 400)
        letter_count = 0
        number_count = 0
        symbol_count = 0
        for char in newpassword:
            if char.isdigit():
                number_count += 1
            elif char.isalpha():
                letter_count += 1
            else:
                symbol_count += 1
        if (letter_count == 0) or (number_count == 0) or (symbol_count == 0):
            return apology(
                "new password must contain letter(s), number(s) and symbol(s)", 400
            )

        # Update password in database
        db.execute(
            "UPDATE users SET hash = ? WHERE id = ?",
            generate_password_hash(newpassword, method="pbkdf2", salt_length=16),
            session["user_id"],
        )
        return redirect("/")
    else:
        return render_template("settings.html")
