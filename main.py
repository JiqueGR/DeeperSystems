import telebot
from pymongo import MongoClient
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime

token = "7326821694:AAHsi6XohwO-qpcJxfDgzZ8M0CYl6iXzmDY"
bot = telebot.TeleBot(token)

url = "mongodb+srv://JiqueGR:6nyk9fSLuOSeo8BL@deepsystem.itxh5.mongodb.net/DeepSystem?retryWrites=true&w=majority&appName=DeepSystem"
client = MongoClient(url)
db = client['DeepSystem']
collection = db['Bank']
temporaryValue = 0

def insertBalanceRecord(model):
    collection.insert_one(model)

def getLastRecord():
    return collection.find_one(sort=[('_id', -1)])

def getBalance():
    lastRecord = getLastRecord()
    if lastRecord:
        return lastRecord.get("balance", 0)
    return 0

def start(message):
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("Check Balance", callback_data="checkBalance"),
        InlineKeyboardButton("Deposit", callback_data="deposit"),
        InlineKeyboardButton("Withdraw", callback_data="withdraw")
    )
    bot.send_message(message.chat.id, "Choose an option:", reply_markup=markup)

@bot.message_handler(commands=['start'])
def start_message(message):
    start(message)

@bot.callback_query_handler(func=lambda call: call.data in ["checkBalance", "deposit", "withdraw"])
def callback_query(call):
    if call.data == "checkBalance":
        lastRecord = getLastRecord()
        if lastRecord is not None:
            balance = lastRecord.get('balance', 0)
            lastTransferValue = lastRecord.get('lastTransferValue', 0)
            lastTransferType = lastRecord.get('lastTransferType', 'None')
            lastTransferTime = lastRecord.get('lastTransferTime', 'None')
            bot.send_message(call.message.chat.id,
                             f"Your balance is: R${balance} "
                             f"\nLast transfer value: R${lastTransferValue} "
                             f"\nLast transfer type: {lastTransferType} "
                             f"\nLast transfer time: {lastTransferTime}")
        else:
            bot.send_message(call.message.chat.id, "No transaction records found.")
        start(call.message)
    elif call.data == "deposit":
        msg = bot.send_message(call.message.chat.id, "How much do you want to deposit?")
        bot.register_next_step_handler(msg, processDepositStep)
    elif call.data == "withdraw":
        msg = bot.send_message(call.message.chat.id, "How much do you want to withdraw?")
        bot.register_next_step_handler(msg, processWithdrawStep)

def processDepositStep(message):
    global temporaryValue
    try:
        value = int(message.text)
        if value > 0:
            temporaryValue = value
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("Confirm", callback_data="confirmDeposit"),
                       InlineKeyboardButton("Cancel", callback_data="cancelDeposit"))
            bot.send_message(message.chat.id, f"Do you want to deposit R${value}?", reply_markup=markup)
        else:
            raise ValueError
    except ValueError:
        msg = bot.send_message(message.chat.id, "Insert a number higher than 0")
        bot.register_next_step_handler(msg, processDepositStep)

@bot.callback_query_handler(func=lambda call: call.data in ["confirmDeposit", "cancelDeposit"])
def confirmDeposit(call):
    global temporaryValue
    if call.data == "confirmDeposit":
        lastTransferTime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        lastTransferType = "Deposit"
        newBalance = getBalance() + temporaryValue

        model = {
            "balance": newBalance,
            "lastTransferValue": temporaryValue,
            "lastTransferTime": lastTransferTime,
            "lastTransferType": lastTransferType
        }
        insertBalanceRecord(model)

        bot.send_message(call.message.chat.id,
                         f"Deposit of R${temporaryValue} succeeded! Your new balance is ${newBalance}.")
        start(call.message)
    elif call.data == "cancelDeposit":
        bot.send_message(call.message.chat.id, "Deposit canceled")
        start(call.message)

def processWithdrawStep(message):
    global temporaryValue
    try:
        value = int(message.text)
        balance = getBalance()
        if value > 0:
            if value <= balance:
                temporaryValue = value
                markup = InlineKeyboardMarkup()
                markup.add(InlineKeyboardButton("Confirm", callback_data="confirmWithdraw"),
                           InlineKeyboardButton("Cancel", callback_data="cancelWithdraw"))
                bot.send_message(message.chat.id, f"Do you want to withdraw R${value}?", reply_markup=markup)
            else:
                bot.send_message(message.chat.id, "Insufficient balance. Please enter a lower amount.")
                msg = bot.send_message(message.chat.id, "How much do you want to withdraw?")
                bot.register_next_step_handler(msg, processWithdrawStep)
        else:
            raise ValueError
    except ValueError:
        msg = bot.send_message(message.chat.id, "Insert a number higher than 0")
        bot.register_next_step_handler(msg, processWithdrawStep)

@bot.callback_query_handler(func=lambda call: call.data in ["confirmWithdraw", "cancelWithdraw"])
def confirmar_retiro(call):
    global temporaryValue
    if call.data == "confirmWithdraw":
        lastTransferTime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        lastTransferType = "Withdraw"
        newBalance = getBalance() - temporaryValue

        model = {
            "balance": newBalance,
            "lastTransferValue": temporaryValue,
            "lastTransferTime": lastTransferTime,
            "lastTransferType": lastTransferType
        }
        insertBalanceRecord(model)

        bot.send_message(call.message.chat.id,
                         f"Withdrawal of R${temporaryValue} succeeded! Your new balance is ${newBalance}.")
        start(call.message)
    elif call.data == "cancelWithdraw":
        bot.send_message(call.message.chat.id, "Withdrawal canceled")
        start(call.message)

bot.polling()
