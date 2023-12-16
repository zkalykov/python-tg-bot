#!/usr/bin/python3.6
import telepot
import urllib3
import csv
from collections import defaultdict
from telepot.namedtuple import InlineKeyboardButton, InlineKeyboardMarkup

# Proxy setup
proxy_url = "http://proxy.server:3128"
telepot.api._pools = {
    'default': urllib3.ProxyManager(proxy_url=proxy_url, num_pools=3, maxsize=10, retries=False, timeout=30),
}

telepot.api._onetime_pool_spec = (urllib3.ProxyManager, dict(proxy_url=proxy_url, num_pools=1, maxsize=1, retries=False, timeout=30))

bot = telepot.Bot('6532691429:AAFa8iBQgLOS2A_L840Jy3jbeIDmFwYVQMs')

# Data structure to store user's transactions and balance

ongoing_actions = {}
users_data={}

## CONNECT WITH DATABASE
# CSV file to store user's transactions and balance
csv_file = 'user_data.csv'

def create_csv():
    with open(csv_file, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Chat_ID', 'Transaction_ID', 'Description', 'Amount', 'Category'])

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
                    'amount': float(row['Amount']),
                    'category':row['Category']
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
        writer.writerow(['Chat_ID', 'Transaction_ID', 'Description', 'Amount','Category'])
        for chat_id, user_data in data.items():
            for transaction in user_data['transactions']:
                writer.writerow([chat_id, transaction['id'], transaction['description'], transaction['amount'], transaction['category'] ] )


####### CODE STARTED


def edit_delete_keyboard(chat_id,transaction_id):
    edit_button = InlineKeyboardButton(text='Edit', callback_data=f'edit_{transaction_id}')
    delete_button = InlineKeyboardButton(text='Delete', callback_data=f'delete_{transaction_id}')

    keyboard = InlineKeyboardMarkup(inline_keyboard=[[edit_button, delete_button ]])
    return keyboard

def confirm_edit_delete_keyboard(chat_id,transaction_id):
    yes_button = InlineKeyboardButton(text='Yes', callback_data=f'yes_{transaction_id}')
    no_button = InlineKeyboardButton(text='No', callback_data=f'no_{transaction_id}')

    keyboard = InlineKeyboardMarkup(inline_keyboard=[[yes_button, no_button ]])
    return keyboard
def cancel_keyboard(chat_id,transaction_id):
    button = InlineKeyboardButton(text='cancel', callback_data=f'no_{transaction_id}')
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[button]])
    return keyboard

def des_amount_cat(chat_id,transaction_id):
    des_button = InlineKeyboardButton(text='Description', callback_data=f'des_{transaction_id}')
    amount_button = InlineKeyboardButton(text='Amount', callback_data=f'amount_{transaction_id}')
    cat_button = InlineKeyboardButton(text='Category', callback_data=f'cat_{transaction_id}')

    keyboard = InlineKeyboardMarkup(inline_keyboard=[[des_button, amount_button,cat_button ]])
    return keyboard
def category_keyboard(chat_id,transaction_id):
    food= InlineKeyboardButton(text='Food', callback_data=f'food_{transaction_id}')
    gifts= InlineKeyboardButton(text='Gifts', callback_data=f'gifts_{transaction_id}')
    health_medical = InlineKeyboardButton(text='Health_medical', callback_data=f'medical_{transaction_id}')
    home= InlineKeyboardButton(text='home', callback_data=f'home_{transaction_id}')
    transportation= InlineKeyboardButton(text='transportation', callback_data=f'transportation{transaction_id}')
    personal= InlineKeyboardButton(text='personal', callback_data=f'personal_{transaction_id}')
    others= InlineKeyboardButton(text='others', callback_data=f'others_{transaction_id}')

    keyboard = InlineKeyboardMarkup(inline_keyboard=[[food], [gifts],[health_medical],[transportation],[personal],[others]])
    return keyboard

