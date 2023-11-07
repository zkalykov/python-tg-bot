#!/usr/bin/python3.6
import telepot
import urllib3
import csv
from collections import defaultdict
from io import BytesIO
# Proxy setup
proxy_url = "http://proxy.server:3128"
telepot.api._pools = {
    'default': urllib3.ProxyManager(proxy_url=proxy_url, num_pools=3, maxsize=10, retries=False, timeout=30),
}

telepot.api._onetime_pool_spec = (urllib3.ProxyManager, dict(proxy_url=proxy_url, num_pools=1, maxsize=1, retries=False, timeout=30))

bot = telepot.Bot('6425973679:AAH3ThUf_aPjo_57-3uHUPu9s4gvmUSPjZc')

# Data structure to store user's transactions and balance

ongoing_actions = {}
users_data={}
## CONNECT WITH DATABASE


# CSV file to store user's transactions and balance
csv_file = 'user_data.csv'

def create_csv():
    with open(csv_file, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Chat_ID', 'Transaction_ID', 'Description', 'Amount'])

# Load existing data from the CSV file into a dictionary
def load_data():
    data = {}
    try:
        with open(csv_file, newline='') as file:
            reader = csv.DictReader(file)
            for row in reader:
                chat_id = int(row['Chat_ID'])
                if chat_id not in data:
                    data[chat_id] = {'transactions': [], 'balance': 0.0}
                transaction = {
                    'id': int(row['Transaction_ID']),
                    'description': row['Description'],
                    'amount': float(row['Amount'])
                }
                data[chat_id]['transactions'].append(transaction)
                data[chat_id]['balance']+=float(row['Amount'])
        return data
    except FileNotFoundError:
        create_csv()
        return {}

# Save all data to the CSV file
def save_data(data):
    with open(csv_file, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Chat_ID', 'Transaction_ID', 'Description', 'Amount'])
        for chat_id, user_data in data.items():
            for transaction in user_data['transactions']:
                writer.writerow([chat_id, transaction['id'], transaction['description'], transaction['amount']])


####### CODE STARTED

def handle_start(chat_id):
    instructions = "Welcome to the Expense Tracker Bot! Send your expenses or earnings in the format 'Description Amount'. For example: 'Uber tax -29.39' or 'Earned work 2000'."
    bot.sendMessage(chat_id, instructions)
    return
#####

food_keywords = [
        'banquet', 'bistro', 'breakfast', 'buffet', 'cafe', 'chow', 'cookery', 'cuisine', 'culinary', 'delicacy',
        'dessert', 'dining', 'dinner', 'eatery', 'eatables', 'edibles', 'fast food', 'feast', 'food', 'gastronomy',
        'gourmet', 'groceries', 'grocery', 'kitchen', 'lunch', 'meal', 'nutrition', 'pantry', 'patisserie', 'produce',
        'refreshment', 'restaurant', 'snack', 'snack bar', 'treat', 'victuals', 'vittles'
]

gifts_keywords = [
        'advantage', 'alms', 'award', 'bequest', 'benevolence', 'benefaction', 'bestowal', 'birthday', 'blessing',
        'bounty', 'celebration', 'charity', 'compensation', 'contribution', 'donation', 'dole', 'endowment', 'favor',
        'gift', 'giveaway', 'goodie', 'gratuity', 'handout', 'inheritance', 'keepsake', 'legacy', 'memento', 'offering',
        'perquisite', 'philanthropy', 'present', 'prize', 'remembrance', 'reward', 'souvenir', 'surprise', 'testimonial',
        'tip', 'token', 'tribute', 'trophy'
]

health_medical_keywords = [
        'care', 'checkup', 'clinic', 'convalescence', 'counseling', 'disease', 'doctor', 'emergency', 'fitness',
        'health', 'health center', 'health check', 'healthcare', 'hospital', 'illness', 'infirmary', 'injury',
        'laboratory', 'medical', 'medical practice', 'medical supplies', 'medical treatment', 'medication', 'medicine',
        'mental health', 'nurse', 'operation', 'patient', 'pharmaceutical', 'pharmacy', 'physical health', 'physician',
        'prescription', 'rehabilitation', 'remedy', 'sick', 'sickroom', 'therapy', 'treatment', 'vaccine', 'wellness'
]

home_keywords = [
        'abode', 'accommodation', 'apartment', 'barn', 'bungalow', 'cabin', 'castle', 'chalet', 'condo', 'cottage',
        'domestic', 'domicile', 'dwelling', 'estate', 'farmhouse', 'flat', 'habitat', 'home', 'homestead', 'house',
        'household', 'living space', 'lodging', 'manor', 'mansion', 'palace', 'property', 'quarters', 'ranch',
        'real estate', 'residence', 'roof', 'rooming', 'shack', 'shed', 'shelter', 'tenement', 'townhouse', 'villa'
]

transportation_keywords = [
        'airplane', 'auto', 'automobile', 'bicycle', 'bike-sharing', 'bus', 'cab', 'car', 'carpool', 'carriage',
        'commute', 'commuter', 'congestion', 'drive', 'driver', 'ferry', 'gasoline', 'highway', 'hitchhike', 'hybrid',
        'lyft', 'metro', 'motorbike', 'motorcycle', 'navigation', 'parking', 'pedestrian', 'public transit', 'rental',
        'ride-sharing', 'road', 'road trip', 'route', 'RV', 'scooter', 'shuttle', 'subway', 'taxi', 'traffic',
        'tram', 'transport', 'trolley', 'truck', 'uber', 'van', 'vehicle', 'walk'
]

personal_keywords = [
        'accessories', 'aesthetic', 'appearance', 'attire', 'attitude', 'beauty', 'care', 'character', 'cleanliness',
        'clothing', 'cosmetics', 'dress', 'emotions', 'face', 'fashion', 'grooming', 'habits', 'hygiene', 'identity',
        'image', 'individual', 'individualism', 'individuality', 'lifestyle', 'look', 'maintenance', 'mentality',
        'outerwear', 'outfit', 'perception', 'persona', 'personal', 'personalized', 'perspective', 'presentation',
        'self', 'self-care', 'self-esteem', 'self-image', 'self-respect', 'style', 'taste', 'trend', 'wardrobe'
]
categories_keywords = {
        'food': food_keywords,
        'gifts': gifts_keywords,
        'health_medical': health_medical_keywords,
        'home': home_keywords,
        'transportation': transportation_keywords,
        'personal': personal_keywords,
        # Add more categories and their keywords here
    }
####
def categorize_transaction(description, categories_keywords):
    # Create a score dictionary
    scores = defaultdict(float)

    # Check each category's keywords for matches and assign scores
    for category, keywords in categories_keywords.items():
        scores[category] = sum(description.count(keyword) for keyword in keywords)

    # Return the category with the highest score, 'other' if no keyword matches
    best_category = max(scores, key=scores.get)
    return best_category if scores[best_category] else 'other'

def handle_categories(chat_id):
    if chat_id not in users_data:
        bot.sendMessage(chat_id, "You haven't added any expenses or earnings yet.")
        return
    transactions=users_data[chat_id]['transactions']
    balance=users_data[chat_id]['balance']

    categories = {
        'food': 0.0,
        'gifts': 0.0,
        'health_medical': 0.0,
        'home': 0.0,
        'transportation': 0.0,
        'personal': 0.0,
        'pets': 0.0,
        'utilities': 0.0,
        'travel': 0.0,
        'debt': 0.0,
        'other': 0.0
    }

# Now the 'categories' dictionary has all the categories with their initial values set to 0.



    categories_totals = defaultdict(float)

    for transaction in transactions:
        description = transaction['description'].lower()  # Convert to lower case
        amount = transaction['amount']
        if amount >= 0:
            categories_totals['earnings'] += amount
        else:
            description = transaction['description'].lower()  # Convert to lower case
            amount = transaction['amount']
            category = categorize_transaction(description, categories_keywords)
            categories_totals[category] += amount

    # Construct the message with spending summary
    message = "Here is your spending summary:\n"
    for category, total in categories_keywords.items():
        message += f"{category.title()}: {categories_totals[category]:.2f}\n"

    message += f"\nEarnings: {categories_totals['earnings']:.2f}\n"
    message += f"\nRemaining Balance: {balance}"

    bot.sendMessage(chat_id, message)
    return
#########
def which_category(chat_id,transaction_id):
    balance=users_data[chat_id]['balance']
    transactions=users_data[chat_id]['transactions']

    categories = {
        'food': 0.0,
        'gifts': 0.0,
        'health_medical': 0.0,
        'home': 0.0,
        'transportation': 0.0,
        'personal': 0.0,
        'pets': 0.0,
        'utilities': 0.0,
        'travel': 0.0,
        'debt': 0.0,
        'other': 0.0
    }

# Now the 'categories' dictionary has all the categories with their initial values set to 0.
    categories_totals = defaultdict(float)


    # Construct the message with spending summary

    for transaction in transactions:
        if transaction['id'] != transaction_id:
            continue

        description = transaction['description'].lower()  # Convert to lower case
        amount = transaction['amount']

        if amount >= 0:
            return "Saved to EARNINGS"
        else:
            category = categorize_transaction(description, categories_keywords)
            return f"Saved to {category}"
    # Construct the message with spending summary
    return
#######
def handle_description_amount(chat_id, description, amount):
    if chat_id not in users_data:
        users_data[chat_id] = {'transactions': [], 'balance': 0.0}

    # Create a new transaction
    transaction = {
        'id': len(users_data[chat_id]['transactions']) + 1,
        'description': description,
        'amount': amount
    }

    # Add the transaction to the list
    users_data[chat_id]['transactions'].append(transaction)
    users_data[chat_id]['balance'] += amount

    transaction_info = f"ID: {transaction['id']} - Transaction \"{transaction['description']}\" amount: \"{transaction['amount']}\" added! \n Or you can /edit this or /delete this transaction"
    transaction_info += f"\n{which_category(chat_id,transaction['id'])}"
    bot.sendMessage(chat_id, transaction_info )
    save_data(users_data)

#####

def handle_transactions(chat_id):
    if chat_id in users_data:
        transactions_info = "\n".join([f"ID: {trans['id']} - Transaction \"{trans['description']}\" amount: \"{trans['amount']}\"" for trans in users_data[chat_id]['transactions']])
        balance = users_data[chat_id]['balance']
        bot.sendMessage(chat_id, f"Here's your breakdown:\n\n{transactions_info}\n\n Remaining Balance: {balance}")
    else:
        bot.sendMessage(chat_id, "You haven't added any expenses or earnings yet.")
    save_data(users_data)
###

def handle_edit_transaction(chat_id, transaction_id, new_description=None, new_amount=None):
    for transaction in users_data[chat_id]['transactions']:
        if transaction['id'] == transaction_id:
            if new_description:
                transaction['description'] = new_description
            if new_amount:
                users_data[chat_id]['balance'] -= transaction['amount']  # Remove old amount
                transaction['amount'] = new_amount
                users_data[chat_id]['balance'] += new_amount  # Add new amount

            transaction_info = f"ID: {transaction_id} - Transaction \"{transaction['description']}\" amount: \"{transaction['amount']}\" updated!"

            bot.sendMessage(chat_id, transaction_info)
            break
    save_data(users_data)
####
def handle_delete_transaction(chat_id, transaction_id):
    transaction_to_delete = None
    for transaction in users_data[chat_id]['transactions']:
        if transaction['id'] == transaction_id:
            transaction_to_delete = transaction
            break

    if transaction_to_delete:
        users_data[chat_id]['transactions'].remove(transaction_to_delete)
        bot.sendMessage(chat_id, f"Transaction ID: {transaction_id} has been deleted.")
    else:
        bot.sendMessage(chat_id, "Transaction not found.")
    save_data(users_data)
####
def handle_confirm_clear_data(chat_id):
    if chat_id in ongoing_actions and ongoing_actions[chat_id]['action'] == 'clear_data':
        users_data[chat_id] = {'transactions': [], 'balance': 0.0}
        del ongoing_actions[chat_id]
        bot.sendMessage(chat_id, "All your data has been cleared.")
    else:
        bot.sendMessage(chat_id, "There is no data clear action in progress.")
    save_data(users_data)
###
def handle_commands(chat_id):
    bot.sendMessage(chat_id,"Here is some useful commands:\n/categories -FOr categories\n/transactions -see transactions\n/delete -delete transaction\n/edit -edit transaction\n/clear_data -for clearing your data\nAnd so on !")
##
def handle(msg):
    users_data=load_data()
    content_type, chat_type, chat_id = telepot.glance(msg)
    if 'my_chat_member' in msg:
        return
    if content_type!="text" and chat_type!="private":
        return

    text = msg.get("text", "")

    if text=='/cancel':
        if ongoing_actions[chat_id]:
            del ongoing_actions[chat_id]
        bot.sendMessage(chat_id,"Action Cancelled ! ")
        return

    #############################

    if chat_id in ongoing_actions:
        #Here continue then for delete goes here
        if ongoing_actions[chat_id]['action']=="clear_data":
            if text=="/confirm_clear_data":
                handle_confirm_clear_data(chat_id)
                return
            else:
                bot.sendMessage(chat_id,"Please /confirm_clear_data or /cancel action !")
        if ongoing_actions[chat_id]['action']=="delete_by_id_asked":
            ongoing_actions[chat_id]['id']=int(text)
            bot.sendMessage(chat_id,"PLease    /confirm_delete  \n or /cancel transaction")
            ongoing_actions[chat_id]['action']="delete_by_id_asked_confirmed"
            return
        if ongoing_actions[chat_id]['action']=="delete_by_id_asked_confirmed":
            if text=="/confirm_delete":
                handle_delete_transaction(chat_id, ongoing_actions[chat_id]['id'])
                del ongoing_actions[chat_id]
                return
            else:
                bot.sendMessage(chat_id,"PLease    /confirm_delete  \n or /cancel transaction")
                return


        #### edit goes here
        if ongoing_actions[chat_id]['action']=="edit_by_id_asked":
            try:
                ongoing_actions[chat_id]['id']=int(text)
                bot.sendMessage(chat_id,"Want you want to edit /description or /amount\n or /cancerl transaction")
                ongoing_actions[chat_id]['action']="edit_by_id_asked_answered"
            except:
                bot.sendMessage(chat_id,"PLease send VALID an ID of transaction to edit\n or /cancerl transaction")
            return

        if ongoing_actions[chat_id]['action']=="edit_by_id_asked_answered":
            if text=="/description":
                bot.sendMessage(chat_id,"PLease send new description for transaction id KOY IDsin\n or /cancel transaction")
                ongoing_actions[chat_id]['action']="edit_by_id_asked_answered_description"
                return
            elif text=="/amount":
                bot.sendMessage(chat_id,"PLease send new AMOUNT for transaction id KOY IDsin\n or /cancerl transaction")
                ongoing_actions[chat_id]['action']="edit_by_id_asked_answered_amount"
                return
        ######
        if ongoing_actions[chat_id]['action']=="edit_by_id_asked_answered_description":
            try:
                handle_edit_transaction(chat_id, ongoing_actions[chat_id]['id'] ,new_description=text)
                del ongoing_actions[chat_id]
            except ValueError:
                bot.sendMessage(chat_id, "Please provide a valid  description 213.")
            return
        #### here amount edit
        if ongoing_actions[chat_id]['action']=="edit_by_id_asked_answered_amount":
            try:
                new_amount = float(text)
                handle_edit_transaction(chat_id,ongoing_actions[chat_id]['id'], new_amount=new_amount)
                del ongoing_actions[chat_id]
            except ValueError:
                bot.sendMessage(chat_id, "Please provide a valid  description 213.")
            return




    ##############################
    if text == '/start':
        handle_start(chat_id)
        return
    if text == '/categories':
        handle_categories(chat_id)
        return
    if text == '/commands':
        handle_commands(chat_id)
        return

    if text == '/transactions':
        handle_transactions(chat_id)
        return

    if text == '/edit':
        ongoing_actions[chat_id] = {'action':'edit_by_id_asked','id':-1}
        bot.sendMessage(chat_id, "Please provide the transaction ID you want to edit. Or /cancel action")
        return

    if text == '/delete':
        ongoing_actions[chat_id] = {'action':'delete_by_id_asked','id':-1}
        bot.sendMessage(chat_id, "Please provide the transaction ID you want to delete. or /cancel action")
        return

    if text == '/clear_data':
        bot.sendMessage(chat_id, "Are you sure you want to clear all your data? This action cannot be undone. Please type /confirm_clear_data to proceed. or /cancel action")
        ongoing_actions[chat_id] = {'action': 'clear_data'}
        return
    try:
        description, amount = text.rsplit(' ', 1)
        amount = float(amount)
        handle_description_amount(chat_id, description, amount)
    except ValueError:
        bot.sendMessage(chat_id,"PLease enter valid request 'Transaction and amount'")
###### CODE END
users_data=load_data()
bot.message_loop(handle)

print('BOT ACTIVE ...')


