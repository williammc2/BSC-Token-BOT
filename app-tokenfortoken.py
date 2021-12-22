import datetime
import sys
import os
import time
import requests
import asyncio
import json
import threading
from web3 import Web3
from pancakeABI import *
import argparse


print("Loading...")

sys.stdout.flush()

currentTimeStamp = ""


parser = argparse.ArgumentParser(
    description='Set your Token and Amount example: "app.py -t 0x34faa80fec0233e045ed4737cc152a71e490e2e3 -a 0.2"')
parser.add_argument(
    '-t', '--token', help='str, Token to buy e.g. "-t 0x34faa80fec0233e045ed4737cc152a71e490e2e3"')
parser.add_argument('-a', '--amount', default=0,
                    help='float, Amount in Bnb to snipe e.g. "-a 0.1"')
args = parser.parse_args()


class style():  # Class of different text colours - default is white
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    UNDERLINE = '\033[4m'
    RESET = '\033[0m'


def getTimestamp():
    while True:
        timeStampData = datetime.datetime.now()
        global currentTimeStamp
        currentTimeStamp = "[" + \
            timeStampData.strftime("%H:%M:%S.%f")[:-3] + "]"

    # -------------------------------- INITIALISE ------------------------------------------


timeStampThread = threading.Thread(target=getTimestamp)
timeStampThread.start()


numTokensDetected = 0
numTokensBought = 0
walletBalance = 0


# load json data
print("Loading configs...")
configFilePath = os.path.abspath('') + '/config.json'

with open(configFilePath, 'r') as configdata:
    data = configdata.read()

# parse file
configData = json.loads(data)

# load config data from JSON file into program
pancakeSwapRouterAddress = configData['pancakeSwapRouterAddress']
# read from JSON later
pancakeSwapFactoryAddress = '0xcA143Ce32Fe78f1f7019d7d551a6402fC5350c73'
walletAddress = configData['walletAddress']
# private key is kept safe and only used in the program
walletPrivateKey = configData['walletPrivateKey']

bscNode = configData['bscNode']


BNBAmount = float(configData['amountTokentobuy'])
# number of seconds after transaction processes to cancel it if it hasn't completed
transactionRevertTime = int(configData['transactionRevertTimeSeconds'])
gasAmount = int(configData['gasAmount'])
gasPrice = int(configData['gasPrice'])
bscScanAPIKey = configData['bscScanAPIKey']
observeOnly = configData['observeOnly']
liquidityPairAddress = configData['liquidityPairAddress']


checkSourceCode = configData['checkSourceCode']
checkValidPancakeV2 = configData['checkValidPancakeV2']
checkMintFunction = configData['checkMintFunction']
checkHoneypot = configData['checkHoneypot']
checkPancakeV1Router = configData['checkPancakeV1Router']
checkForTest = configData['checkForTest']
minLiquidityAmount = float(configData['minLiquidityAmount'])

web3 = Web3(Web3.WebsocketProvider(bscNode))

print("Connecting to BSC Node...")
if web3.isConnected():
    print(currentTimeStamp + " [Info] Web3 successfully connected")


enableMiniAudit = False

if checkSourceCode == "True" and (checkValidPancakeV2 == "True" or checkMintFunction == "True" or checkHoneypot == "True" or checkPancakeV1Router == "True"):
    enableMiniAudit = True

# check bsc balance


def checkBSCBalance():
    bscBalance = web3.fromWei(web3.eth.get_balance(walletAddress), 'ether')
    bscBalance = round(
        bscBalance, -(int("{:e}".format(bscBalance).split('e')[1]) - 4))
    print(currentTimeStamp +
          " [Info] BSC Balance: " + str(bscBalance) + " BNB")


checkBSCBalance()


def updateTitle():
    # There are references to ether in the code but it's set to BNB, its just how Web3 was originally designed
    walletBalance = web3.fromWei(web3.eth.get_balance(walletAddress), 'ether')
    # the number '4' is the wallet balance significant figures + 1, so shows 5 sig figs
    walletBalance = round(
        walletBalance, -(int("{:e}".format(walletBalance).split('e')[1]) - 4))
    sys.stdout.write("Wallet Balance: " + str(walletBalance) + " BNB")
    sys.stdout.flush()


updateTitle()


print(currentTimeStamp + " [Info] Using Wallet Address: " + walletAddress)


# ------------------------------------- BUY SPECIFIED TOKEN ON PANCAKESWAP ----------------------------------------------------------


def Buy(tokenAddress, tokenSymbol, amountToBuy):
    try:
        if(tokenAddress != None):

            tokenToBuy = web3.toChecksumAddress(tokenAddress)
            spend = web3.toChecksumAddress(
                "0xe9e7cea3dedca5984780bafc599bd69add087d56")  # BUSD contract address
            contract = web3.eth.contract(
                address=pancakeSwapRouterAddress, abi=pancakeABI)
            nonce = web3.eth.get_transaction_count(walletAddress)
            start = time.time()
            amountToBuy = web3.toWei(amountToBuy, 'ether')
            print(amountToBuy)

            # swapTokensForExactTokens
            pancakeswap2_txn = contract.functions.swapExactTokensForTokens(amountToBuy,0, [spend, tokenToBuy], walletAddress, (int(time.time()) + transactionRevertTime)).buildTransaction({'from': walletAddress,'value': 0, 'gas': gasAmount, 'gasPrice': web3.toWei(gasPrice, 'gwei'), 'nonce': nonce, })

            try:
                print("Buying the token...")

                signed_txn = web3.eth.account.sign_transaction(
                    pancakeswap2_txn, walletPrivateKey)
                tx_token = web3.eth.send_raw_transaction(
                    signed_txn.rawTransaction)  # BUY THE TOKEN


            except:
                print(style.RED + currentTimeStamp + " Transaction failed.")
                print("")  # line break: move onto scanning for next token

            txHash = str(web3.toHex(tx_token))

        # TOKEN IS BOUGHT

            checkTransactionSuccessURL = "https://api.bscscan.com/api?module=transaction&action=gettxreceiptstatus&txhash=" + \
                txHash + "&apikey=" + bscScanAPIKey
            checkTransactionRequest = requests.get(
                url=checkTransactionSuccessURL)
            txResult = checkTransactionRequest.json()['status']

            if(txResult == "1"):
                print(style.GREEN + currentTimeStamp + " [BUY] Successfully bought $" + tokenSymbol +
                      " for " + style.BLUE + str(amountToBuy) + style.GREEN + " BUSD - TX ID: ", txHash)

            else:
                print(style.RED + currentTimeStamp +
                      " [BUY] Transaction failed: likely not enough gas.")

            updateTitle()

            exit()  # exit program

    except Exception as ex:
        print(style.RED + currentTimeStamp +
              " [ERROR] Unknown error with buying token: ")
        print(ex)


tokenToBuy = "0x50332bdca94673f33401776365b66cc4e81ac81d"
tokenToBuy = web3.toChecksumAddress(tokenToBuy)

tokenSymbol = "TOKEN"

amountToBuy = "0.9"
amountToBuy = float(amountToBuy)

Buy(tokenToBuy, tokenSymbol, amountToBuy)