def on_callback_query(msg):
    query_id, chat_id, query_data = telepot.glance(msg, flavor='callback_query')

    # Extract the action and transaction_id from the callback_data
    action, transaction_id = query_data.split('_')

    if action == 'edit':
        bot.sendMessage(chat_id,f"EDIT here show a transacion : {query_data}",reply_markup=des_amount_cat(chat_id,transaction_id))
    elif action == 'delete':
        bot.sendMessage(chat_id, f"Are you sure to delete transaction {transaction_id} ? ", reply_markup=confirm_edit_delete_keyboard(chat_id,transaction_id))
    elif action=="yes":
        bot.sendMessage(chat_id,f"{chat_id,transaction_id}")
        handle_delete_transaction(chat_id,transaction_id)
    elif action=="no":
        if ongoing_actions[chat_id]:
            del ongoing_actions[chat_id]
        bot.sendMessage(chat_id,"Action Cancelled !")
    elif action=="des":
        bot.sendMessage(chat_id,f"Please send me a new description for transaction {transaction_id}",reply_markup=cancel_keyboard(chat_id,transaction_id) )
        ongoing_actions[chat_id]={'action':'description','id':int(transaction_id)}
        # !
    elif action=="amount":
        bot.sendMessage(chat_id,f"Please send me a new AMount for transaction {transaction_id}",reply_markup=cancel_keyboard(chat_id,transaction_id) )
        ongoing_actions[chat_id]={'action':'amount','id':int(transaction_id)}
        # !
    elif action=="cat":
        bot.sendMessage(chat_id,f"Please select one of these category for your transaction {transaction_id}",reply_markup=category_keyboard(chat_id,transaction_id) )
    elif action in ['food','gifts','medical','home','transportation','personal','others']:
        #chat_id transaction_id action
        tr=users_data[chat_id]['transactions']
        temp=0
        for detail in tr:
            if detail['id']==int(transaction_id):
                detail['category']=action
                temp=1;
                break
        if temp==1:
            bot.sendMessage(chat_id,f"Transaction : {transaction_id} has been updated !")
        else:
            bot.sendMessage(chat_id,f"Something went wrong ( !")
        save_data(users_data)
    # Add more actions if needed
    return

def handle_start(chat_id):
    instructions = "Welcome to the Expense Tracker Bot! Send your expenses or earnings in the format 'Description Amount'. For example: 'Uber tax -29.39' or 'Earned work 2000'."
    bot.sendMessage(chat_id, instructions)
    return
