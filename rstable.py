import discord
import asyncio
import random
import time
import datetime
import os
import psycopg2
import hashslingingslasher as hasher
from discord.utils import get

DATABASE_URL = os.environ['DATABASE_URL']
conn = psycopg2.connect(DATABASE_URL, sslmode='require')
c=conn.cursor()

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
# 				tickets integer
# 				)""")
# c.execute("INSERT INTO rsmoney VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", ("546184449373634560",0,0,0,0,0,0,"None",False,0,0,0,0))
# conn.commit()

# c.execute("DROP TABLE data")
# c.execute("""CREATE TABLE data (
# 				seedreset text,
# 				serverseed text,
# 				yesterdayseed text,
# 				nonce integer,
# 				rs3profit bigint,
# 				osrsprofit bigint
# 				)""")
# c.execute("INSERT INTO data VALUES (%s, %s, %s, %s, %s, %s)", (time.strftime("%d"), hasher.create_seed(), "None", 0, 0, 0))
conn.commit()

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
				channelid text
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

client = discord.Client()


def add_member(userid,rs3,osrs,usd):
	c.execute("INSERT INTO rsmoney VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", (userid,rs3,osrs,0,0,0,0,"ClientSeed",False,0,0,0,0))
	conn.commit()

def getvalue(userid,value,table):
	strings=["clientseed","seedreset","serverseed","yesterdayseed","deck","botcards","playercards","currency","messageid","channelid","bets","streak"]
	if value=="07":
		value="osrs"
	try:
		c.execute("SELECT rs3 FROM rsmoney WHERE id={}".format(userid))
		tester=int(c.fetchone()[0])
	except:
		print("New Member")
		add_member(int(userid),0,0,0)
		return 0

	c.execute("SELECT {} FROM {} WHERE id={}".format(value, table, userid))

	if value=="privacy" or value=="claimed":
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
	conn.commit()

def isstaff(checkedid,serverroles,authorroles):
	for i in open("staff.txt"):
		role=get(serverroles, name=str(i.strip()))
		if role in authorroles:
			return "verified"

def formatok(amount, currency):
	#takes amount as string from message.content
	#returns an integer in K
	#amount=str(amount)
	if (amount[-1:]).lower()=="m":
		return int(float(str(amount[:-1]))*1000)
	elif (amount[-1:]).lower()=="k":
		return int(float(str(amount[:-1])))
	elif (amount[-1:]).lower()=="b":
		return int(float(str(amount[:-1]))*1000000)
	else:
		return int(float(amount)*1000)

def formatfromk(amount, currency):
	#takes amount as integer in K
	#returns a string to be printed

	if amount>=1000000:
		if len(str(amount))==7:
			return '{0:.3g}'.format(amount*0.000001)+"B"
		elif len(str(amount))==8:
			return '{0:.4g}'.format(amount*0.000001)+"B"
		else:
			return '{0:.5g}'.format(amount*0.000001)+"B"
	elif amount>=1000:
		if len(str(amount))==4:
			return '{0:.3g}'.format(amount*0.001)+"M"
		elif len(str(amount))==5:
			return '{0:.4g}'.format(amount*0.001)+"M"
		elif len(str(amount))==6:
			return '{0:.5g}'.format(amount*0.001)+"M"
	else:
		return str(amount)+"k"

def isenough(amount, currency):
	global words
	if currency=="rs3":
		if amount<1000:
			words="The minimum amount you can bet is **1m** gp RS3."
			return False, words
		else:
			return True, " "
	elif currency=="07":
		if amount<100:
			words="The minimum amount you can bet is **100k** gp 07."
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
	conn.commit()

def getrandint(userid):
	c.execute("SELECT serverseed FROM data")
	serverseed=str(c.fetchone()[0])
	c.execute("SELECT nonce FROM data")
	nonce=int(c.fetchone()[0])
	clientseed=getvalue(userid, "clientseed","rsmoney")
	randint=hasher.getrandint(serverseed, clientseed, nonce)
	c.execute("UPDATE data SET nonce={}".format(int(nonce+1)))
	conn.commit()
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
	
	if player==True:
		c.execute("UPDATE bj SET playerscore={} WHERE id={}".format(score, userid))
	elif player==False:
		c.execute("UPDATE bj SET botscore={} WHERE id={}".format(score, userid))
	return score

def printbj(user,stood,description,color):
	botcards=[]
	playercards=[]
	botscore=getvalue(user.id,"botscore","bj")
	playerscore=getvalue(user.id,"playerscore","bj")
	bot=""
	player=""
	if stood:
		size=0
	else:
		size=1
		bot+=(str(get(client.get_all_emojis(), name="cardback")))

	for i in ((getvalue(user.id,"botcards","bj")).split("|"))[size:]:
		for emoji in client.get_all_emojis():
			if emoji.name==i:
				emojid=emoji.id
				bot+=("<:"+str(i)+":"+str(emojid)+">")
	for i in ((getvalue(user.id,"playercards","bj")).split("|"))[:-1]:
		for emoji in client.get_all_emojis():
			if emoji.name==i:
				emojid=emoji.id
				player+=("<:"+str(i)+":"+str(emojid)+">")

	embed = discord.Embed(description=description, color=color)
	embed.set_author(name=str(user)[:-5]+"'s Blackjack Game", icon_url=str(user.avatar_url))
	embed.add_field(name=str(user)[:-5]+"'s Hand - "+str(playerscore), value=player, inline=True)
	if stood:
		embed.add_field(name="Dealer's Hand - "+str(botscore), value=bot, inline=True)
	else:
		embed.add_field(name="Dealer's Hand - ?", value=bot, inline=True)
	return embed

