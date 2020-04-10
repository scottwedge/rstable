import discord
import asyncio
import random
import time
import datetime
import os
import cv2
import psycopg2
import math
import numpy as np
import hashslingingslasher as hasher
from urllib.request import Request, urlopen
from discord.utils import get
from utilities import isstaff, formatok, formatfromk, pickflower, scorefp

DATABASE_URL = os.environ['DATABASE_URL']
conn = psycopg2.connect(DATABASE_URL, sslmode='require')
c=conn.cursor()
conn.set_session(autocommit=True)

# c.execute("DROP TABLE rsmoney")
# c.execute("""CREATE TABLE rsmoney (
# 				id bigint,
# 				rs3 integer,
# 				osrs integer,
# 				rs3total bigint,
# 				osrstotal bigint,
# 				rs3week bigint,
# 				osrsweek bigint,
# 				clientseed text,
# 				privacy boolean,
# 				bronze integer,
# 				silver integer,
# 				gold integer,
# 				tickets integer,
#				weeklydate text,
#				xp integer
# 				)""")
# c.execute("INSERT INTO rsmoney VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", ("546184449373634560",0,0,0,0,0,0,"None",False,0,0,0,0,"2020-01-01 00:00:00",0))
# conn.commit()

# c.execute("DROP TABLE data")
# c.execute("""CREATE TABLE data (
# 				seedreset text,
# 				serverseed text,
# 				yesterdayseed text,
# 				nonce integer,
# 				rs3profit bigint,
# 				osrsprofit bigint,
#				jackpotroll integer
# 				)""")
# c.execute("INSERT INTO data VALUES (%s, %s, %s, %s, %s, %s)", (time.strftime("%d"), hasher.create_seed(), "None", 0, 0, 0, 1000))
#conn.commit()

c.execute("DROP TABLE bj")
c.execute("""CREATE TABLE bj (
				id bigint,
				deck text,
				botcards text,
				playercards text,
				botscore integer,
				playerscore integer,
				bet integer,
				currency text,
				messageid text,
				channelid text,
				split text
				)""")
conn.commit()

c.execute("DROP TABLE roulette")
c.execute("""CREATE TABLE roulette (
				id bigint,
				bet integer,
				currency text,
				area text
				)""")
conn.commit()

# c.execute("DROP TABLE jackpot")
# c.execute("""CREATE TABLE jackpot (
# 				id bigint,
# 				bet integer,
# 				chance real
# 				)""")
# conn.commit()

# c.execute("DROP TABLE cash")
# c.execute("""CREATE TABLE cash (
# 				id text,
# 				way text,
# 				code integer,
# 				currency text,
# 				amount integer
# 				)""")
# conn.commit()

client = discord.Client()

def add_member(userid,rs3,osrs):
	c.execute("INSERT INTO rsmoney VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", (userid,rs3,osrs,0,0,0,0,"ClientSeed",False,0,0,0,0,"2020-01-01 00:00:00",0))

def getvalue(userid,value,table):
	strings=['clientseed','seedreset','serverseed','yesterdayseed','deck','botcards','playercards','currency','messageid','channelid','bets','streak','weeklydate','split']
	booleans=['privacy', 'claimed']

	if value=="07":
		value="osrs"
	try:
		c.execute("SELECT rs3 FROM rsmoney WHERE id={}".format(userid))
		tester=int(c.fetchone()[0])
	except:
		print("New Member")
		add_member(int(userid),0,0)
		return 0

	c.execute("SELECT {} FROM {} WHERE id={}".format(value, table, userid))

	if value in booleans:
		return bool(c.fetchone()[0])
	elif value in strings:
		return str(c.fetchone()[0])
	else:
		return int(c.fetchone()[0])

#amount should be in K not M
def update_money(userid,amount,currency):
	rs3=getvalue(int(userid),currency,"rsmoney")
	osrs=getvalue(int(userid),currency,"rsmoney")
	if currency=="07":
		c.execute("UPDATE rsmoney SET osrs={} WHERE id={}".format(osrs+amount, userid))
	elif currency=="rs3":
		c.execute("UPDATE rsmoney SET rs3={} WHERE id={}".format(rs3+amount, userid))

def isenough(amount, currency):
	global words
	if currency=="rs3":
		if amount<100:
			words="The minimum amount you can bet is **100k** gp RS3."
			return False, words
		else:
			return True, " "
	elif currency=="07":
		if amount<10:
			words="The minimum amount you can bet is **10k** gp 07."
			return False, words
		else:
			return True, " "

def ticketbets(userid, bet, currency):
	if currency=="rs3":
		totalbet=getvalue(userid, "rs3total","rsmoney")
		c.execute("UPDATE rsmoney SET rs3total={} WHERE id={}".format(totalbet+bet, userid))
		totalbet=getvalue(userid, "rs3week","rsmoney")
		c.execute("UPDATE rsmoney SET rs3week={} WHERE id={}".format(totalbet+bet, userid))
	elif currency=="07":
		totalbet=getvalue(userid, "osrstotal","rsmoney")
		c.execute("UPDATE rsmoney SET osrstotal={} WHERE id={}".format(totalbet+bet, userid))
		totalbet=getvalue(userid, "osrsweek","rsmoney")
		c.execute("UPDATE rsmoney SET osrsweek={} WHERE id={}".format(totalbet+bet, userid))

def getrandint(userid):
	c.execute("SELECT serverseed FROM data")
	serverseed=str(c.fetchone()[0])
	c.execute("SELECT nonce FROM data")
	nonce=int(c.fetchone()[0])
	clientseed=getvalue(userid, "clientseed","rsmoney")
	randint=hasher.getrandint(serverseed, clientseed, nonce)
	c.execute("UPDATE data SET nonce={}".format(int(nonce+1)))
	return randint

def scorebj(userid,cards,player):
	#player is a bool representing if that is player or bot score
	score=0
	aces=0
	for i in cards.split("|"):
		if i=="":
			continue
		elif i[0]=="a":
			aces+=1
		elif i[0]=="j" or i[0]=="q" or i[0]=="k" or i[:2]=="10":
			score+=10
		else:
			score+=int(i[0])
	for i in range(aces):
		if aces>1 or score>10:
			score+=1
		else:
			score+=11
	
	if player:
		c.execute("UPDATE bj SET playerscore={} WHERE id={}".format(score, userid))
	elif player == False:
		c.execute("UPDATE bj SET botscore={} WHERE id={}".format(score, userid))
	return score

def printbj(user,stood,description,color):
	def cardsToEmoji(cards, stood, bot):
		emojiCards=''
		size = 0
		if stood == False and bot:
			size = 1
			emojiCards += (str(get(client.get_all_emojis(), name="cardback")))
		for i in (cards.split("|"))[size:]:
			for emoji in client.get_all_emojis():
				if emoji.name==i:
					emojid=emoji.id
					emojiCards+=("<:"+str(i)+":"+str(emojid)+">")
		return emojiCards

	botscore = getvalue(user.id,"botscore","bj")
	playerscore = getvalue(user.id,"playerscore","bj")
	botcards = getvalue(user.id, 'botcards', 'bj')
	playercards = getvalue(user.id, 'playercards', 'bj')
	split = getvalue(user.id, 'split', 'bj')
	splitscore = scorebj(user.id, split[1:], 'Split') if split != 'None' else None
	embed = discord.Embed(description=description, color=color)

	if split != 'None':
		embed.set_author(name=str(user)[:-5]+"'s Blackjack Game - Split", icon_url=str(user.avatar_url))
	else:
		embed.set_author(name=str(user)[:-5]+"'s Blackjack Game", icon_url=str(user.avatar_url))
	if 'y' in split:
		embed.add_field(name=str(user)[:-5]+"'s First Hand - "+str(playerscore), value=cardsToEmoji(playercards, stood, False), inline=True)
		embed.add_field(name=str(user)[:-5]+"'s Second Hand - "+str(splitscore), value=cardsToEmoji(split[1:], stood, False), inline=True)
	elif 'z' in split:
		embed.add_field(name=str(user)[:-5]+"'s First Hand - "+str(splitscore), value=cardsToEmoji(split[1:], stood, False), inline=True)
		embed.add_field(name=str(user)[:-5]+"'s Second Hand - "+str(playerscore), value=cardsToEmoji(playercards, stood, False), inline=True)
	else:
		embed.add_field(name=str(user)[:-5]+"'s Hand - "+str(playerscore), value=cardsToEmoji(playercards, stood, False), inline=True)
	if stood:
		embed.add_field(name="Dealer's Hand - "+str(botscore), value=cardsToEmoji(botcards, stood, True), inline=True)
	else:
		embed.add_field(name="Dealer's Hand - ?", value=cardsToEmoji(botcards, stood, True), inline=True)

	return embed

def drawcard(userid,player):
	deck=getvalue(userid,"deck","bj")
	decklist=deck.split("|")
	index=random.randint(0, (len(decklist)-1))
	card=decklist[index]
	del decklist[index]
	deck='|'.join(decklist)
	
	if player:
		playercards=getvalue(userid,"playercards","bj")
		c.execute("UPDATE bj SET playercards='{}' WHERE id={}".format(str(playercards)+str(card)+"|", userid))
	elif player==False:
		botcards=getvalue(userid,"botcards","bj")
		c.execute("UPDATE bj SET botcards='{}' WHERE id={}".format(str(botcards)+str(card)+"|", userid))

	c.execute("UPDATE bj SET deck='{}' WHERE id={}".format(deck, userid))

def bjresult(user, bet, currency, botscore, playerscore, playercards):
			if playerscore>21:
				embed = printbj(user, True, "Sorry. You busted and lost.", 16711718)
			elif botscore>21:
				embed = printbj(user, True, "Dealer Busts. You win **"+formatfromk(bet*2, currency)+"**!", 3407616)
				update_money(user.id, bet*2, currency)
			elif playerscore==21 and playercards.count('a')==1 and (playercards.count('10')==1 or playercards.count('j')==1 or playercards.count('q')==1 or playercards.count('k')==1):
				embed = printbj(user, True, "You got a blackjack! You win **"+formatfromk(bet*2, currency)+"**!", 3407616)
				update_money(user.id, bet*2, currency)
			elif botscore==playerscore:
				embed = printbj(user, True, "Tie! Money Back.", 16776960)
				update_money(user.id, bet, currency)
			elif playerscore>botscore:
				embed = printbj(user, True, "Your score is higher than the dealer's. You win **"+formatfromk(bet*2, currency)+"**!", 3407616)
				update_money(user.id, bet*2, currency)
			elif botscore>playerscore:
				embed = printbj(user, True, "The dealer's score is higher than yours. You lose.", 16711718)
			return embed