#####
food_keywords = ['banquet', 'bistro', 'breakfast', 'buffet', 'cafe', 'chow', 'cookery', 'cuisine', 'culinary', 'delicacy', 'dessert', 'dining', 'dinner', 'eatery', 'eatables', 'edibles', 'fast food', 'feast', 'food', 'gastronomy', 'gourmet', 'groceries', 'grocery', 'kitchen', 'lunch', 'meal', 'nutrition', 'pantry', 'patisserie', 'produce', 'refreshment', 'restaurant', 'snack', 'snack bar', 'treat', 'victuals', 'vittles']
gifts_keywords = ['advantage', 'alms', 'award', 'bequest', 'benevolence', 'benefaction', 'bestowal', 'birthday', 'blessing', 'bounty', 'celebration', 'charity', 'compensation', 'contribution', 'donation', 'dole', 'endowment', 'favor', 'gift', 'giveaway', 'goodie', 'gratuity', 'handout', 'inheritance', 'keepsake', 'legacy', 'memento', 'offering', 'perquisite', 'philanthropy', 'present', 'prize', 'remembrance', 'reward', 'souvenir', 'surprise', 'testimonial', 'tip', 'token', 'tribute', 'trophy']
health_medical_keywords = ['care', 'checkup', 'clinic', 'convalescence', 'counseling', 'disease', 'doctor', 'emergency', 'fitness', 'health', 'health center', 'health check', 'healthcare', 'hospital', 'illness', 'infirmary', 'injury', 'laboratory', 'medical', 'medical practice', 'medical supplies', 'medical treatment', 'medication', 'medicine', 'mental health', 'nurse', 'operation', 'patient', 'pharmaceutical', 'pharmacy', 'physical health', 'physician', 'prescription', 'rehabilitation', 'remedy', 'sick', 'sickroom', 'therapy', 'treatment', 'vaccine', 'wellness']
home_keywords = ['abode', 'accommodation', 'apartment', 'barn', 'bungalow', 'cabin', 'castle', 'chalet', 'condo', 'cottage', 'domestic', 'domicile', 'dwelling', 'estate', 'farmhouse', 'flat', 'habitat', 'home', 'homestead', 'house', 'household', 'living space', 'lodging', 'manor', 'mansion', 'palace', 'property', 'quarters', 'ranch', 'real estate', 'residence', 'roof', 'rooming', 'shack', 'shed', 'shelter', 'tenement', 'townhouse', 'villa']
transportation_keywords = ['airplane', 'auto', 'automobile', 'bicycle', 'bike-sharing', 'bus', 'cab', 'car', 'carpool', 'carriage', 'commute', 'commuter', 'congestion', 'drive', 'driver', 'ferry', 'gasoline', 'highway', 'hitchhike', 'hybrid', 'lyft', 'metro', 'motorbike', 'motorcycle', 'navigation', 'parking', 'pedestrian', 'public transit', 'rental', 'ride-sharing', 'road', 'road trip', 'route', 'RV', 'scooter', 'shuttle', 'subway', 'taxi', 'traffic', 'tram', 'transport', 'trolley', 'truck', 'uber', 'van', 'vehicle', 'walk']
personal_keywords = ['accessories', 'aesthetic', 'appearance', 'attire', 'attitude', 'beauty', 'care', 'character', 'cleanliness', 'clothing', 'cosmetics', 'dress', 'emotions', 'face', 'fashion', 'grooming', 'habits', 'hygiene', 'identity', 'image', 'individual', 'individualism', 'individuality', 'lifestyle', 'look', 'maintenance', 'mentality', 'outerwear', 'outfit', 'perception', 'persona', 'personal', 'personalized', 'perspective', 'presentation', 'self', 'self-care', 'self-esteem', 'self-image', 'self-respect', 'style', 'taste', 'trend', 'wardrobe']
categories_keywords = {'food': food_keywords, 'gifts': gifts_keywords, 'health_medical': health_medical_keywords, 'home': home_keywords, 'transportation': transportation_keywords, 'personal': personal_keywords, 'others': 'N/A'}

######### PREDICT categories
def predict_category(chat_id,description):
    description = description.lower()
    scores = defaultdict(float)
    t=users_data[chat_id]['transactions']

    # Check each category's keywords for matches and assign scores
    for category, keywords in categories_keywords.items():
        scores[category] = sum(description.count(keyword) for keyword in keywords)

    for ss in t:
        cat=ss['category']
        des=ss['description']
        list_des=des.split(' ')
        scores[cat] += sum(description.count(keyword) for keyword in list_des)

    # Return the category with the highest score, 'other' if no keyword matches

    best_category = max(scores, key=scores.get)
    return best_category if scores[best_category] > 0 else 'others'
    ########################
#######

def handle_description_amount(chat_id, description, amount):
    if chat_id not in users_data:
        users_data[chat_id] = {'transactions': [], 'balance': 0.0}
    pred=""
    if amount<0:
        pred=predict_category(chat_id,description)
    else:
        pred="earnings"
    # Create a new transaction
    transaction = {
        'id': len(users_data[chat_id]['transactions']) + 1,
        'description': description,
        'amount': amount,
        'category':pred
    }

    # Add the transaction to the list
    users_data[chat_id]['transactions'].append(transaction)
    users_data[chat_id]['balance'] += amount

    transaction_info = f"ID: {transaction['id']} - Transaction \"{transaction['description']}\" amount: \"{transaction['amount']}\" \nCatergy {pred}\n\nadded! \n Or you can /edit this or /delete this transaction "

    #transaction_info += f"\n{which_category(chat_id,transaction['id'])}"

    bot.sendMessage(chat_id, transaction_info, reply_markup=edit_delete_keyboard(chat_id,transaction['id']))
    save_data(users_data)