def drawcard(userid,player):
	deck=getvalue(userid,"deck","bj")
	decklist=deck.split("|")
	index=random.randint(0, (len(decklist)-1))
	card=decklist[index]
	del decklist[index]
	deck='|'.join(decklist)
	
	if player==True:
		playercards=getvalue(userid,"playercards","bj")
		c.execute("UPDATE bj SET playercards='{}' WHERE id={}".format(str(playercards)+str(card)+"|", userid))
	elif player==False:
		botcards=getvalue(userid,"botcards","bj")
		c.execute("UPDATE bj SET botcards='{}' WHERE id={}".format(str(botcards)+str(card)+"|", userid))

	c.execute("UPDATE bj SET deck='{}' WHERE id={}".format(deck, userid))
	conn.commit()

def profit(win, currency, bet):
	if currency=="rs3":
		c.execute("SELECT rs3profit FROM data")
		rs3profit=c.fetchone()[0]
		if win==True:
			c.execute("UPDATE data SET rs3profit={}".format(rs3profit-bet))
		elif win==False:
			c.execute("UPDATE data SET rs3profit={}".format(rs3profit+bet))
	else:
		c.execute("SELECT osrsprofit FROM data")
		osrsprofit=c.fetchone()[0]
		if win==True:
			c.execute("UPDATE data SET osrsprofit={}".format(osrsprofit-bet))
		elif win==False:
			c.execute("UPDATE data SET osrsprofit={}".format(osrsprofit+bet))
	conn.commit()

def pickflower():
	roll=random.randint(0,9990)
	if roll in range(0,10):
		return 8#"White"
	elif roll in range(10,20):
		return 7#"Black"
	elif roll in range(20,1486):
		return 6#"Mixed"
	elif roll in range(1486,2564):
		return 5#"Assorted"
	elif roll in range(2564,4102):
		return 4#"Orange"
	elif roll in range(4102,5587):
		return 3#"Purple"
	elif roll in range(5587,7052):
		return 2#"Yellow"
	elif roll in range(7052,8582):
		return 1#"Blue"
	elif roll in range(8582,9990):
		return 0#"Red"

def scorefp(hand):
	pairs=0
	three=False
	returned=0, "None"
	for i in hand:
		if hand.count(i)==5:
			returned=6, "Five Of A Kind"
		elif hand.count(i)==4:
			returned=5, "Four Of A Kind"

		if hand.count(i)==3:
			three=True
		if hand.count(i)==2:
			pairs+=1
		if pairs>=1 and three==True:
			returned=4, "Full House"
		elif three==True:
			returned=3, "Three Of A Kind"
		elif pairs>=3:
			returned=2, "Two Pairs"
		elif pairs==1 or pairs==2:
			returned=1, "One Pair"

	if 7 in hand and 8 in hand:
		return 7, "Two Wild Flowers (Auto-Win)"
	elif 7 in hand or 8 in hand:
		if returnd==6 or returned==5:
			return 6, "Five Of A Kind"
		elif returned==4 or returned==3:
			return 5, "Four Of A Kind"
		elif returned==2:
			return 4, "Full House"
		elif returned==1:
			return 3, "Three Of A Kind"
		elif returned==0:
			return 1, "One Pair"
	else:
		return returned
######################################################################################

#Predefined Variables

colors=["A","B","C","D","E","F","0","1","2","3","4","5","6","7","8","9"]
nextgiveaway=0
participants=[]
roulette=41
roulettemsg=0
gif=""