def profit(win, currency, bet):
	if currency=="rs3":
		c.execute("SELECT rs3profit FROM data")
		rs3profit=c.fetchone()[0]
		if win:
			c.execute("UPDATE data SET rs3profit={}".format(rs3profit-bet))
		elif win==False:
			c.execute("UPDATE data SET rs3profit={}".format(rs3profit+bet))
	else:
		c.execute("SELECT osrsprofit FROM data")
		osrsprofit=c.fetchone()[0]
		if win:
			c.execute("UPDATE data SET osrsprofit={}".format(osrsprofit-bet))
		elif win==False:
			c.execute("UPDATE data SET osrsprofit={}".format(osrsprofit+bet))

def openkey(kind):
	if kind=='bronze':
		ranges=[7, 8, 9, 16, 19, 21, 23, 25, 29, 35, 56, 92, 153, 101, 91, 78, 66, 62, 55, 48, 6, 16, 24, 24, 110]
	elif kind=='silver':
		ranges=[1, 1, 10, 15, 18, 20, 35, 40, 40, 41, 43, 44, 46, 53, 56, 56, 55, 54, 51, 38, 48, 48, 56, 35, 45, 24, 24, 170, 50, 40, 100, 30, 30]
	elif kind=='gold':
		ranges=[1, 2, 3, 4, 8, 10, 22, 25, 26, 28, 40, 60, 50, 75, 65, 60, 52, 54, 56, 65, 55, 100, 69, 36, 34, 65, 170, 40, 70, 20]

	chances=[]
	for i in ranges:
		chances.append(i/sum(ranges))
		
	return random.choices(population=range(0, len(ranges)), weights=chances, k=1)

def endjackpot():
	c.execute('SELECT * FROM jackpot')
	bets=c.fetchall()
	total=sum(x[1] for x in bets)
	chances=[]

	for i in bets:
		chances.append(i[2]/100)
	winner=random.choices(population=bets, weights=chances, k=1)[0]

	update_money(winner[0], total-total*0.05, '07')
	c.execute("DROP TABLE jackpot")
	c.execute("""CREATE TABLE jackpot (
					id bigint,
					bet integer,
					chance real
					)""")
	embed = discord.Embed(description='<@'+str(winner[0])+'> has won **'+formatfromk(int(total-total*0.05),'07')+'** from the jackpot with a chance of **'+str(winner[2])+'%**!', color=5056466)
	embed.set_footer(text="Use '$add (amount)' to start a new jackpot game")
	embed.set_author(name="Jackpot Winner")
	return embed
######################################################################################

#Predefined Variables

colors=["A","B","C","D","E","F","0","1","2","3","4","5","6","7","8","9"]
nextgiveaway=0
participants=[]
roulette=41
roulettemsg=0
gif=""
override=100

async def my_background_task():
	global roulette,participants,winner,roulettemsg,gif,nextgiveaway,override
	await client.wait_until_ready()
	while not client.is_closed:
		channel = discord.Object(id='617076198740328459')
		c.execute("SELECT seedreset FROM data")
		lastdate=str(c.fetchone()[0])
		today=str(time.gmtime()[2])

		if today!=lastdate:

			if datetime.datetime.today().weekday() == 0:
				c.execute("UPDATE rsmoney SET rs3week=0")
				c.execute("UPDATE rsmoney SET osrsweek=0")

			c.execute("SELECT serverseed FROM data")
			serverseed=str(c.fetchone()[0])
			newseed=hasher.create_seed()
			c.execute("UPDATE data SET serverseed='{}'".format(newseed))
			c.execute("UPDATE data SET yesterdayseed='{}'".format(serverseed))
			c.execute("UPDATE data SET seedreset={}".format(today))
			c.execute("UPDATE data SET nonce=0")

			embed = discord.Embed(color=16724721)
			embed.set_author(name="Server Seed Updates")
			embed.add_field(name="Yesterday's Server Seed Unhashed", value=serverseed, inline=True)
			embed.add_field(name="Yesterday's Server Seed Hashed", value=hasher.hash(serverseed), inline=True)
			embed.add_field(name="Today's Server Seed Hashed", value=hasher.hash(newseed), inline=True)
			#embed.add_field(name="Today's Server Seed Unhashed", value=newseed, inline=True)
			await client.send_message(channel, embed=embed)

		else:
			if roulette<1:
				if override!=100:
					roll=override
				else:
					roll=random.randint(0,37)

				winnerids=""
				c.execute("SELECT * from roulette")
				bets=c.fetchall()
				for counter, i in enumerate(bets):
					win=False

					if i[3]=='00':
						if roll==37:
							win=True
					elif i[3].isdigit():
						if int(i[3])==roll:
							update_money(int(i[0]), int(i[1])*36, str(i[2]))
							winnerids+=("<@"+str((i[0]))+"> __Won "+formatfromk(int(i[1]*36), str(i[2]))+"__ (Bet "+i[3]+" **Payout x36**)\n")
					elif i[3]=='even':
						if roll % 2 == 0 and roll!=0:
							win=True
					elif i[3]=='odd':
						if roll % 2 != 0 and roll!=37:
							win=True
					elif i[3]=='green':
						if roll==0 or roll==37:
							update_money(int(i[0]), int(i[1])*15, str(i[2]))
							winnerids+=("<@"+str((i[0]))+"> __Won "+formatfromk(int(i[1]*15), str(i[2]))+"__ (Bet "+i[3].title()+" **Payout x15**)\n")
					elif i[3]=='black':
						if roll in [2, 4, 6, 8, 10, 11, 13, 15, 17, 20, 22, 24, 26, 28, 29, 31, 33, 35]:
							win=True
					elif i[3]=='red':
						if roll in [1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36]:
							win=True
					elif i[3]=='low':
						if 19>roll>0:
							win=True
					elif i[3]=='high':
						if 37>roll>18:
							win=True
					elif i[3]=='1st':
						if 13>roll>0:
							update_money(int(i[0]), int(i[1])*3, str(i[2]))
							winnerids+=("<@"+str((i[0]))+"> __Won "+formatfromk(int(i[1]*3), str(i[2]))+"__ (Bet "+i[3]+" **Payout x3**)\n")
					elif i[3]=='2nd':
						if 25>roll>12:
							update_money(int(i[0]), int(i[1])*3, str(i[2]))
							winnerids+=("<@"+str((i[0]))+"> __Won "+formatfromk(int(i[1]*3), str(i[2]))+"__ (Bet "+i[3]+" **Payout x3**)\n")
					elif i[3]=='3rd':
						if 37>roll>24:
							update_money(int(i[0]), int(i[1])*3, str(i[2]))
							winnerids+=("<@"+str((i[0]))+"> __Won "+formatfromk(int(i[1]*3), str(i[2]))+"__ (Bet "+i[3]+" **Payout x3**)\n")

					if win:
						update_money(int(i[0]), int(i[1])*2, str(i[2]))
						winnerids+=("<@"+str((i[0]))+"> __Won "+formatfromk(int(i[1]*2), str(i[2]))+"__ (Bet "+(i[3]).title()+" **Payout x2**)\n")

				if roll==37:
					roll='00'

				if roll in [2, 4, 6, 8, 10, 11, 13, 15, 17, 20, 22, 24, 26, 28, 29, 31, 33, 35]:
					embed = discord.Embed(description="The roulette wheel landed on **"+str(roll)+"** ⚫! Winners have been paid out!", color=0)
				elif roll in [1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36]:
					embed = discord.Embed(description="The roulette wheel landed on **"+str(roll)+"** 🔴! Winners have been paid out!", color=12977421)
				else:
					embed = discord.Embed(description="The roulette wheel landed on **"+str(roll)+"**! Winners have been paid out!", color=3800857)
				embed.set_author(name="Roulette Results", icon_url='https://images-ext-2.discordapp.net/external/ZHvyT2JKvVpfLsN1_RdcnocCsnFjJylZom7aoOFUTD8/https/cdn.discordapp.com/icons/512158131674152973/567873fba79be608443232aae21dbb7c.jpg')
				embed.set_image(url=random.choice(['https://bit.ly/3aUQk2J', 'https://bit.ly/2Wb3wwc']))
				channel = discord.Object(id='621787403778129934')
				await client.send_message(channel, embed=embed)
				if winnerids=="":
					await client.send_message(channel, "No winners.")
				else:
					await client.send_message(channel, winnerids)
				roulette=41
				override=100
				c.execute("DROP TABLE roulette")
				c.execute("""CREATE TABLE roulette (
								id bigint,
								bet integer,
								currency text,
								area text
								)""")


			elif roulette!=41 and roulette!=0:
				embed = discord.Embed(description="A game of roulette is going on! Use `bet (0-36, High/Low, Black/Red/Green, or Odd/Even) (Amount) (rs3 or 07)` to place a bet on the wheel.", color=3800857)
				embed.set_author(name="Roulette Game", icon_url='https://images-ext-2.discordapp.net/external/ZHvyT2JKvVpfLsN1_RdcnocCsnFjJylZom7aoOFUTD8/https/cdn.discordapp.com/icons/512158131674152973/567873fba79be608443232aae21dbb7c.jpg')
				embed.add_field(name="Time Left", value="**"+str(roulette)+"** Seconds", inline=True)
				embed.set_image(url=gif)
				await client.edit_message(roulettemsg, embed=embed)
				roulette-=10
			else:
				None
		# channel = discord.Object(id='566165744954638346')

		# if nextgiveaway==0:
		# 	if len(participants)<1:
		# 		embed = discord.Embed(description="Couldn't determine a giveaway winner. Next giveaway in __30 minutes__.", color=557823)
		# 		embed.set_author(name="Giveaway", icon_url="https://cdn.discordapp.com/icons/444569488491413506/fb7ac7ed9204c85dd640d86e7358f1b8.jpg")
		# 		await client.send_message(channel, embed=embed)
		# 	else:
		# 		winner=random.choice(participants)
		# 		embed = discord.Embed(description="<@"+winner+"> has won a raffle ticket! Next giveaway in __30 minutes__.", color=557823)
		# 		embed.set_author(name="Giveaway", icon_url="https://cdn.discordapp.com/icons/444569488491413506/fb7ac7ed9204c85dd640d86e7358f1b8.jpg")
		# 		await client.send_message(channel, embed=embed)
		# 		tickets=getvalue(int(message.author.id),"tickets","rsmoney")
		# 		c.execute("UPDATE rsmoney SET tickets={} WHERE id={}".format(tickets+1, winner))
		# 		participants=[]
		# 	nextgiveaway=30
		# elif nextgiveaway==7:
		# 	embed = discord.Embed(description="Say something in the next minute to be entered in a raffle ticket giveaway!", color=557823)
		# 	embed.set_author(name="Giveaway", icon_url="https://cdn.discordapp.com/icons/444569488491413506/fb7ac7ed9204c85dd640d86e7358f1b8.jpg")
		# 	await client.send_message(channel, embed=embed)
		# 	nextgiveaway-=1
		# else:
		# 	nextgiveaway-=1
		await asyncio.sleep(10)