#####

def handle_transactions(chat_id):
    if chat_id in users_data:
        transactions_info = "\n".join([f"ID: {trans['id']} - Transaction \"{trans['description']}\" amount: \"{trans['amount']}\"" for trans in users_data[chat_id]['transactions']])
        balance = users_data[chat_id]['balance']
        bot.sendMessage(chat_id, f"Here's your breakdown:\n\n{transactions_info}\n\n Remaining Balance: {balance}")
    else:
        bot.sendMessage(chat_id, "You haven't added any expenses or earnings yet.")
###
def handle_categories(chat_id):
    if chat_id not in users_data:
        bot.sendMessage(chat_id, "You haven't added any expenses or earnings yet.")
        return

    tr = users_data[chat_id]['transactions']
    bl = users_data[chat_id]['balance']

    # Initialize category totals
    ct = {
        'food': 0.0,
        'gifts': 0.0,
        'health_medical': 0.0,
        'home': 0.0,
        'transportation': 0.0,
        'personal': 0.0,
        'others': 0.0,
        'earnings':0.0
    }

    # Calculate category totals
    for i in tr:
        ct[i['category']] += i['amount']

    # Display category totals
    message = "Category-wise expenses:\n"
    for category, total in ct.items():
        message += f"{category.capitalize()}: ${total:.2f}\n"

    # Optionally, you can include the overall balance
    message += f"\nOverall Balance: ${bl:.2f}"

    # Send the message to the user
    bot.sendMessage(chat_id, message)



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
    transaction_id=int(transaction_id)
    for transaction in users_data[chat_id]['transactions']:
        if transaction['id'] == transaction_id:
            transaction_to_delete = transaction
            break

    if transaction_to_delete:
        users_data[chat_id]['transactions'].remove(transaction_to_delete)
        bot.sendMessage(chat_id, f"Transaction ID: {transaction_id} has been deleted.")
    else:
        bot.sendMessage(chat_id, "Transaction not found. Please Send valid ID or /cancel action ")
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
    bot.sendMessage(chat_id,"Here is some useful commands:\n\n/categories -For categories\n\n/transactions -see transactions\n\n/delete -delete transaction\n\n/edit -edit transaction\n\n/clear_data -for clearing your data\n\nAnd so on !")
##
def handle(msg):
    content_type, chat_type, chat_id = telepot.glance(msg)

    if 'my_chat_member' in msg:
        return
    if content_type!="text" or chat_type!="private":
        return

    text = msg.get("text", "")

    if text=='/cancel':
        if ongoing_actions[chat_id]:
            del ongoing_actions[chat_id]
        bot.sendMessage(chat_id,"Action Cancelled ! ")
        return

    #############################

    if chat_id in ongoing_actions:

        if ongoing_actions[chat_id]['action']=='description':
            handle_edit_transaction(chat_id,int(ongoing_actions[chat_id]['id']),new_description=text)
        elif ongoing_actions[chat_id]['action']=='amount':
            handle_edit_transaction(chat_id,int(ongoing_actions[chat_id]['id']),new_amount=int(text))

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
        #ongoing_actions[chat_id] = {'action': 'clear_data'}
        return
    try:
        description, amount = text.rsplit(' ', 1)
        amount = float(amount)
        handle_description_amount(chat_id, description, amount)
    except ValueError:
        bot.sendMessage(chat_id,"PLease enter valid request 'Transaction and amount'")
###### CODE END
users_data=load_data()
bot.message_loop({'chat': handle, 'callback_query': on_callback_query})

print('BOT ACTIVE ...')