async def my_background_task():
	global roulette,participants,winner,roulettemsg,gif,nextgiveaway
	await client.wait_until_ready()
	while not client.is_closed:
		channel = discord.Object(id='590950795390746634')
		c.execute("SELECT seedreset FROM data")
		lastdate=str(c.fetchone()[0])
		today=str(time.gmtime()[2])
		if today!=lastdate:

			c.execute("SELECT serverseed FROM data")
			serverseed=str(c.fetchone()[0])
			newseed=hasher.create_seed()
			c.execute("UPDATE data SET serverseed='{}'".format(newseed))
			c.execute("UPDATE data SET yesterdayseed='{}'".format(serverseed))
			c.execute("UPDATE data SET seedreset={}".format(today))
			c.execute("UPDATE data SET nonce=0")
			conn.commit()

			embed = discord.Embed(color=16724721)
			embed.set_author(name="Server Seed Updates")
			embed.add_field(name="Yesterday's Server Seed Unhashed", value=serverseed, inline=True)
			embed.add_field(name="Yesterday's Server Seed Hashed", value=hasher.hash(serverseed), inline=True)
			embed.add_field(name="Today's Server Seed Hashed", value=hasher.hash(newseed), inline=True)
			#embed.add_field(name="Today's Server Seed Unhashed", value=newseed, inline=True)
			await client.send_message(channel, embed=embed)
		else:
			if roulette<1:
				roll=random.randint(0,37)

				winnerids=""
				c.execute("SELECT * from roulette")
				bets=c.fetchall()
				for counter, i in enumerate(bets):
					win=False

					if i[3].isdigit():
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
							win=True
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
				embed.set_image(url='https://cdn.discordapp.com/attachments/580436923756314624/614584339841155072/unknown.png')
				channel = discord.Object(id='580153388402999308')
				await client.send_message(channel, embed=embed)
				if winnerids=="":
					await client.send_message(channel, "No winners.")
				else:
					await client.send_message(channel, winnerids)
				roulette=41
				c.execute("DROP TABLE roulette")
				c.execute("""CREATE TABLE roulette (
								id bigint,
								bet integer,
								currency text,
								area text
								)""")
				conn.commit()

			elif roulette!=41 and roulette!=0:
				embed = discord.Embed(description="A game of roulette is going on! Use `bet (0-36, High/Low, Black/Red/Green, or Odd/Even) (Amount) (rs3 or 07)` to place a bet on the wheel.", color=3800857)
				embed.set_author(name="Roulette Game", icon_url='https://images-ext-2.discordapp.net/external/ZHvyT2JKvVpfLsN1_RdcnocCsnFjJylZom7aoOFUTD8/https/cdn.discordapp.com/icons/512158131674152973/567873fba79be608443232aae21dbb7c.jpg')
				embed.add_field(name="Time Left", value="**"+str(roulette)+"** Seconds", inline=True)
				embed.set_image(url=gif)
				await client.edit_message(roulettemsg, embed=embed)
				roulette-=10
			else:
				None
		channel = discord.Object(id='580153388402999308')

		if nextgiveaway==0:
			if len(participants)<1:
				embed = discord.Embed(description="Couldn't determine a giveaway winner. Next giveaway in __30 minutes__.", color=557823)
				embed.set_author(name="Giveaway", icon_url="https://cdn.discordapp.com/icons/444569488491413506/fb7ac7ed9204c85dd640d86e7358f1b8.jpg")
				await client.send_message(channel, embed=embed)
			else:
				winner=random.choice(participants)
				embed = discord.Embed(description="<@"+winner+"> has won a raffle ticket! Next giveaway in __30 minutes__.", color=557823)
				embed.set_author(name="Giveaway", icon_url="https://cdn.discordapp.com/icons/444569488491413506/fb7ac7ed9204c85dd640d86e7358f1b8.jpg")
				await client.send_message(channel, embed=embed)
				tickets=getvalue(int(message.author.id),"tickets","rsmoney")
				c.execute("UPDATE rsmoney SET tickets={} WHERE id={}".format(tickets+1, message.author.id))
				conn.commit()
				participants=[]
			nextgiveaway=30
		elif nextgiveaway==7:
			embed = discord.Embed(description="Say something in the next minute to be entered in a raffle ticket giveaway!", color=557823)
			embed.set_author(name="Giveaway", icon_url="https://cdn.discordapp.com/icons/444569488491413506/fb7ac7ed9204c85dd640d86e7358f1b8.jpg")
			await client.send_message(channel, embed=embed)
			nextgiveaway-=1
		else:
			nextgiveaway-=1
		print(nextgiveaway)
		await asyncio.sleep(10)




@client.event
async def on_ready():
	print("Bot Logged In!")

# @client.event
# async def on_message_delete(message):
# 	await client.send_message(client.get_channel("473944352427868170"), str(message.author)+" said: \""+str(message.content)+"\"")