@client.event
async def on_ready():
	print("Bot Logged In!")

# @client.event
# async def on_message_delete(message):
# 	await client.send_message(client.get_channel("473944352427868170"), str(message.author)+" said: \""+str(message.content)+"\"")

@client.event
async def on_message(message):
	global roulette,roulettemsg,gif,nextgiveaway,participants,override

	if str(message.author.id) != '580511336598077511':
		if message.content.startswith('$'):
			None
		else:
			xp = getvalue(message.author.id, 'xp', 'rsmoney')
			c.execute("UPDATE rsmoney SET xp={} WHERE id={}".format(xp + 10, message.author.id))

	message.content=(message.content).lower()

	# if nextgiveaway<=7 and message.channel.id=="580153388402999308" and message.server.id=="518832231532331018":
	# 	if str(message.author.id) not in participants and str(message.author.id)!="580511336598077511":
	# 		participants.append(str(message.author.id))

	if message.server.id!="512158131674152973" and message.server.id!="518832231532331018":
		None
	elif str(message.channel.id)=="556097134370226192":
		if message.author.id!="580511336598077511":
			await client.delete_message(message)
			embed = discord.Embed(description=str(message.content).title(), color=15925108)
			embed.set_author(name="Suggestion From "+str(message.author)[:-5], icon_url=str(message.server.icon_url))
			embed.set_footer(text="Suggested On:"+str(datetime.datetime.now())[:-7])
			embed.set_footer(text="👍 = Like | 👎 = Dislike")
			sent=await client.send_message(message.channel, embed=embed)
			await client.add_reaction(sent,"👍")
			await client.add_reaction(sent,"👎")
	#############################################
	elif message.content.startswith("$input"):
		print(message.content)
    ###########################################
	elif message.content==("$log"):
		if isstaff(message.author.id,message.server.roles,message.author.roles)=="verified":
			await client.send_message(message.channel, "Goodbye!")
			await client.logout()
		else:
			None
	################################################
	elif message.content.startswith('$colorpicker') or message.content.startswith('$colourpicker'):
		color=('')
		for i in range(6):
			color+=random.choice(colors)
		if message.content.startswith("$colorpicker"):
			await client.send_message(message.channel, "Your random color is https://www.colorhexa.com/"+color)
		elif message.content.startswith("$colourpicker"):
			await client.send_message(message.channel, "Your random colour is https://www.colorhexa.com/"+color)
	# ############################################
	elif message.content.startswith("$poll"):
		message.content=(message.content).title()
		embed = discord.Embed(description="Respond below with 👍 for YES, 👎 for NO, or 🤔 for UNSURE/NEUTRAL", color=16724721)
		embed.set_author(name=str(message.content[6:]), icon_url=str(message.server.icon_url))
		embed.set_footer(text="Polled on: "+str(datetime.datetime.now())[:-7])
		sent = await client.send_message(message.channel, embed=embed)
		await client.add_reaction(sent,"👍")
		await client.add_reaction(sent,"👎")
		await client.add_reaction(sent,"🤔")
	#############################################
	elif message.content.startswith("$userinfo"):
		try:
			int(str(message.content[12:13]))
			member=message.server.get_member(message.content[12:30])
		except:
			member=message.server.get_member(message.content[13:31])
		roles=[]
		for i in member.roles:
			if str(i)=="@everyone":
				roles.append("everyone")
			else:
				roles.append(i.name)
		embed = discord.Embed(description=" Name: "+str(member)+"\n"+
											"\nRoles: "+', '.join(roles)+"\n"+
											"\nJoined server on: "+str(member.joined_at).split(" ")[0]+"\n"+
											"\nCreated account on: "+str(member.created_at).split(" ")[0]+"\n"+
											"\nPlaying: "+str(member.game)+"\n", color=8270499)
		embed.set_author(name="Information of "+str(member)[:-5], icon_url=str(member.avatar_url))
		embed.set_footer(text="Spying on people's information isn't very nice...")
		await client.send_message(message.channel, embed=embed)
	###############################################
	elif message.content.startswith("$setseed"):
		if str(message.channel.id)=="656709120870580235":
			clientseed=str((message.content)[9:])
			if len(clientseed)>20:
				await client.send_message(message.channel, "That client seed is too long. Please try a shorter one. (20 Character Limit)")
			else:
				c.execute("UPDATE rsmoney SET clientseed='{}' WHERE id={}".format(str(clientseed), int(message.author.id)))
				await client.send_message(message.channel, "Your client seed has been set to "+(message.content)[9:]+".")
		else:
			await client.send_message(message.channel, "This command can only be used in <#656709120870580235> to prevent spam.")
	# #####################################








	###################################################
	elif message.content == '$wallet' or message.content == '$w':
		osrs=getvalue(int(message.author.id),"07","rsmoney")
		rs3=getvalue(int(message.author.id),"rs3","rsmoney")
		tickets=getvalue(int(message.author.id),"tickets","rsmoney")

		if osrs>=1000000 or rs3>=1000000:
			sidecolor=2693614
		elif osrs>=10000 or rs3>=10000:
			sidecolor=2490163
		else:
			sidecolor=12249599
		osrs=formatfromk(osrs, "osrs")
		rs3=formatfromk(rs3, "rs3")
		if rs3=="0k":
			rs3="0 k"
		if osrs=="0k":
			osrs="0 k"
		embed = discord.Embed(description='Need to load up on weekly keys? Check out our [Patreon](https://www.patreon.com/EvilBob)', color=sidecolor)
		embed.set_author(name=(str(message.author))[:-5]+"'s Wallet", icon_url=str(message.author.avatar_url))
		embed.add_field(name="RS3 Balance", value=rs3, inline=True)
		embed.add_field(name="07 Balance", value=osrs, inline=True)
		embed.add_field(name="Tickets", value=str(tickets), inline=True)
		c.execute('SELECT * FROM jackpot')
		bets=c.fetchall()
		total=sum(x[1] for x in bets)
		embed.set_footer(text="Checkout our Jackpot game, the current pot is up to "+formatfromk(total, '07')+"!")
		if getvalue(int(message.author.id), "privacy","rsmoney")==True:
			await client.send_message(message.channel, embed=embed)
		else:
			await client.send_message(message.channel, embed=embed)



	elif message.content.startswith("$wallet <@") or message.content.startswith("$w <@"):
		if message.content.startswith("$wallet <@"):
			try:
				int(str(message.content[10:11]))
				member=message.server.get_member(message.content[10:28])
			except:
				member=message.server.get_member(message.content[11:29])
		else:
			try:
				int(str(message.content[5:6]))
				member=message.server.get_member(message.content[5:23])
			except:
				member=message.server.get_member(message.content[6:24])

		if getvalue(int(member.id), "privacy","rsmoney")==False or isstaff(message.author.id,message.server.roles,message.author.roles)=="verified":
			osrs=getvalue(int(member.id),"07","rsmoney")
			rs3=getvalue(int(member.id),"rs3","rsmoney")
			tickets=getvalue(int(member.id),"tickets","rsmoney")

			if osrs>=1000000 or rs3>=1000000:
				sidecolor=2693614
			elif osrs>=10000 or rs3>=10000:
				sidecolor=2490163
			else:
				sidecolor=12249599
			osrs=formatfromk(osrs, "osrs")
			rs3=formatfromk(rs3, "rs3")
			if rs3=="0k":
				rs3="0 k"
			if osrs=="0k":
				osrs="0 k"
			embed = discord.Embed(description='Need to load up on weekly keys? Check out our [Patreon](https://www.patreon.com/EvilBob)', color=sidecolor)
			embed.set_author(name=(str(member))[:-5]+"'s Wallet", icon_url=str(member.avatar_url))
			embed.add_field(name="RS3 Balance", value=rs3, inline=True)
			embed.add_field(name="07 Balance", value=osrs, inline=True)
			embed.add_field(name="Tickets", value=str(tickets), inline=True)
			await client.send_message(message.channel, embed=embed)
			
		elif getvalue(int(member.id), "privacy","rsmoney")==True:
			await client.send_message(message.channel, "Sorry, that user has wallet privacy mode enabled.")
	##########################################
	elif message.content.startswith("$clear"):
		try:
			if isstaff(message.author.id,message.server.roles,message.author.roles)=="verified":
				try:
					int(str(message.content).split(" ")[2][2:3])
					member=message.server.get_member(str(message.content).split(" ")[2][2:-1])
				except:
					member=message.server.get_member(str(message.content).split(" ")[2][3:-1])

				if str(message.content).split(" ")[1]=="07":
					currency="07"
					c.execute("UPDATE rsmoney SET osrs={} WHERE id={}".format(0, member.id))
				elif str(message.content).split(" ")[1]=="rs3":
					currency="rs3"
					c.execute("UPDATE rsmoney SET rs3={} WHERE id={}".format(0, member.id))

				embed = discord.Embed(description="<@"+str(member.id)+">'s "+currency+" currency has been cleared. RIP", color=5174318)
				embed.set_author(name="Wallet Clearing", icon_url=str(member.avatar_url))
				await client.send_message(message.channel, embed=embed)
			else:
				await client.send_message(message.channel, "Admin Command Only!")
		except:
			await client.send_message(message.channel, "An **error** occurred. Make sure you use `$clear (rs3 or 07) (@USER)`")
	###########################################
	elif message.content.startswith("$deposit") or message.content.startswith("$withdraw"):
		try:
			if isstaff(message.author.id,message.server.roles,message.author.roles)=="verified":
				maximum=False
				if (str(message.content).split(" ")[2][-1:]).lower()=="b":
					if int(str(message.content).split(" ")[2][:-1])>100:
						await client.send_message(message.channel, "You can only give up to 100b at one time for...reasons.")
						maximum=True

				if maximum==False:
					if len((message.content).split(" "))==3:
						currency='07'
					else:
						currency=(message.content).split(" ")[3]
					amount=formatok(str(message.content).split(" ")[2], currency)

					try:
						int(str(message.content).split(" ")[1][2:3])
						member=message.server.get_member(str(message.content).split(" ")[1][2:-1])
					except:
						member=message.server.get_member(str(message.content).split(" ")[1][3:-1])

					if message.content.startswith("$deposit"):
						update_money(int(member.id), amount, currency)
					elif message.content.startswith("$withdraw"):
						update_money(int(member.id), amount*-1, currency)
	
					embed = discord.Embed(description="<@"+str(member.id)+">'s wallet has been updated.", color=5174318)
					embed.set_author(name="Update Request", icon_url=str(message.author.avatar_url))
					await client.send_message(message.channel, embed=embed)
				else:
					None
			else:
				await client.send_message(message.channel, "Admin Command Only!")
		except:
			await client.send_message(message.channel, "An **error** has occurred. Make sure you use `$update (@USER) (AMOUNT) (rs3 or 07)`.")
	############################################
	elif  message.content == '$commands' or message.content == '$cmds':
		walletcmds, wagercmds, keycmds, gamecmds, misccmds = [], [], [], [], []

		f = open('commands.txt')
		for counter, i in enumerate(f):
			if counter<7:
				walletcmds.append(i.split("|")[0] + '\n')
			elif counter>6 and counter<11:
				wagercmds.append(i.split("|")[0] + '\n')
			elif counter>10 and counter<17:
				keycmds.append(i.split("|")[0] + '\n')
			elif counter>16 and counter<28:
				gamecmds.append(i.split("|")[0] + '\n')
			else:
				misccmds.append(i.split("|")[0] + '\n')

		embed = discord.Embed(description='Use `$help (COMMAND NAME)` for a description of what that command does.\n*Example: $help $wallet*', color=16771099)
		embed.set_author(name="Bot Commands", icon_url=str(message.server.icon_url))
		embed.add_field(name='Wallet Commands', value=''.join(walletcmds), inline=True)
		embed.add_field(name='Wager Commands', value=''.join(wagercmds), inline=True)
		embed.add_field(name='Mystery Box Commands', value=''.join(keycmds), inline=True)
		embed.add_field(name='Game Commands', value=''.join(gamecmds), inline=True)
		embed.add_field(name='Miscellaneous Commands', value=''.join(misccmds), inline=True)
		await client.send_message(message.channel, embed=embed)

	elif message.content.startswith('$help'):
		try:
			command = (message.content).split(' ')[1]
			f = open('commands.txt')
			for i in f:
				if command in (i.strip('\n')).split('|')[0]:
					description = (i.strip('\n')).split('|')[2] + '\n\nUsage: `' + i.split('|')[1] + '`'
					break
			embed = discord.Embed(description='This command ' + str(description), color=16771099)
			embed.set_author(name="Command Explanation", icon_url=str(message.server.icon_url))
			await client.send_message(message.channel, embed=embed)
		except:
			await client.send_message(message.channel, 'That command could not be found, use `$commands` or `$cmds` for a list of commands.')
	###################################
	elif message.content.startswith("$transfer"):
		try:
			if len((message.content).split(" "))==3:
				currency='07'
			else:
				currency=(message.content).split(" ")[3]

			transfered=formatok((message.content).split(" ")[2], currency)
			current=getvalue(int(message.author.id),currency,"rsmoney")

			if transfered>1:
				if current>=transfered:
					try:
						int(str(message.content).split(" ")[1][2:3])
						member=message.server.get_member(str(message.content).split(" ")[1][2:-1])
					except:
						member=message.server.get_member(str(message.content).split(" ")[1][3:-1])
					
					if str(member.id)==str(message.author.id):
						await client.send_message(message.channel, "You can't transfer money to yourself 😂")
					else:
						taker=getvalue(int(member.id),currency,"rsmoney")
				
						if currency=="rs3":
							c.execute("UPDATE rsmoney SET rs3={} WHERE id={}".format(current-transfered, message.author.id))
							c.execute("UPDATE rsmoney SET rs3={} WHERE id={}".format(taker+transfered, member.id))
						elif currency=="07":
							c.execute("UPDATE rsmoney SET osrs={} WHERE id={}".format(current-transfered, message.author.id))
							c.execute("UPDATE rsmoney SET osrs={} WHERE id={}".format(taker+transfered, member.id))

						embed = discord.Embed(description="<@"+str(message.author.id)+"> has transfered "+str(formatfromk(transfered, currency))+" "+currency+" to <@"+str(member.id)+">'s wallet.", color=5174318)
						embed.set_author(name="Transfer Request", icon_url=str(message.author.avatar_url))
						await client.send_message(message.channel, embed=embed)
				else:
					await client.send_message(message.channel, "<@"+str(message.author.id)+">, You don't have enough money to transfer that amount!")
			else:
				await client.send_message(message.channel, "You must transfer at least **1k** "+currency+".")
		except:
			await client.send_message(message.channel, "An **error** has occurred. Make sure you use `$transfer (@USER) (AMOUNT) (rs3 or 07)`.")
	###################################
	elif message.content.startswith("$53") or message.content.startswith("$50") or message.content.startswith("$75") or message.content.startswith("$95"):
		if str(message.channel.id) in ['570857748451950603', '563836659003686913', '558011134074945536', '570857634299772929']:
			try:
				if len((message.content).split(" "))==2:
					currency='07'
				else:
					currency=str(message.content).split(" ")[2]
				bet=formatok(str(message.content).split(" ")[1], currency)
				current=getvalue(message.author.id, currency,"rsmoney")

				if isenough(bet, currency)[0]:
					if message.content.startswith("$53x2") or message.content.startswith("$53"):
						title, odds, multiplier = '53x2', 54, 2
					elif message.content.startswith("$50x1.8") or message.content.startswith("$50"):
						title, odds, multiplier = '50x1.8', 51, 1.8
					elif message.content.startswith("$75x3") or message.content.startswith("$75"):
						title, odds, multiplier = '75x3', 76, 3
					elif message.content.startswith("$95x7") or message.content.startswith("$95"):
						title, odds, multiplier = '95x7', 96, 7

					if current>=bet:
						roll=getrandint(message.author.id)

						if roll in range(1,odds):
							winnings = bet
							words = "Rolled **"+str(roll)+"** out of **100**. You lost **"+str(formatfromk(bet, currency))+"** "+str(currency)+"."
							sidecolor, gains, win = 16718121, (bet*-1), False
						else:
							winnings = formatfromk(int(bet*multiplier), currency)
							words = "Rolled **"+str(roll)+"** out of **100**. You won **"+str(winnings)+"** "+str(currency)+"."	
							winnings = formatok(winnings, currency)
							sidecolor, gains, win = 3997475, ((bet*multiplier)-bet), True

						update_money(int(message.author.id), gains, currency)

						c.execute("SELECT nonce FROM data")
						nonce=int(c.fetchone()[0])
						clientseed=getvalue(message.author.id, "clientseed", "rsmoney")

						embed = discord.Embed(color=sidecolor)
						embed.set_author(name=str(message.author), icon_url=str(message.author.avatar_url))
						embed.add_field(name=title, value=words, inline=True)
						embed.set_footer(text="Nonce: "+str(nonce-1)+" | Client Seed: \""+str(clientseed)+"\"")
						await client.send_message(message.channel, embed=embed)

						ticketbets(message.author.id, bet, currency)
						profit(win, currency, winnings)

					else:
						await client.send_message(message.channel, "<@"+str(message.author.id)+">, you don't have that much gold!")
				else:
					await client.send_message(message.channel, (isenough(bet, currency))[1])
			except:
				await client.send_message(message.channel, "An **error** has occurred. Make sure you use `$(50, 53, 75, or 95) (BET) (rs3 or 07)`.")
		else:
			await client.send_message(message.channel, "This command can only be used in one of the dicing channels.")
	#############################
	elif message.content == '$wager' or message.content == '$total bet' or message.content == '$tb':
		rs3total=getvalue(message.author.id, "rs3total","rsmoney")
		osrstotal=getvalue(message.author.id, "osrstotal","rsmoney")

		osrs=formatfromk(osrstotal, "osrs")
		rs3=formatfromk(rs3total, "rs3")

		embed = discord.Embed(color=16766463)
		embed.set_author(name=(str(message.author))[:-5]+"'s Total Bets", icon_url=str(message.author.avatar_url))
		embed.add_field(name="RS3 Total Bets", value=rs3, inline=True)
		embed.add_field(name="07 Total Bets", value=osrs, inline=True)
		c.execute('SELECT * FROM jackpot')
		bets=c.fetchall()
		total=sum(x[1] for x in bets)
		embed.set_footer(text="Checkout our Jackpot game, the current pot is up to "+formatfromk(total, '07')+"!")
		await client.send_message(message.channel, embed=embed)
	###############################
	elif message.content == '$thisweek':
		rs3week=getvalue(message.author.id, "rs3week","rsmoney")
		osrsweek=getvalue(message.author.id, "osrsweek","rsmoney")

		osrs=formatfromk(osrsweek, "osrs")
		rs3=formatfromk(rs3week, "rs3")

		embed = discord.Embed(color=16766463)
		embed.set_author(name=(str(message.author))[:-5]+"'s Weekly Bets", icon_url=str(message.author.avatar_url))
		embed.add_field(name="RS3 Weekly Bets", value=rs3, inline=True)
		embed.add_field(name="07 Weekly Bets", value=osrs, inline=True)
		await client.send_message(message.channel, embed=embed)
	################################
	elif message.content == '$reset thisweek':
		if isstaff(message.author.id,message.server.roles,message.author.roles)=="verified":
			c.execute("UPDATE rsmoney SET rs3week=0")
			c.execute("UPDATE rsmoney SET osrsweek=0")
			embed = discord.Embed(description="All weekly bets have been reset.", color=5174318)
			embed.set_author(name="Weekly Bets Reset", icon_url=str(message.server.icon_url))
			await client.send_message(message.channel, embed=embed)
		else:
			await client.send_message(message.channel, "Admin Command Only!")
	###############################
	elif message.content == '$privacy on':
		c.execute("UPDATE rsmoney SET privacy=True WHERE id={}".format(message.author.id))
		embed = discord.Embed(description="<@"+str(message.author.id)+">'s wallet privacy is now enabled.", color=5174318)
		embed.set_author(name="Privacy Mode", icon_url=str(message.author.avatar_url))
		await client.send_message(message.channel, embed=embed)

	elif message.content == '$privacy off':
		c.execute("UPDATE rsmoney SET privacy=False WHERE id={}".format(message.author.id))
		embed = discord.Embed(description="<@"+str(message.author.id)+">'s wallet privacy is now disabled.", color=5174318)
		embed.set_author(name="Privacy Mode", icon_url=str(message.author.avatar_url))
		await client.send_message(message.channel, embed=embed)
	#################################
	elif message.content.startswith('$bj'):
		if str(message.channel.id) == '585143700129185829' or str(message.channel.id) == '617144512409501696':
			try:
				deck="aC|aS|aH|aD|2C|2S|2H|2D|3C|3S|3H|3D|4C|4S|4H|4D|5C|5S|5H|5D|6C|6S|6H|6D|7C|7S|7H|7D|8C|8S|8H|8D|9C|9S|9H|9D|10C|10S|10H|10D|jC|jS|jH|jD|qC|qS|qH|qD|kC|kS|kH|kD"
				if len((message.content).split(" "))==2:
					currency='07'
				else:
					currency=(message.content).split(" ")[2]

				bet=formatok((message.content).split(" ")[1], currency)
				current=getvalue(int(message.author.id), currency, "rsmoney")

				if isenough(bet, currency)[0]:
					if current>=bet:
						try:
							c.execute("SELECT playerscore FROM bj WHERE id={}".format(message.author.id))
							tester=int(c.fetchone()[0])
							await client.send_message(message.channel, "You are already in a game of blackjack! Type `hit`, `stand`, or `dd` to continue the game!")
						except:
							update_money(message.author.id, bet*-1, currency)
							ticketbets(message.author.id, bet, currency)
							c.execute("INSERT INTO bj VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", (message.author.id, deck, '', '', 0, 0, bet, currency, '', str(message.channel.id), 'None'))
							drawcard(message.author.id, True)
							drawcard(message.author.id, True)
							drawcard(message.author.id, False)
							drawcard(message.author.id, False)
							botcards = getvalue(message.author.id, "botcards", "bj")
							playercards = getvalue(message.author.id, "playercards", "bj")
							scorebj(message.author.id,botcards, False)
							scorebj(message.author.id,playercards, True)
							sent = await client.send_message(message.channel, embed=printbj(message.author, False, "Use `hit` to draw, `stand` to pass, `dd` to double down, or `split` to split.", 28))
							c.execute("UPDATE bj SET messageid={} WHERE id={}".format(str(sent.id), message.author.id))
					else:
						await client.send_message(message.channel, "<@"+str(message.author.id)+">, you don't have that much gold!")
				else:
					await client.send_message(message.channel, isenough(bet, currency)[1])
			except:
				await client.send_message(message.channel, "An **error** has occurred. Make sure you use `$bj (AMOUNT) (rs3 or 07)`.")
		else:
			await client.send_message(message.channel, "This command can only be used in <#585143700129185829>.")
	################################
	elif message.content == 'hit':
		drawcard(message.author.id, True)
		playercards = getvalue(message.author.id,"playercards","bj")
		playerscore = scorebj(message.author.id,playercards,True)
		botcards = getvalue(message.author.id, 'botcards', 'bj')
		botscore = getvalue(message.author.id, 'botscore', 'bj')
		messageid = getvalue(message.author.id,"messageid","bj")
		channelid = getvalue(message.author.id,"channelid","bj")
		currency = getvalue(message.author.id,"currency","bj")
		bet = getvalue(message.author.id,"bet","bj")
		split = getvalue(message.author.id, 'split', 'bj')
		sent = await client.get_message(message.server.get_channel(channelid), messageid)

		if playerscore>21:
			if 'y' in split:
				c.execute("UPDATE bj SET playercards='{}' WHERE id={}".format(split[1:], message.author.id))
				c.execute("UPDATE bj SET split='{}' WHERE id={}".format('z'+playercards, message.author.id))
				botcards = getvalue(message.author.id, "botcards", "bj")
				playercards = getvalue(message.author.id, "playercards", "bj")
				scorebj(message.author.id, botcards, False)
				scorebj(message.author.id, playercards, True)
				await client.edit_message(sent, embed=printbj(message.author, False, "Use `hit` to draw, `stand` to pass, or `dd` to double down for hand two.", 28))
			elif split == 'None':
				await client.edit_message(sent, embed=printbj(message.author, True, "Sorry. You busted and lost.", 16711718))
				c.execute("DELETE FROM bj WHERE id={}".format(message.author.id))
			else:
				await client.delete_message(sent)
				splitscore = scorebj(message.author.id, split[1:], 'Split')
				embed1 = bjresult(message.author, bet, currency, botscore, splitscore, split[1:])
				embed2 = bjresult(message.author, bet, currency, botscore, playerscore, playercards)
				embed1.set_author(name=str(message.author)[:-5]+"'s Blackjack Hand 1 Result", icon_url=str(message.author.avatar_url))
				embed2.set_author(name=str(message.author)[:-5]+"'s Blackjack Hand 2 Result", icon_url=str(message.author.avatar_url))
				await client.send_message(message.channel, embed=embed1)
				await client.send_message(message.channel, embed=embed2)
				c.execute("DELETE FROM bj WHERE id={}".format(message.author.id))
		else:
			await client.edit_message(sent, embed=printbj(message.author, False, "Use `hit` to draw, `stand` to pass, `dd` to double down, or `split` to split.", 28))
	###################################
	elif message.content == 'stand' or message.content == 'dd':
		currency = getvalue(message.author.id,"currency","bj")
		playerscore = getvalue(message.author.id,"playerscore","bj")
		playercards = getvalue(message.author.id,"playercards","bj")
		botcards = getvalue(message.author.id,"botcards","bj")
		messageid = getvalue(message.author.id,"messageid","bj")
		channelid = getvalue(message.author.id,"channelid","bj")
		current = getvalue(int(message.author.id), currency, "rsmoney")
		bet = getvalue(message.author.id,"bet","bj")
		split = getvalue(message.author.id, 'split', 'bj')
		sent = await client.get_message(message.server.get_channel(channelid), messageid)
		enough = True

		if message.content=='dd':
			if current>=bet:
				update_money(message.author.id, bet*-1, currency)
				ticketbets(message.author.id, bet, currency)
				bet = bet*2
				drawcard(message.author.id, True)
				cards = getvalue(message.author.id,"playercards","bj")
				playerscore = scorebj(message.author.id,cards,True)
				if playerscore>21:
					if split == 'None':
						await client.edit_message(sent, embed=printbj(message.author, True, "Sorry. You busted and lost.", 16711718))
						c.execute("DELETE FROM bj WHERE id={}".format(message.author.id))
			else:
				enough=False
				await client.send_message(message.channel, "You don't have enough money to double down!")

		if enough:
			if 'y' not in split:
				botcards = getvalue(message.author.id, "botcards", "bj")
				botscore = scorebj(message.author.id, botcards, False)
				while botscore < 17 and playerscore > botscore:
					drawcard(message.author.id, False)
					botcards = getvalue(message.author.id,"botcards","bj")
					botscore = scorebj(message.author.id, botcards, False)

			if 'y' in split:
				c.execute("UPDATE bj SET playercards='{}' WHERE id={}".format(split[1:], message.author.id))
				c.execute("UPDATE bj SET split='{}' WHERE id={}".format('z'+playercards, message.author.id))
				botcards = getvalue(message.author.id, "botcards", "bj")
				playercards = getvalue(message.author.id, "playercards", "bj")
				scorebj(message.author.id, botcards, False)
				scorebj(message.author.id, playercards, True)
				await client.edit_message(sent, embed=printbj(message.author, False, "Use `hit` to draw, `stand` to pass, or `dd` to double down for hand two.", 28))
			elif split == 'None':
				await client.edit_message(sent, embed=bjresult(message.author, bet, currency, botscore, playerscore, playercards))
				c.execute("DELETE FROM bj WHERE id={}".format(message.author.id))
			else:
				await client.delete_message(sent)
				splitscore = scorebj(message.author.id, split[1:], 'Split')
				embed1 = bjresult(message.author, bet, currency, botscore, splitscore, split[1:])
				embed2 = bjresult(message.author, bet, currency, botscore, playerscore, playercards)
				embed1.set_author(name=str(message.author)[:-5]+"'s Blackjack Hand 1 Result", icon_url=str(message.author.avatar_url))
				embed2.set_author(name=str(message.author)[:-5]+"'s Blackjack Hand 2 Result", icon_url=str(message.author.avatar_url))
				await client.send_message(message.channel, embed=embed1)
				await client.send_message(message.channel, embed=embed2)
				c.execute("DELETE FROM bj WHERE id={}".format(message.author.id))
	################################
	elif message.content == 'split':
		currency = getvalue(message.author.id,"currency","bj")
		bet = getvalue(message.author.id,"bet","bj")
		playercards = getvalue(message.author.id,"playercards","bj")
		current = getvalue(int(message.author.id), currency, "rsmoney")
		messageid = getvalue(message.author.id,"messageid","bj")
		channelid = getvalue(message.author.id,"channelid","bj")
		split = getvalue(message.author.id,"split","bj")
		if split == 'None':
			if len(playercards.split('|')) == 3 and playercards.split('|')[0][0] == playercards.split('|')[1][0]:
				if current >= bet:
					update_money(message.author.id, bet*-1, currency)
					c.execute("UPDATE bj SET split='{}' WHERE id={}".format('y'+playercards.split('|')[1]+'|', message.author.id))
					c.execute("UPDATE bj SET playercards='{}' WHERE id={}".format(playercards.split('|')[0]+'|', message.author.id))
					playercards = getvalue(message.author.id, "playercards", "bj")
					scorebj(message.author.id, playercards, True)
					sent = await client.get_message(message.server.get_channel(channelid), messageid)
					await client.edit_message(sent, embed=printbj(message.author, False, "Use `hit` to draw, `stand` to pass, or `dd` to double down.", 28))
				else:
					await client.send_message(message.channel, "You don't have enough money to split!")
			else:
				await client.send_message(message.channel, "Conditions not met to split. Your hand must consist of a pair of the same card.")
		else:
			await client.send_message(message.channel, "You cannot split when you have already split...")
	################################
	elif message.content == '$keys' or message.content == '$k':
		bronze=getvalue(message.author.id, "bronze", "rsmoney")
		silver=getvalue(message.author.id, "silver", "rsmoney")
		gold=getvalue(message.author.id, "gold", "rsmoney")

		embed = discord.Embed(color=13226456)
		embed.set_author(name=(str(message.author))[:-5]+"'s Keys", icon_url=str(message.author.avatar_url))
		embed.add_field(name="Bronze", value="**"+str(bronze)+"**", inline=True)
		embed.add_field(name="Silver", value="**"+str(silver)+"**", inline=True)
		embed.add_field(name="Gold", value="**"+str(gold)+"**", inline=True)
		c.execute('SELECT * FROM jackpot')
		bets=c.fetchall()
		total=sum(x[1] for x in bets)
		embed.set_footer(text="Checkout our Jackpot game, the current pot is up to "+formatfromk(total, '07')+"!")
		await client.send_message(message.channel, embed=embed)
	###############################
	elif message.content.startswith("$buykey"):
		if str(message.channel.id) == '552943110561202176' or str(message.channel.id) == '617144512409501696':
			try:
				amount=int((message.content).split(" ")[1])
				kind=(message.content).split(" ")[2]
				bronze=getvalue(message.author.id, "bronze", "rsmoney")
				silver=getvalue(message.author.id, "silver", "rsmoney")
				gold=getvalue(message.author.id, "gold", "rsmoney")
				buyer=getvalue(message.author.id, "07", "rsmoney")
				embed = discord.Embed(description="You successfully purchased **"+str(amount)+"** key(s)!", color=5174318)
				embed.set_author(name="Purchase Complete", icon_url=str(message.author.avatar_url))

				if kind=="bronze":
					if buyer<250*amount:
						await client.send_message(message.channel, "You don't have enough to buy that many bronze keys.")
					else:
						c.execute("UPDATE rsmoney SET bronze={} WHERE id={}".format(bronze+amount, message.author.id))
						update_money(message.author.id, -250*amount, "07")
						await client.send_message(message.channel, embed=embed)
				elif kind=="silver":
					if buyer<750*amount:
						await client.send_message(message.channel, "You don't have enough to buy that many silver keys.")
					else:
						c.execute("UPDATE rsmoney SET silver={} WHERE id={}".format(silver+amount, message.author.id))
						update_money(message.author.id, -750*amount, "07")
						await client.send_message(message.channel, embed=embed)
				elif kind=="gold":
					if buyer<2000*amount:
						await client.send_message(message.channel, "You don't have enough to buy that many gold keys.")
					else:
						c.execute("UPDATE rsmoney SET gold={} WHERE id={}".format(gold+amount, message.author.id))
						update_money(message.author.id, -2000*amount, "07")
						await client.send_message(message.channel, embed=embed)
			except:
				await client.send_message(message.channel, "An **error** has occurred. Make sure you use `$buykey (AMOUNT) (KEY TYPE)`.")
		else:
			await client.send_message(message.channel, "This command can only be used in <#552943110561202176>.")
	###############################
	elif message.content.startswith("$open"):
		if str(message.channel.id) == '552943110561202176' or str(message.channel.id) == '617144512409501696':
			try:
				kind = (message.content).split(" ")[1]
				keyvalue = getvalue(message.author.id, kind, 'rsmoney')
				index = openkey(kind)[0]

				if keyvalue>=1:
					if kind=='bronze':
						c.execute("UPDATE rsmoney SET bronze={} WHERE id={}".format(keyvalue-1, message.author.id))
						sidecolor=11880979
					elif kind=='silver':
						c.execute("UPDATE rsmoney SET silver={} WHERE id={}".format(keyvalue-1, message.author.id))
						sidecolor=13226456
					elif kind=='gold':
						c.execute("UPDATE rsmoney SET gold={} WHERE id={}".format(keyvalue-1, message.author.id))
						sidecolor=16759822

					f=open(kind+".txt")
					for counter, i in enumerate(f):
						if counter==index:
							item=(i.strip("\n")).split("|")[0]
							price=(i.strip("\n")).split("|")[1]
							url=(i.strip("\n")).split("|")[2]

					bronze=getvalue(message.author.id, "bronze", "rsmoney")
					silver=getvalue(message.author.id, "silver", "rsmoney")

					if item=="2 Bronze Keys":
						c.execute("UPDATE rsmoney SET bronze={} WHERE id={}".format(bronze+2, message.author.id))
					elif item=="2 Silver Keys":
						c.execute("UPDATE rsmoney SET silver={} WHERE id={}".format(silver+2, message.author.id))

					update_money(message.author.id, int(price), "07")

					embed = discord.Embed(description="You recieved item: **"+str(item)+"**!", color=sidecolor)
					embed.add_field(name="Price", value="*"+formatfromk(int(price), "07")+"*", inline=True)
					embed.set_author(name=kind.title()+" Key Prize", icon_url=str(message.author.avatar_url))
					embed.set_thumbnail(url=str(url))
					await client.send_message(message.channel, embed=embed)
				else:
					await client.send_message(message.channel, "You don't have any *"+kind+"* keys to open!")
			except:
				await client.send_message(message.channel, "An **error** has occurred. Make sure you use `$open (KEY TYPE)`.")
		else:
			await client.send_message(message.channel, "This command can only be used in <#552943110561202176>.")
	################################
	elif message.content.startswith("$updatekey"):
		try:
			if isstaff(message.author.id,message.server.roles,message.author.roles)=="verified":
				try:
					int(str(message.content).split(" ")[1][2:3])
					member=message.server.get_member(str(message.content).split(" ")[1][2:-1])
				except:
					member=message.server.get_member(str(message.content).split(" ")[1][3:-1])
						
				amount=int((message.content).split(" ")[3])
				kind=(message.content).split(" ")[2]
				current=getvalue(member.id, kind, 'rsmoney')

				if kind=='bronze':
					c.execute("UPDATE rsmoney SET bronze={} WHERE id={}".format(current+amount, member.id))
				elif kind=='silver':
					c.execute("UPDATE rsmoney SET silver={} WHERE id={}".format(current+amount, member.id))
				elif kind=='gold':
					c.execute("UPDATE rsmoney SET gold={} WHERE id={}".format(current+amount, member.id))

				embed = discord.Embed(description="<@"+str(message.author.id)+"> has transfered "+str(amount)+" "+kind+" key(s) to <@"+str(member.id)+">.", color=5174318)
				embed.set_author(name="Key Transfer", icon_url=str(message.author.avatar_url))
				await client.send_message(message.channel, embed=embed)
			else:
				await client.send_message(message.channel, "Admin Command Only!")
		except:
			await client.send_message(message.channel, "An **error** has occurred. Make sure you use `$updatekey (@USER) (KEY TYPE) (AMOUNT)`.")
	################################
	elif message.content.startswith('$giftkey'):
		try:
			bronze=get(message.server.roles, name='Bronze Donor')
			silver=get(message.server.roles, name='Silver Donor')
			gold=get(message.server.roles, name='Gold Donor')
			if bronze in message.author.roles or silver in message.author.roles or gold in message.author.roles:
				try:
					int(str(message.content).split(" ")[1][2:3])
					member=message.server.get_member(str(message.content).split(" ")[1][2:-1])
				except:
					member=message.server.get_member(str(message.content).split(" ")[1][3:-1])
		
				kind=str(message.content).split(" ")[2]
				keyvalue=getvalue(message.author.id, kind, 'rsmoney')

				if keyvalue>=1:
					if kind=='bronze':
						c.execute("UPDATE rsmoney SET bronze={} WHERE id={}".format(keyvalue-1, message.author.id))
					elif kind=='silver':
						c.execute("UPDATE rsmoney SET silver={} WHERE id={}".format(keyvalue-1, message.author.id))
					elif kind=='gold':
						c.execute("UPDATE rsmoney SET gold={} WHERE id={}".format(keyvalue-1, message.author.id))

					index = openkey(kind)[0]
					f=open(kind+".txt")
					for counter, i in enumerate(f):
						if counter==index:
							item=(i.strip("\n")).split("|")[0]
							price=(i.strip("\n")).split("|")[1]
							url=(i.strip("\n")).split("|")[2]

					bronze=getvalue(member.id, "bronze", "rsmoney")
					silver=getvalue(member.id, "silver", "rsmoney")
					if item=="2 Bronze Keys":
						c.execute("UPDATE rsmoney SET bronze={} WHERE id={}".format(bronze+2, member.id))
					elif item=="2 Silver Keys":
						c.execute("UPDATE rsmoney SET silver={} WHERE id={}".format(silver+2, member.id))

					update_money(member.id, int(price), "07")

					embed = discord.Embed(description="You gifted a "+kind+" prize to <@"+str(member.id)+"> and they won item: **"+str(item)+"**!", color=16756991)
					embed.add_field(name="Price", value="*"+formatfromk(int(price), "07")+"*", inline=True)
					embed.set_author(name=kind.title()+" Key Prize - Gift", icon_url=str(member.avatar_url))
					embed.set_thumbnail(url=str(url))
					await client.send_message(message.channel, embed=embed)
				else:
					await client.send_message(message.channel, "You don't have any *"+kind+"* keys to open!")
			else:
				await client.send_message(message.channel, 'This is a subscriber-only command.')
		except:
			await client.send_message(message.channel, "An **error** has occurred. Make sure you use `$giftkey (@USER) (KEY TYPE)`.")
	################################
	elif message.content.startswith("$fp"):
		if str(message.channel.id) == '558011172314677249' or str(message.channel.id) == '617144512409501696':
			try:
				if len((message.content).split(" "))==2:
					game='07'
				else:
					game=(message.content).split(" ")[2]
				bet=formatok(str(message.content).split(" ")[1], game)
				current=getvalue(message.author.id, game,"rsmoney")
				ticketbets(message.author.id, bet, game)

				if isenough(bet, game)[0]:
					if current>=bet:
						botflowers=[]
						playerflowers=[]
						for i in range(5):
							botflowers.append(pickflower())
							playerflowers.append(pickflower())

						pprint=""
						bprint=""
						#flowers=["Red","Orange","Yellow","Assorted","Blue","Purple","Mixed","Black","White"]
						emojis=["rf","blf","yf","puf","of","pf","raf","bf","wf"]
						for i in playerflowers:
							pprint+=str(get(client.get_all_emojis(), name=emojis[i]))
						for i in botflowers:
							bprint+=str(get(client.get_all_emojis(), name=emojis[i]))

						if scorefp(playerflowers)[0]==scorefp(botflowers)[0]:
							embed = discord.Embed(description="Tie! 10% commission taken.", color=16776960)
							update_money(message.author.id, bet*-0.1, game)
						elif scorefp(playerflowers)[0]>scorefp(botflowers)[0]:
							embed = discord.Embed(description="Congratulations! You won **"+formatfromk(bet*2, game)+"**!", color=3997475)
							update_money(message.author.id, bet, game)
						elif scorefp(playerflowers)[0]<scorefp(botflowers)[0]:
							embed = discord.Embed(description="House wins. You lost "+formatfromk(bet, game)+".", color=16718121)
							update_money(message.author.id, bet*-1, game)

						embed.add_field(name="Player Hand", value=pprint+"\nResult: "+scorefp(playerflowers)[1], inline=True)
						embed.add_field(name="House Hand", value=bprint+"\nResult: "+scorefp(botflowers)[1], inline=True)
						embed.set_author(name="Flower Poker", icon_url=str(message.author.avatar_url))
						await client.send_message(message.channel, embed=embed)

					else:
						await client.send_message(message.channel, "<@"+str(message.author.id)+">, you don't have that much gold!")
				else:
					await client.send_message(message.channel, (isenough(bet, game))[1])
			except:
				await client.send_message(message.channel, "An **error** has occurred. Make sure you use `$fp (AMOUNT) (rs3 or 07)`.")
		else:
			await client.send_message(message.channel, "This command can only be used in <#552943110561202176>.")
	###############################
	elif message.content.startswith("$leaderboard"):
		try:
			game = (message.content).split(" ")[1]
			board = (message.content).split(" ")[2]
			if game=="rs3" or game=="osrs" or game=="07":
				if game=="rs3":
					if board == 'weekly':
						c.execute("SELECT * From rsmoney ORDER BY rs3week DESC LIMIT 8")
						number=5
					else:
						c.execute("SELECT * From rsmoney ORDER BY rs3total DESC LIMIT 8")
						number = 3
					prizes=["None", "None", "None", "None", "None", "None", "None", "None"]
				elif game=="osrs" or game=="07":
					if board == 'weekly':
						c.execute("SELECT * From rsmoney ORDER BY osrsweek DESC LIMIT 8")
						number=6
					else:
						c.execute("SELECT * From rsmoney ORDER BY osrstotal DESC LIMIT 8")
						number=4
					prizes=["5 Silver Keys", "3 Silver Keys", "1 Silver Key", "1 Bronze Key", "1 Bronze Key", "1 Bronze Key", "1 Bronze Key", "1 Bronze Key"]
					
				top=c.fetchall()
				words=""
				for counter, i in enumerate(top):
					userid=i[0]
					total=i[number]
					total=formatfromk(int(total),game)
					words+=(str(counter+1)+". <@"+str(userid)+"> - **"+total+"**\n\n")# - **"+prizes[counter]+"**\n\n")

				embed = discord.Embed(color=557823, description=words)
				embed.set_author(name="Top "+game.upper()+" Wagers", icon_url=str(message.server.icon_url))
				await client.send_message(message.channel, embed=embed)
			else:
				None
		except:
			await client.send_message(message.channel, "An **error** has occurred. Make sure you use `$leaderboard (rs3 or 07) (weekly or total)`.")
	###########################################
	elif message.content == "$please":
		if str(message.channel.id)=='621787403778129934':
			if roulette!=41:
				await client.send_message(message.channel, "There is already a roulette game going on!")
			else:
				roulette=40
				embed = discord.Embed(description="A game of roulette has started! Use `bet (1st/2nd/3rd, 0-36, High/Low, Black/Red/Green, or Odd/Even) (Amount) (rs3 or 07)` to place a bet on the wheel.", color=3800857)
				embed.set_author(name="Roulette Game", icon_url=str(message.server.icon_url))
				embed.add_field(name="Time Left", value="**40** Seconds", inline=True)
				gif=random.choice(['https://cdn.discordapp.com/attachments/580436923756314624/687833813358870553/ezgif.com-resize.gif','https://cdn.discordapp.com/attachments/580436923756314624/614584556065914880/SenranKatsuragi.gif','https://cdn.discordapp.com/attachments/580436923756314624/611625448094302218/RStablegamesTRADEMARK.gif','https://cdn.discordapp.com/attachments/580436923756314624/687711049864183816/wheelgirl2.2.gif','https://cdn.discordapp.com/attachments/580436923756314624/687686305622130748/WheelGirl2.0.gif'])
				embed.set_image(url=gif)
				roulettemsg = await client.send_message(message.channel, embed=embed)
		else:
			await client.send_message(message.channel, "This command can only be used in <#621787403778129934>.")
	###########################################
	elif message.content.startswith("bet "):
		if str(message.channel.id)=='621787403778129934':
			try:
				if roulette!=41:
					areas=['1st','2nd','3rd','high','low','black','red','green','odd','even','00','0','1','2','3','4','5','6','7','8','9','10','11','12','13','14','15','16','17','18','19','20','21','22','23','24','25','26','27','28','29','30','31','32','33','34','35','36']
					if len((message.content).split(" "))==3:
						game='07'
					else:
						game=(message.content).split(" ")[3]
					bet=formatok(str(message.content).split(" ")[2], game)
					area=str(message.content).split(" ")[1]
					if area not in areas:
						await client.send_message(message.channel, "You can only bet on `1st/2nd/3rd`, `0-36`, `High/Low`, `Black/Red/Green`, and `Odd/Even`")
					else:
						current=getvalue(message.author.id, game,"rsmoney")
						ticketbets(message.author.id, bet, game)

						if isenough(bet, game)[0]:
							if current>=bet:
								update_money(message.author.id, bet*-1, game)
								c.execute("INSERT INTO roulette VALUES (%s, %s, %s, %s)", (message.author.id,bet,game,area))
								await client.add_reaction(message,"✅")
							else:
								await client.send_message(message.channel, "<@"+str(message.author.id)+">, you don't have that much gold!")
						else:
							await client.send_message(message.channel, (isenough(bet, game))[1])
				else:
					await client.send_message(message.channel, "`Ask nicely and she will spin the wheel, say $please`")
			except:
				await client.send_message(message.channel, "An **error** has occurred. Make sure you use `bet (1st/2nd/3rd, 0-36, High/Low, Black/Red/Green, or Odd/Even) (AMOUNT) (rs3 or 07)`.")
		else:
			await client.send_message(message.channel, "This command can only be used in <#621787403778129934>.")
	###########################################
	# elif message.content==("$menu"):
	# 	embed = discord.Embed(description="""1. Blurberry Special\n
	# 										2. Chef's Delight\n
	# 										3. Cider\n
	# 										4. Dragon Bitter\n
	# 										5. Karamjan Rum\n
	# 										6. Legendary Cocktail\n
	# 										7. Nice Beer\n
	# 										8. Purple Lumbridge\n
	# 										9. Short Green Guy\n
	# 										10. Wine of Zamorak\n
	# 										11. Wizard's Mind Bomb\n
	# 										""", color=3800857)
	# 	embed.set_author(name="Drink Menu", icon_url=str(message.server.icon_url))
	# 	await client.send_message(message.channel, embed=embed)
	###############################################
	elif message.content == "$drawraffle":
		if isstaff(message.author.id,message.server.roles,message.author.roles)=="verified":
			c.execute("SELECT id,tickets FROM rsmoney")
			tickets=c.fetchall()
			entered=[]
			for i in tickets:
				for x in range(i[1]):
					entered.append(str(i[0]))
			winner = random.choice(entered)
			blacklist = ['248121348755292160'] 
			while winner in blacklist:
				winner = random.choice(entered)
			print(str(winner))
			c.execute("UPDATE rsmoney SET tickets=0")

			embed = discord.Embed(description="<@"+str(winner)+"> has won the raffle!", color=16729241)
			embed.set_author(name="Raffle Winner", icon_url=str(message.server.icon_url))
			await client.send_message(message.channel, embed=embed)
		else:
			await client.send_message(message.channel, "Admin Command Only!")
	########################################
	elif message.content.startswith("$ticket"):
		if isstaff(message.author.id,message.server.roles,message.author.roles)=="verified":
			amount=int((message.content).split(" ")[2])
			try:
				int(str(message.content).split(" ")[1][2:3])
				member=message.server.get_member(str(message.content).split(" ")[1][2:-1])
			except:
				member=message.server.get_member(str(message.content).split(" ")[1][3:-1])
			tickets=getvalue(int(member.id),"tickets","rsmoney")
			c.execute("UPDATE rsmoney SET tickets={} WHERE id={}".format(tickets+amount, member.id))
			await client.send_message(message.channel, "Tickets updated.")
		else:
			await client.send_message(message.channel, "Admin Command Only!")
	########################################
	elif message.content.startswith("$override"):
		if isstaff(message.author.id,message.server.roles,message.author.roles)=="verified":
			override=int((message.content).split(" ")[1])
			await client.send_message(message.channel, "Overridden")
		else:
			await client.send_message(message.channel, "Admin Command Only!")
	#######################################
	elif message.content == '$weekly':
		bronze = get(message.server.roles, name='Bronze Donor')
		silver = get(message.server.roles, name='Silver Donor')
		gold = get(message.server.roles, name='Gold Donor')
		lastdate = getvalue(message.author.id,'weeklydate','rsmoney')
		date_format = "%Y-%m-%d %H:%M:%S"
		difference = time.mktime(time.strptime(str(datetime.datetime.now())[:-7], date_format)) - time.mktime(time.strptime(lastdate, date_format))
		times = (604800 - int(difference))
		go = False

		if times <= 0:
			go = True
		else:
			days = times // (24 * 3600)
			times = times % (24 * 3600)
			hours = times // 3600
			times %= 3600
			minutes = times // 60
		
		if bronze in message.author.roles or silver in message.author.roles or gold in message.author.roles:
			if go:
				if bronze in message.author.roles:
					bkeys=getvalue(int(message.author.id),'bronze','rsmoney')
					c.execute('UPDATE rsmoney SET bronze={} WHERE id={}'.format(bkeys+5, message.author.id))
				elif silver in message.author.roles:
					skeys=getvalue(int(message.author.id),'silver','rsmoney')
					c.execute('UPDATE rsmoney SET silver={} WHERE id={}'.format(skeys+5, message.author.id))
				elif gold in message.author.roles:
					gkeys=getvalue(int(message.author.id),'gold','rsmoney')
					c.execute('UPDATE rsmoney SET gold={} WHERE id={}'.format(gkeys+5, message.author.id))
				c.execute("UPDATE rsmoney SET weeklydate='{}' WHERE id={}".format(str(datetime.datetime.now())[:-7], message.author.id))
				words='Your weekly keys have been given!'
			else:
				words='You have **'+str(days)+'** day(s), **'+str(hours)+'** hour(s), and **'+str(minutes)+'** minute(s) left until you can collect your weekly keys.'
			embed = discord.Embed(description=words, color=65348)
			embed.set_author(name="Weekly Keys", icon_url=str(message.author.avatar_url))
			await client.send_message(message.channel, embed=embed)
		else:
			embed = discord.Embed(description="Not so fast there, Amigo!\n\n**Start your subscription today at\nhttps://patreon.com/evilbob**", color=7995152)
			embed.set_author(name="Subscribe for Weekly Keys", icon_url=str(message.server.icon_url))
			embed.set_image(url="https://cdn.discordapp.com/attachments/580436923756314624/671919480271667200/Screen_Shot_2020-01-28_at_10.10.57_PM.png")
			embed.set_footer(text="Bronze, Silver, and Gold Subscriptions Available")
			await client.send_message(message.channel, embed=embed)
	#######################################
	elif message.content.startswith('$jackpot'):
		if isstaff(message.author.id,message.server.roles,message.author.roles)=="verified":
			rollamount = formatok(message.content.split(' ')[1], '07')
			c.execute("UPDATE data SET jackpotroll={}".format(rollamount))
			await client.send_message(message.channel, 'The jackpot will now end once the pot reaches **'+formatfromk(rollamount, '07')+'**.')
		else:
			await client.send_message(message.channel, "Only admins can change the amount at which a jackpot will end. Please tag one if necessary.")
	#######################################
	elif message.content.startswith('$add'):
		if str(message.channel.id)=='658489832284094469':
			bet = formatok(str(message.content).split(" ")[1], '07')
			current = getvalue(message.author.id, '07','rsmoney')
			c.execute("SELECT jackpotroll FROM data")
			rollamount = int(c.fetchone()[0])

			if isenough(bet, '07')[0]:
				if current>=bet:
					update_money(message.author.id, bet*-1, '07')
					ticketbets(message.author.id, bet, '07')
					c.execute('SELECT * FROM jackpot')
					bets=c.fetchall()

					alreadyin=False
					for y in bets:
						if int(message.author.id) in y:
							c.execute('UPDATE jackpot SET bet={} WHERE id={}'.format(bet+y[1], message.author.id))
							alreadyin=True

					if alreadyin==False:
						c.execute("INSERT INTO jackpot VALUES (%s, %s, %s)", (int(message.author.id), bet, 0))

					await client.add_reaction(message,"✅")

					c.execute('SELECT * FROM jackpot')
					bets=c.fetchall()
					total=sum(x[1] for x in bets)
					embed = discord.Embed(description='Jackpot Value: **'+formatfromk(total, '07')+'**\n*This jackpot will end once the pot reaches: **'+formatfromk(rollamount, '07')+'***\n\nUse `$add (amount in 07)` to contribute to the jackpot.', color=5056466)

					for i in bets:
						chance=round(i[1]/total*100, 3)
						c.execute('UPDATE jackpot SET chance={} WHERE id={}'.format(float(chance), i[0]))
						embed.add_field(name=message.server.get_member(str(i[0])).name, value='Bet - *'+formatfromk(i[1], '07')+'* | Chance of Winning - *'+str(chance)+'%*', inline=False)
					embed.set_author(name="Jackpot Bets", icon_url=str(message.server.icon_url))
					embed.set_footer(text='*You can only bet 07 gold on the Jackpot game')
					await client.send_message(message.channel, embed=embed)

					if total >= rollamount:
						await client.send_message(message.channel, embed=endjackpot())
				else:
					await client.send_message(message.channel, "<@"+str(message.author.id)+">, you don't have that much gold!")
			else:
				await client.send_message(message.channel, (isenough(bet, '07'))[1])
		else:
			await client.send_message(message.channel, "This command can only be used in <#658489832284094469>.")
	######################################
	elif message.content == '$endjackpot':
		if isstaff(message.author.id,message.server.roles,message.author.roles)=="verified":
			await client.send_message(message.channel, embed=endjackpot())
		else:
			await client.send_message(message.channel, "Only admins can end a jackpot. Please tag one if necessary.")
	######################################
	elif message.content == '$rank':
		xp = getvalue(message.author.id, 'xp', 'rsmoney')
		c.execute("SELECT xp FROM rsmoney ORDER BY xp DESC")
		leaderboard = c.fetchall()
		for counter, i in enumerate(leaderboard):
			if i[0] == xp:
				rank = counter + 1

		role, badge, badges, progress, levelxp, color = None, '', [], int((xp/2000)*495), 2000, (255, 255, 255)

		if xp >= 2000:
			role = get(message.server.roles, name='🎒Rookie')
			badges.append(('pictures/rookie.png', (500, 590)))
			progress = int(((xp-2000)/3000)*495)
			badge, levelxp, color = 'Rookie', 5000, (29, 50, 171)
		if xp >= 5000:
			role = get(message.server.roles, name='💎Pro')
			badges.append(('pictures/pro.png', (410, 500)))
			progress = int(((xp-5000)/6500)*495)
			badge, levelxp, color = 'Pro', 11500, (209, 149, 97)
		if xp >= 11500:
			role = get(message.server.roles, name='⭐All-Star')
			badges.append(('pictures/allstars.png', (320, 410)))
			progress = int(((xp-11500)/13500)*495)
			badge, levelxp, color = 'All Star', 25000, (92, 214, 217)
		if xp >= 25000:
			role = get(message.server.roles, name='🎾Hall of Famer')
			badges.append(('pictures/halloffamers.png', (230, 320)))
			progress = int(((xp-25000)/100000)*495)
			badge, levelxp, color = 'H.O.F', 100000, (85, 195, 141)

		if role != None and role not in message.author.roles:
			await client.add_roles(message.author, role)

		template = cv2.imread('pictures/rankbar.png', 1)
		cv2.line(template, (50, 160), (550, 160), (136, 128, 122), 15)
		cv2.line(template, (50, 160), (50 + progress, 160), color, 15)
		width, height = (cv2.getTextSize(str(message.author)[:-5], 5, 1.3, 2))[0]
		cv2.putText(template, str(message.author)[:-5], (150, 130), 5, 1.3, (255,255,255), 2, cv2.LINE_AA)
		cv2.putText(template, str(message.author)[-5:], (150 + width, 130), 2, 0.6, (70, 70, 70), 1, cv2.LINE_AA)
		cv2.putText(template, badge, (150, 50), 2, 0.7, color, 1, cv2.LINE_AA)
		cv2.putText(template, str('{:,}'.format(xp)) + '/' + str('{:,}'.format(levelxp)) + ' XP', (435, 130), 5, 0.7, (255, 255, 255), 1, cv2.LINE_AA)

		try:
			req = Request(str(message.author.avatar_url), headers={'User-Agent': 'Mozilla/5.0'})
			arr = np.asarray(bytearray(urlopen(req).read()), dtype=np.uint8)
			avatar = cv2.imdecode(arr, 1)
			resized = cv2.resize(avatar, (100, 100), interpolation = cv2.INTER_AREA)
		except:
			avatar = cv2.imread('pictures/defaultavatar.png', 1)
			resized = cv2.resize(avatar, (100, 100), interpolation = cv2.INTER_AREA)

		template[30:130, 30:130] = resized
		
		for i in badges:
			badge = cv2.imread(i[0], 1)
			newbadge = cv2.resize(badge, (90, 90), interpolation = cv2.INTER_AREA)
			template[10:100, i[1][0]:i[1][1]] = newbadge

		cv2.rectangle(template, (0, 0), (600, 200), color, 5)
		cv2.imwrite('edited.png', template)
		await client.send_file(message.channel, 'edited.png')
	##############################
	elif message.content == '$levels':
		c.execute("SELECT id, xp From rsmoney ORDER BY xp DESC LIMIT 10")
		top=c.fetchall()
		words=""

		for counter, i in enumerate(top):
			userid=i[0]
			xp=i[1]
			words+=(str(counter+1)+". <@"+str(userid)+"> - **XP: "+str(xp)+"**\n\n")

		embed = discord.Embed(color=557823, description=words)
		embed.set_author(name="Top Levels and XP", icon_url=str(message.server.icon_url))
		await client.send_message(message.channel, embed=embed)
	################################
	elif message.content.startswith('$purge'):
		if isstaff(message.author.id,message.server.roles,message.author.roles)=="verified":
			purged = int((message.content).split(' ')[1]) + 1
			await client.purge_from(message.channel, limit = purged)
		else:
			await client.send_message(message.channel, "Admin Command Only!")
	################################
	elif message.content.startswith('$sayin'):
		if isstaff(message.author.id,message.server.roles,message.author.roles)=="verified":
			channel = client.get_channel(str((message.content).split('|')[1]))
			await client.send_message(channel, (str((message.content).split('|')[2])).title())
		else:
			await client.send_message(message.channel, "Admin Command Only!")
	################################
	elif message.content.startswith('$cashin') or message.content.startswith('$cashout'):
		if str(message.channel.id) == '514298345993404416':
			try:
				if len((message.content).split(' ')) == 2:
					game = '07'
				else:
					game = (message.content).split(' ')[2]

				amount = formatok((message.content).split(' ')[1], game)
				current = getvalue(message.author.id, game, "rsmoney")
				way = (message.content).split(' ')[0][1:]
				enough = True

				if way == 'cashout' and amount > current:
					enough = False

				if enough:
					c.execute("SELECT code FROM cash")
					codelist, codes = c.fetchall(), []
					for i in codelist:
						codes.append(int(i[0]))
					while True:
						code = random.randint(100,999)
						if code in codes:
							continue
						else:
							break
					c.execute("INSERT INTO cash VALUES (%s, %s, %s, %s, %s)", (message.author.id, way, code, game, amount))
					await client.send_message(client.get_channel('617795929570803723'), '<@&512370598459080724>, <@' + str(message.author.id) + '> wants to ' + way + ' **' + formatfromk(amount, game) + '** ' + game + '. Use `$accept ' + str(code) + '`.')
					embed = discord.Embed(description="A message has been sent to a cashier. Your request will be processed and you will be messaged soon.", color=5174318)
					embed.set_author(name=way.title(), icon_url=str(message.server.icon_url))
					await client.send_message(message.channel, embed=embed)
				else:
					await client.send_message(message.channel, "<@"+str(message.author.id)+">, You don't have that much money to cashout!")
			except:
				await client.send_message(message.channel, "An **error** has occurred. Make sure you use `$" + way + " (AMOUNT) (rs3 or 07)`.")
		else:
			await client.send_message(message.channel, "This command can only be used in <#514298345993404416>.")

	elif message.content.startswith('$accept'):
		if str(message.channel.id) == "617795929570803723":
			code = int((message.content).split(' ')[1])
			c.execute("SELECT code FROM cash")
			codelist, codes = c.fetchall(), []
			for i in codelist:
				codes.append(int(i[0]))

			if code in codes:
				c.execute("SELECT * FROM cash WHERE code={}".format(code))
				cash = c.fetchall()[0]
				userid = str(cash[0])
				way = str(cash[1])
				currency = str(cash[3])
				amount = int(cash[4])
				if way == 'cashout':
					update_money(userid, amount*-1, currency)
				embed = discord.Embed(description="<@"+userid+">, <@"+str(message.author.id)+"> will perform your "+way+".", color=5174318)
				embed.set_author(name=way.title(), icon_url=str(message.server.icon_url))
				await client.send_message(client.get_channel("514298345993404416"), embed=embed)
				await client.send_message(message.channel, "Accepted. Please DM them now.")
				c.execute("DELETE FROM cash where code={}".format(code))
			else:
				await client.send_message(message.channel, "There is no cashout/cashin request with that code.")
		else:
			None

	elif message.content == '$giveaways':
		await client.add_roles(message.author, get(message.server.roles, name='Giveaways'))

client.loop.create_task(my_background_task())
Bot_Token = os.environ['TOKEN']
client.run(str(Bot_Token))
#https://discordapp.com/oauth2/authorize?client_id=580511336598077511&scope=bot&permissions=8
#heroku pg:psql postgresql-adjacent-85932 --app rstable


"""
Add new commands to command list

Full Poker Game

Dice Duels

Whip Duels - Cryptoscape
"""