@client.event
async def on_message(message):
	global roulette,roulettemsg,gif,nextgiveaway,participants
	message.content=(message.content).lower()

	if nextgiveaway<=7 and message.channel.id=="580153388402999308" and message.server.id=="518832231532331018":
		if str(message.author.id) not in participants and str(message.author.id)!="580511336598077511":
			participants.append(str(message.author.id))

	if message.server.id!="518832231532331018":
		None
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
		if str(message.channel.id)=="585098613152153600":
			clientseed=str((message.content)[9:])
			if len(clientseed)>20:
				await client.send_message(message.channel, "That client seed is too long. Please try a shorter one. (20 Character Limit)")
			else:
				c.execute("UPDATE rsmoney SET clientseed='{}' WHERE id={}".format(str(clientseed), int(message.author.id)))
				conn.commit()
				await client.send_message(message.channel, "Your client seed has been set to "+(message.content)[9:]+".")
		else:
			await client.send_message(message.channel, "This command can only be used in <#585098613152153600> to prevent spam.")
	# #####################################








	###################################################
	elif (message.content).lower()==("$wallet") or (message.content).lower()==("$w"):
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
		if getvalue(int(message.author.id), "privacy","rsmoney")==True:
			await client.send_message(message.channel, embed=embed)
		else:
			await client.send_message(message.channel, embed=embed)



	elif  ((message.content).lower()).startswith("$wallet <@") or ((message.content).lower()).startswith("$w <@"):
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
				conn.commit()

				embed = discord.Embed(description="<@"+str(member.id)+">'s "+currency+" currency has been cleared. RIP", color=5174318)
				embed.set_author(name="Wallet Clearing", icon_url=str(member.avatar_url))
				await client.send_message(message.channel, embed=embed)
			else:
				await client.send_message(message.channel, "Admin Command Only!")
		except:
			await client.send_message(message.channel, "An **error** occured. Make sure you use `$clear (rs3 or 07) (@user)`")
	###########################################
	elif (message.content).startswith("$deposit") or message.content.startswith("$withdraw"):
		try:
			if isstaff(message.author.id,message.server.roles,message.author.roles)=="verified":
				maximum=False
				if (str(message.content).split(" ")[2][-1:]).lower()=="b":
					if int(str(message.content).split(" ")[2][:-1])>100:
						await client.send_message(message.channel, "You can only give up to 100b at one time for...reasons.")
						maximum=True

				if maximum==False:
					game=(message.content).split(" ")[3]
					amount=formatok(str(message.content).split(" ")[2], game)

					try:
						int(str(message.content).split(" ")[1][2:3])
						member=message.server.get_member(str(message.content).split(" ")[1][2:-1])
					except:
						member=message.server.get_member(str(message.content).split(" ")[1][3:-1])

					if message.content.startswith("$deposit"):
						update_money(int(member.id), amount, game)
					elif message.content.startswith("$withdraw"):
						update_money(int(member.id), amount*-1, game)
	
					embed = discord.Embed(description="<@"+str(member.id)+">'s wallet has been updated.", color=5174318)
					embed.set_author(name="Update Request", icon_url=str(message.author.avatar_url))
					await client.send_message(message.channel, embed=embed)
				else:
					None
			else:
				await client.send_message(message.channel, "Admin Command Only!")
		except:
			await client.send_message(message.channel, "An **error** has occured. Make sure you use `$update (@user) (amount) (rs3 or 07)`.")
	############################################
	elif message.content.startswith("$help") or message.content.startswith("$commands"):
		embed = discord.Embed(description=  #"\n `$colorpicker` - Shows a random color\n" +
											#"\n `$start unscramble` - Starts a game where you unscramble a word\n" +
											#"\n `$start hangman` - Starts a game of hangman\n" +
											#"\n `$random (SIZE)` - Starts a game where you guess a number between 1 and the given size\n" +
											#"\n `$poll (QUESTION)` - Starts a Yes/No poll with the given question\n" +
											"\n `$w` or `$wallet` - Checks your own wallet\n" +
											"\n `$w (@USER)` or `$wallet (@USER)` - Checks that user's wallet\n" +
											"\n `$k` or `$keys` - Checks how many keys of each kind you have\n" +
											"\n `$open (KEY TYPE)` - Opens that type of chest\n" +
											#"\n `$flower (AMOUNT) (hot or cold)` - Hot or cold gives x2, 5% \\of auto loss\n" +
											"\n `$50 (BET) (rs3 or 07)` - Must roll above 50, x1.8 payout\n" +
											"\n `$53 (BET) (rs3 or 07)` - Must roll above 53, x2 payout\n" +
											"\n `$75 (BET) (rs3 or 07)` - Must roll above 75, x3 payout\n" +
											"\n `$95 (BET) (rs3 or 07)` - Must roll above 95, x7 payout\n" +
											#"\n `$swap (rs3 or 07) (AMOUNT)` - Swaps that amount of gold to the other game" +
											#"\n `$rates` - Shows the swapping rates between currencies" +
											"\n `$bj (BET) (rs3 or 07)` - Starts a game of blackjack with the bot\n" +
											#"\n `$deposit (rs3 or 07) (AMOUNT)` - Notifes a cashier that you want to deposit the amount to your wallet\n" +
											#"\n `$withdraw (rs3 or 07) (AMOUNT)` - Notifes a cashier that you want to withdraw the amount from your wallet\n" +
											"\n `$transfer (@USER) (AMOUNT) (rs3 or 07)` - Transfers that amount from your wallet to the user's wallet\n" +
											"\n `$wager`, `$total bet` or `$tb` - Shows your total amount bet for rs3 and 07\n" +
											"\n `$thisweek` - Shows your total amount bet for rs3 and 07 this week\n" +
											"\n `$fp (AMOUNT) (rs3 or 07)` - Starts flower poker against the bot\n" +
											"\n `$setseed (SEED)` - Sets your client seed for provably fair gambling\n", color=16771099)

		embed.set_author(name="Bot Commands", icon_url=str(message.server.icon_url))
		await client.send_message(message.channel, embed=embed)
		# await client.send_message(message.channel, "The commands have been sent to your private messages.")
	###################################
	elif ((message.content).lower()).startswith("$transfer"):
		try:
			transfered=formatok((str(message.content).split(" ")[2]), str(message.content).split(" ")[3])
			enough=True

			if str(message.content).split(" ")[3]=="rs3":
				if transfered<1:
					await client.send_message(message.channel, "You must transfer at least **1k** 07.")
					enough=False

			elif str(message.content).split(" ")[3]=="07":
				if transfered<1:
					await client.send_message(message.channel, "You must transfer at least **1k** RS3.")
					enough=False

			currency=str(message.content).split(" ")[3]
			current=getvalue(int(message.author.id),currency,"rsmoney")

			if enough==True:
				if current>=transfered:
					try:
						int(str(message.content).split(" ")[1][2:3])
						member=message.server.get_member(str(message.content).split(" ")[1][2:-1])
					except:
						member=message.server.get_member(str(message.content).split(" ")[1][3:-1])
					
					taker=getvalue(int(member.id),currency,"rsmoney")
			
					if currency=="rs3":
						c.execute("UPDATE rsmoney SET rs3={} WHERE id={}".format(current-transfered, message.author.id))
						c.execute("UPDATE rsmoney SET rs3={} WHERE id={}".format(taker+transfered, member.id))
					elif currency=="07":
						c.execute("UPDATE rsmoney SET osrs={} WHERE id={}".format(current-transfered, message.author.id))
						c.execute("UPDATE rsmoney SET osrs={} WHERE id={}".format(taker+transfered, member.id))
					conn.commit()

					embed = discord.Embed(description="<@"+str(message.author.id)+"> has transfered "+str(formatfromk(transfered, currency))+" "+currency+" to <@"+str(member.id)+">'s wallet.", color=5174318)
					embed.set_author(name="Transfer Request", icon_url=str(message.author.avatar_url))
					await client.send_message(message.channel, embed=embed)
				else:
					await client.send_message(message.channel, "<@"+str(message.author.id)+">, You don't have enough money to transfer that amount!")
			else:
				None
		except:
			await client.send_message(message.channel, "An **error** has occured. Make sure you use `$transfer (@user) (Amount you want to give) (rs3 or 07)`.")
	###################################
	elif message.content.startswith("$53") or message.content.startswith("$50") or message.content.startswith("$75") or message.content.startswith("$95"):
		try:
			game=str(message.content).split(" ")[2]
			bet=formatok(str(message.content).split(" ")[1], game)
			current=getvalue(message.author.id, game,"rsmoney")

			if isenough(bet, game)[0]:
				if message.content.startswith("$53x2") or message.content.startswith("$53"):
					title="53x2"
					odds=54
					multiplier=2
				elif message.content.startswith("$50x1.8") or message.content.startswith("$50"):
					title="50x1.8"
					odds=51
					multiplier=1.8
				elif message.content.startswith("$75x3") or message.content.startswith("$75"):
					title="75x3"
					odds=76
					multiplier=3
				elif message.content.startswith("$95x7") or message.content.startswith("$95"):
					title="95x7"
					odds=96
					multiplier=7

				if current>=bet:
					roll=getrandint(message.author.id)

					if roll in range(1,odds):
						winnings=bet
						words="Rolled **"+str(roll)+"** out of **100**. You lost **"+str(formatfromk(bet, game))+"** "+str(game)+"."
						sidecolor=16718121
						gains=bet*-1
						win=False
					else:
						winnings=int(bet*multiplier)
						winnings=formatfromk(winnings, game)
						words="Rolled **"+str(roll)+"** out of **100**. You won **"+str(winnings)+"** "+str(game)+"."	
						winnings=formatok(winnings, game)
						sidecolor=3997475
						gains=(bet*multiplier)-(bet)
						win=True

					update_money(int(message.author.id), gains, game)

					c.execute("SELECT nonce FROM data")
					nonce=int(c.fetchone()[0])
					clientseed=getvalue(message.author.id, "clientseed", "rsmoney")

					embed = discord.Embed(color=sidecolor)
					embed.set_author(name=str(message.author), icon_url=str(message.author.avatar_url))
					embed.add_field(name=title, value=words, inline=True)
					embed.set_footer(text="Nonce: "+str(nonce-1)+" | Client Seed: \""+str(clientseed)+"\"")
					await client.send_message(message.channel, embed=embed)

					ticketbets(message.author.id, bet, game)
					profit(win, game, winnings)

				else:
					await client.send_message(message.channel, "<@"+str(message.author.id)+">, you don't have that much gold!")
			else:
				await client.send_message(message.channel, (isenough(bet, game))[1])
		except:
			await client.send_message(message.channel, "An **error** has occured. Make sure you use `$(50, 53, 75, or 95) (BET) (rs3 or 07)`.")
	#############################
	elif ((message.content).lower())==("$wager") or ((message.content).lower())==("$total bet") or ((message.content).lower())==("$tb"):
		rs3total=getvalue(message.author.id, "rs3total","rsmoney")
		osrstotal=getvalue(message.author.id, "osrstotal","rsmoney")

		osrs=formatfromk(osrstotal, "osrs")
		rs3=formatfromk(rs3total, "rs3")

		embed = discord.Embed(color=16766463)
		embed.set_author(name=(str(message.author))[:-5]+"'s Total Bets", icon_url=str(message.author.avatar_url))
		embed.add_field(name="RS3 Total Bets", value=rs3, inline=True)
		embed.add_field(name="07 Total Bets", value=osrs, inline=True)
		await client.send_message(message.channel, embed=embed)
	###############################
	elif message.content=="$thisweek":
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
	elif message.content=="$reset thisweek":
		if isstaff(message.author.id,message.server.roles,message.author.roles)=="verified":
			c.execute("UPDATE rsmoney SET rs3week={}".format(0))
			c.execute("UPDATE rsmoney SET osrsweek={}".format(0))
			conn.commit()
			embed = discord.Embed(description="All weekly bets have been reset.", color=5174318)
			embed.set_author(name="Weekly Bets Reset", icon_url=str(message.server.icon_url))
			await client.send_message(message.channel, embed=embed)
		else:
			await client.send_message(message.channel, "Admin Command Only!")
	###############################
	elif message.content=="$privacy on":
		c.execute("UPDATE rsmoney SET privacy=True WHERE id={}".format(message.author.id))
		conn.commit()
		embed = discord.Embed(description="<@"+str(message.author.id)+">'s wallet privacy is now enabled.", color=5174318)
		embed.set_author(name="Privacy Mode", icon_url=str(message.author.avatar_url))
		await client.send_message(message.channel, embed=embed)
	#################################
	elif message.content=="$privacy off":
		c.execute("UPDATE rsmoney SET privacy=False WHERE id={}".format(message.author.id))
		conn.commit()
		embed = discord.Embed(description="<@"+str(message.author.id)+">'s wallet privacy is now disabled.", color=5174318)
		embed.set_author(name="Privacy Mode", icon_url=str(message.author.avatar_url))
		await client.send_message(message.channel, embed=embed)
	#################################
	# elif message.content.startswith("!randint"):
	# 	maximum=int((message.content).split(" ")[1])
	# 	if maximum>10000 or maximum<1:
	# 		await client.send_message(message.channel, "That is not a valid maximum number. Please try again.")
	# 	else:
	# 		await client.send_message(message.channel, "**"+str(random.randint(1,maximum))+"**")
	# elif message.content==("!roll"):
	# 	await client.send_message(message.channel, "**"+str(random.randint(1, 100))+"**")
	#################################
	elif message.content.startswith("$bj"):
		try:
			deck="aC|aS|aH|aD|2C|2S|2H|2D|3C|3S|3H|3D|4C|4S|4H|4D|5C|5S|5H|5D|6C|6S|6H|6D|7C|7S|7H|7D|8C|8S|8H|8D|9C|9S|9H|9D|10C|10S|10H|10D|jC|jS|jH|jD|qC|qS|qH|qD|kC|kS|kH|kD"
			currency=(message.content).split(" ")[2]
			bet=formatok((message.content).split(" ")[1], currency)
			current=getvalue(int(message.author.id), currency,"rsmoney")
			if isenough(bet, currency)[0]:
				if current>=bet:
					try:
						c.execute("SELECT playerscore FROM bj WHERE id={}".format(message.author.id))
						tester=int(c.fetchone()[0])
						await client.send_message(message.channel, "You are already in a game of blackjack! Type `hit` or `stand` to continue the game!")
					except:
						update_money(message.author.id, bet*-1, currency)
						ticketbets(message.author.id, bet, currency)
						c.execute("INSERT INTO bj VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", (message.author.id,deck,"","",0,0,bet,currency,"",str(message.channel.id)))
						drawcard(message.author.id,True)
						drawcard(message.author.id,True)
						drawcard(message.author.id,False)
						drawcard(message.author.id,False)
						botcards=getvalue(message.author.id,"botcards","bj")
						playercards=getvalue(message.author.id,"playercards","bj")
						scorebj(message.author.id,botcards,False)
						scorebj(message.author.id,playercards,True)
						sent=await client.send_message(message.channel, embed=printbj(message.author, False, "Use `hit` to draw or `stand` to pass.", 28))
						c.execute("UPDATE bj SET messageid={} WHERE id={}".format(str(sent.id), message.author.id))
					conn.commit()
				else:
					await client.send_message(message.channel, "<@"+str(message.author.id)+">, you don't have that much gold!")
			else:
				await client.send_message(message.channel, (isenough(bet, game))[1])
		except:
			await client.send_message(message.channel, "An **error** has occured. Make sure you use `$bj (Amount) (rs3 or 07)`.")
	################################
	elif message.content==("hit"):
		drawcard(message.author.id,True)
		cards=getvalue(message.author.id,"playercards","bj")
		playerscore=scorebj(message.author.id,cards,True)
		botscore=getvalue(message.author.id,"botscore","bj")
		messageid=getvalue(message.author.id,"messageid","bj")
		channelid=getvalue(message.author.id,"channelid","bj")
		currency=getvalue(message.author.id,"currency","bj")
		bet=getvalue(message.author.id,"bet","bj")
		sent=await client.get_message(message.server.get_channel(channelid), messageid)
		if playerscore>21:
			await client.edit_message(sent, embed=printbj(message.author, True, "Sorry. You busted and lost.", 16711718))
			profit(False, currency, bet)
			c.execute("DELETE FROM bj WHERE id={}".format(message.author.id))
			conn.commit()
		else:
			await client.edit_message(sent, embed=printbj(message.author, False, "Use `hit` to draw or `stand` to pass.", 28))
	###################################
	elif message.content==("stand"):
		playerscore=getvalue(message.author.id,"playerscore","bj")
		messageid=getvalue(message.author.id,"messageid","bj")
		channelid=getvalue(message.author.id,"channelid","bj")
		sent=await client.get_message(message.server.get_channel(channelid), messageid)
		while True:
			cards=getvalue(message.author.id,"botcards","bj")
			botscore=scorebj(message.author.id,cards,False)

			if botscore<17:
				drawcard(message.author.id,False)
			else:
				break

		bet=getvalue(message.author.id,"bet","bj")
		currency=getvalue(message.author.id,"currency","bj")
		win=False

		if botscore>21:
			await client.edit_message(sent, embed=printbj(message.author, True, "Dealer Busts. You Win!", 3407616))
			update_money(message.author.id, bet*2, currency)
			win=True
		elif botscore==playerscore:
			await client.edit_message(sent, embed=printbj(message.author, True, "Tie! Money Back.", 16776960))
			update_money(message.author.id, bet, currency)
		elif playerscore>botscore:
			await client.edit_message(sent, embed=printbj(message.author, True, "Your score is higher than the dealer's. You Win!", 3407616))
			update_money(message.author.id, bet*2, currency)
			win=True
		elif botscore>playerscore:
			await client.edit_message(sent, embed=printbj(message.author, True, "The dealer's score is higher than yours. You lose.", 16711718))

		profit(win, currency, bet)

		c.execute("DELETE FROM bj WHERE id={}".format(message.author.id))
		conn.commit()
	################################
	elif message.content==("$keys") or message.content==("$k"):
		bronze=getvalue(message.author.id, "bronze", "rsmoney")
		silver=getvalue(message.author.id, "silver", "rsmoney")
		gold=getvalue(message.author.id, "gold", "rsmoney")

		embed = discord.Embed(color=13226456)
		embed.set_author(name=(str(message.author))[:-5]+"'s Keys", icon_url=str(message.author.avatar_url))
		embed.add_field(name="Bronze", value="**"+str(bronze)+"**", inline=True)
		embed.add_field(name="Silver", value="**"+str(silver)+"**", inline=True)
		embed.add_field(name="Gold", value="**"+str(gold)+"**", inline=True)
		await client.send_message(message.channel, embed=embed)
	###############################
	elif message.content.startswith("$buykey"):
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
		conn.commit()
	###############################
	elif message.content.startswith("$open"):
		try:
			roll=(round(random.uniform(0,100), 1))*10
			kind=(message.content).split(" ")[1]
			bronze=getvalue(message.author.id, "bronze", "rsmoney")
			silver=getvalue(message.author.id, "silver", "rsmoney")
			gold=getvalue(message.author.id, "gold", "rsmoney")
			if kind=="bronze":
				if bronze>=1:
					c.execute("UPDATE rsmoney SET bronze={} WHERE id={}".format(bronze-1, message.author.id))
					ranges=[range(0,7), range(7,15), range(15,24), range(24,40), range(40,59), range(59,80), range(80,103), range(103,128), range(128,157), range(157,192), range(192,248), range(248,340), range(340,493), range(493,594), range(594,685), range(685,763), range(763,829), range(829,891), range(891,946), range(946,994), range(994,1000)]
					sidecolor=11880979
				else:
					await client.send_message(message.channel, "You don't have any bronze keys to open!")
			elif kind=="silver":
				if silver>=1:
					c.execute("UPDATE rsmoney SET silver={} WHERE id={}".format(silver-1, message.author.id))
					ranges=[range(0,1), range(1,2), range(2,12), range(12,27), range(27,45), range(45,65), range(65,100), range(100,140), range(140,180), range(180,221), range(221,264), range(264,308), range(308,354), range(354,407), range(407,463), range(463,519), range(519,574), range(574,628), range(628,679), range(679,717), range(717,765), range(765,813), range(864,920), range(920,955), range(955,1000)]	
					sidecolor=13226456
				else:
					await client.send_message(message.channel, "You don't have any silver keys to open!")
			elif kind=="gold":
				if gold>=1:
					c.execute("UPDATE rsmoney SET gold={} WHERE id={}".format(gold-1, message.author.id))
					ranges=[range(0,1), range(1,3), range(3,6), range(6,10), range(10,18), range(18,28), range(28,50), range(50,75), range(75,101), range(101,129), range(129,169), range(169,229), range(229,279), range(279,354), range(354,419), range(419,479), range(479,531), range(531,585), range(585,641), range(641,706), range(706,761), range(761,861), range(861,930), range(930,966), range(966,1000)]
					sidecolor=16759822
				else:
					await client.send_message(message.channel, "You don't have any gold keys to open!")
			conn.commit()

			for counter, i in enumerate(ranges):
				if roll in i:
					index=counter
				else:
					continue

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
			conn.commit()

			update_money(message.author.id, int(price), "07")

			embed = discord.Embed(description="You recieved item: **"+str(item)+"**!", color=sidecolor)
			embed.add_field(name="Price", value="*"+formatfromk(int(price), "07")+"*", inline=True)
			embed.set_author(name=kind.title()+" Key Prize", icon_url=str(message.author.avatar_url))
			embed.set_thumbnail(url=str(url))
			await client.send_message(message.channel, embed=embed)
		except:
			await client.send_message(message.channel, "An **error** has occured. Make sure you use `$open (bronze, silver, or gold)`.")
	# ###############################
	elif message.content.startswith("$fp"):
		try:
			game=str(message.content).split(" ")[2]
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
						embed = discord.Embed(description="Congratulations! You won "+formatfromk(bet*2, game)+"!", color=3997475)
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
			await client.send_message(message.channel, "An **error** has occured. Make sure you use `$fp (Amount) (rs3 or 07)`.")
	###############################
	elif message.content.startswith("$top"):
		game=(message.content).split(" ")[1]
		if game=="rs3" or game=="osrs" or game=="07":
			if game=="rs3":
				c.execute("SELECT * From rsmoney ORDER BY rs3week DESC LIMIT 8")
				number=5
				prizes=["None", "None", "None", "None", "None", "None", "None", "None"]
			elif game=="osrs" or game=="07":
				c.execute("SELECT * From rsmoney ORDER BY osrsweek DESC LIMIT 8")
				number=6
				prizes=["5 Silver Keys", "3 Silver Keys", "1 Silver Key", "1 Bronze Key", "1 Bronze Key", "1 Bronze Key", "1 Bronze Key", "1 Bronze Key"]
				
			top=c.fetchall()
			words=""
			for counter, i in enumerate(top):
				userid=i[0]
				total=i[number]
				total=formatfromk(int(total),game)
				words+=(str(counter+1)+". <@"+str(userid)+"> - **"+total+"** - **"+prizes[counter]+"**\n\n")

			embed = discord.Embed(color=557823, description=words)
			embed.set_author(name="Top "+game.upper()+" Thisweek Wager", icon_url=str(message.server.icon_url))
			# days=abs(time.gmtime()[6]-4)
			# embed.set_footer(text="Days Until Reset: "+str(days))
			await client.send_message(message.channel, embed=embed)
		else:
			None
	###########################################
	elif message.content==("$please"):
		if str(message.channel.id)=='566165744954638346':
			if roulette!=41:
				await client.send_message(message.channel, "There is already a roulette game going on!")
			else:
				roulette=40
				embed = discord.Embed(description="A game of roulette has started! Use `bet (1st/2nd/3rd, 0-36, High/Low, Black/Red/Green, or Odd/Even) (Amount) (rs3 or 07)` to place a bet on the wheel.", color=3800857)
				embed.set_author(name="Roulette Game", icon_url=str(message.server.icon_url))
				embed.add_field(name="Time Left", value="**40** Seconds", inline=True)
				gif=random.choice(['https://bit.ly/2znjmak','https://bit.ly/2Zqh2dx','https://bit.ly/2NuBqHN'])
				embed.set_image(url=gif)
				roulettemsg = await client.send_message(message.channel, embed=embed)
		else:
			await client.send_message(message.channel, "This command can only be used in <#566165744954638346>.")
	###########################################
	elif message.content.startswith("bet "):
		try:
			if roulette!=41:
				areas=['1st','2nd','3rd','high','low','black','red','green','odd','even','0','1','2','3','4','5','6','7','8','9','10','11','12','13','14','15','16','17','18','19','20','21','22','23','24','25','26','27','28','29','30','31','32','33','34','35','36']
				game=str(message.content).split(" ")[3]
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
			await client.send_message(message.channel, "An **error** has occured. Make sure you use `bet (1st/2nd/3rd, 0-36, High/Low, Black/Red/Green, or Odd/Even) (Amount) (rs3 or 07)`.")
	###########################################
	elif message.content==("$menu"):
		embed = discord.Embed(description="""1. Blurberry Special\n
											2. Chef's Delight\n
											3. Cider\n
											4. Dragon Bitter\n
											5. Karamjan Rum\n
											6. Legendary Cocktail\n
											7. Nice Beer\n
											8. Purple Lumbridge\n
											9. Short Green Guy\n
											10. Wine of Zamorak\n
											11. Wizard's Mind Bomb\n
											""", color=3800857)
		embed.set_author(name="Drink Menu", icon_url=str(message.server.icon_url))
		await client.send_message(message.channel, embed=embed)
	###############################################
	elif message.content==("$drawraffle"):
		if isstaff(message.author.id,message.server.roles,message.author.roles)=="verified":
			c.execute("SELECT id,tickets FROM rsmoney")
			tickets=c.fetchall()
			entered=[]
			for i in tickets:
				for x in range(i[1]):
					entered+=str(i[0])
			winner=random.choice(entered)
			c.execute("UPDATE rsmoney SET tickets=0")
			conn.commit()

			embed = discord.Embed(description="<@"+winner+"> has won the raffle!", color=16729241)
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
			tickets=getvalue(int(message.author.id),"tickets","rsmoney")
			c.execute("UPDATE rsmoney SET tickets={} WHERE id={}".format(tickets+amount, member.id))
			conn.commit()
			await client.send_message(message.channel, "Tickets updated.")
		else:
			await client.send_message(message.channel, "Admin Command Only!")


client.loop.create_task(my_background_task())
Bot_Token = os.environ['TOKEN']
client.run(str(Bot_Token))
#https://discordapp.com/oauth2/authorize?client_id=580511336598077511&scope=bot&permissions=8
#heroku pg:psql postgresql-adjacent-85932 --app rstable
