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
# 				privacy boolean
# 				)""")
# c.execute("INSERT INTO rsmoney VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)", ("546184449373634560",0,0,0,0,0,0,"None",False))
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
# conn.commit()

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

# c.execute("DROP TABLE cash")
# c.execute("""CREATE TABLE cash (
# 				id text,
# 				way text,
# 				code integer
# 				)""")
# conn.commit()

# c.execute("DROP TABLE hosts")
# c.execute("""CREATE TABLE hosts (
# 				id bigint,
# 				bets text,
# 				streak text
# 				)""")
# conn.commit()

client = discord.Client()


def add_member(userid,rs3,osrs,usd):
	c.execute("INSERT INTO rsmoney VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)", (userid,rs3,osrs,0,0,0,0,"ClientSeed",False))
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
		if score>10:
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
######################################################################################

#Predefined Variables

colors=["A","B","C","D","E","F","0","1","2","3","4","5","6","7","8","9"]
nextgiveaway=1
participants=[]
flowers=["Red","Orange","Yellow","Pastel","Blue","Purple","Mixed"]
sidecolors=[16711680, 16743712, 16776960, 7399068, 1275391, 16730111, 16777215]
pictures=["https://vignette.wikia.nocookie.net/2007scape/images/8/8d/Red_flowers.png/revision/latest?cb=20151223232624",
			"https://vignette.wikia.nocookie.net/2007scape/images/f/f9/Orange_flowers.png/revision/latest?cb=20151223232623",
			"https://vignette.wikia.nocookie.net/2007scape/images/b/b8/Yellow_flowers.png/revision/latest?cb=20151223232627",
			"https://vignette.wikia.nocookie.net/2007scape/images/8/8f/Assorted_flowers.png/revision/latest?cb=20151223232621",
			"https://vignette.wikia.nocookie.net/2007scape/images/5/59/Blue_flowers.png/revision/latest?cb=20151223232622",
			"https://vignette.wikia.nocookie.net/2007scape/images/c/c3/Purple_flowers.png/revision/latest?cb=20151223232623",
			"https://vignette.wikia.nocookie.net/2007scape/images/e/ec/Mixed_flowers.png/revision/latest?cb=20151223232622"]


async def my_background_task():
	global nextgiveaway,participants,winner
	await client.wait_until_ready()
	while not client.is_closed:
		channel = discord.Object(id='566165744954638346')
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
			None
		# channel = discord.Object(id='444569488948461569')
		# if nextgiveaway==1:
		# 	if len(participants)<1:
		# 		embed = discord.Embed(description="Couldn't determine a giveaway winner. Next giveaway in __15 minutes__.", color=557823)
		# 		embed.set_author(name="Giveaway", icon_url="https://cdn.discordapp.com/icons/444569488491413506/fb7ac7ed9204c85dd640d86e7358f1b8.jpg")
		# 		await client.send_message(channel, embed=embed)
		# 	else:
		# 		winner=random.choice(participants)
		# 		embed = discord.Embed(description="<@"+winner+"> has won **100k** 07! Next giveaway in __15 minutes__.", color=557823)
		# 		embed.set_author(name="Giveaway", icon_url="https://cdn.discordapp.com/icons/444569488491413506/fb7ac7ed9204c85dd640d86e7358f1b8.jpg")
		# 		await client.send_message(channel, embed=embed)
		# 		update_money(winner, 100, "07")
		# 		participants=[]
		# 	nextgiveaway=15
		# else:
		# 	nextgiveaway=1
		# 	embed = discord.Embed(description="Say something in the next minute to be entered in a **100k** 07 Giveaway!", color=557823)
		# 	embed.set_author(name="Giveaway", icon_url="https://cdn.discordapp.com/icons/444569488491413506/fb7ac7ed9204c85dd640d86e7358f1b8.jpg")
		# 	await client.send_message(channel, embed=embed)
		await asyncio.sleep(nextgiveaway*60)




@client.event
async def on_ready():
	print("Bot Logged In!")

@client.event
async def on_message_delete(message):
	await client.send_message(client.get_channel("473944352427868170"), str(message.author)+" said: \""+str(message.content)+"\"")

@client.event
async def on_message(message):
	message.content=(message.content).lower()

	# if nextgiveaway==1 and message.channel.id=="444569488948461569" and message.server.id=="444569488491413506":
	# 	if str(message.author.id) not in participants and str(message.author.id)!="456484773783928843":
	# 		participants.append(str(message.author.id))

	if message.server.id!="518832231532331018":
		None
	#############################################
	elif message.content.startswith("!input"):
		print(message.content)
    ###########################################
	elif message.content==("!log"):
		if isstaff(message.author.id,message.server.roles,message.author.roles)=="verified":
			await client.send_message(message.channel, "Goodbye!")
			await client.logout()
		else:
			None
	################################################
	elif message.content.startswith('!colorpicker') or message.content.startswith('!colourpicker'):
		color=('')
		for i in range(6):
			color+=random.choice(colors)
		if message.content.startswith("!colorpicker"):
			await client.send_message(message.channel, "Your random color is https://www.colorhexa.com/"+color)
		elif message.content.startswith("!colourpicker"):
			await client.send_message(message.channel, "Your random colour is https://www.colorhexa.com/"+color)
	# ###############################################
	# elif message.content.startswith("!emoji"):
	# 	try:
	# 		await client.delete_message(message)
	# 	except:
	# 		print("No permissions to delete messages. RIP")
	# 	finalmessage=("")
	# 	characters=[]
	# 	characters+=(str(message.content).lower())[7:]
	# 	for i in characters:
	# 		if i==" ":
	# 			finalmessage+=":white_small_square: "
	# 		elif i in "abcdefghijklmnopqrstuvwxyz":
	# 			finalmessage+=":regional_indicator_"+i+": "
	# 		elif i=="!":
	# 			finalmessage+=":grey_exclamation: "
	# 	await client.send_message(message.channel, finalmessage)
	# ############################################
	elif message.content.startswith("!poll"):
		message.content=(message.content).title()
		embed = discord.Embed(description="Respond below with 👍 for YES, 👎 for NO, or 🤔 for UNSURE/NEUTRAL", color=16724721)
		embed.set_author(name=str(message.content[6:]), icon_url=str(message.server.icon_url))
		embed.set_footer(text="Polled on: "+str(datetime.datetime.now())[:-7])
		sent = await client.send_message(message.channel, embed=embed)
		await client.add_reaction(sent,"👍")
		await client.add_reaction(sent,"👎")
		await client.add_reaction(sent,"🤔")
	#############################################
	elif message.content.startswith("!userinfo"):
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
	elif message.content.startswith("!setseed"):
		if str(message.channel.id)=="559182875316977694":
			clientseed=str((message.content)[9:])
			if len(clientseed)>20:
				await client.send_message(message.channel, "That client seed is too long. Please try a shorter one. (20 Character Limit)")
			else:
				c.execute("UPDATE rsmoney SET clientseed='{}' WHERE id={}".format(str(clientseed), int(message.author.id)))
				conn.commit()
				await client.send_message(message.channel, "Your client seed has been set to "+(message.content)[9:]+".")
		else:
			await client.send_message(message.channel, "This command can only be used in <#559182875316977694> to prevent spam.")
	# #####################################








	###################################################
	elif (message.content).lower()==("!wallet") or (message.content).lower()==("!w") or message.content=="!$":
		osrs=getvalue(int(message.author.id),"07","rsmoney")
		rs3=getvalue(int(message.author.id),"rs3","rsmoney")

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
		embed = discord.Embed(color=sidecolor)
		embed.set_author(name=(str(message.author))[:-5]+"'s Wallet", icon_url=str(message.author.avatar_url))
		embed.add_field(name="RS3 Balance", value=rs3, inline=True)
		embed.add_field(name="07 Balance", value=osrs, inline=True)
		if getvalue(int(message.author.id), "privacy","rsmoney")==True:
			await client.send_message(message.channel, embed=embed)
		else:
			await client.send_message(message.channel, embed=embed)



	elif  ((message.content).lower()).startswith("!wallet <@") or ((message.content).lower()).startswith("!w <@") or message.content.startswith("!$ <@"):
		if message.content.startswith("!wallet <@"):
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
			embed = discord.Embed(color=sidecolor)
			embed.set_author(name=(str(member))[:-5]+"'s Wallet", icon_url=str(member.avatar_url))
			embed.add_field(name="RS3 Balance", value=rs3, inline=True)
			embed.add_field(name="07 Balance", value=osrs, inline=True)
			await client.send_message(message.channel, embed=embed)
			
		elif getvalue(int(member.id), "privacy","rsmoney")==True:
			await client.send_message(message.channel, "Sorry, that user has wallet privacy mode enabled.")
	##########################################
	elif message.content.startswith("!clear"):
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
			await client.send_message(message.channel, "An **error** occured. Make sure you use `!clear (rs3 or 07) (@user)`")
	###########################################
	elif (message.content).startswith("!update 07") or (message.content).startswith("!update rs3"):
		try:
			if isstaff(message.author.id,message.server.roles,message.author.roles)=="verified":
				maximum=False
				if (str(message.content).split(" ")[3][-1:]).lower()=="b":
					if int(str(message.content).split(" ")[3][:-1])>100:
						await client.send_message(message.channel, "You can only give up to 100b at one time for...reasons.")
						maximum=True

				if maximum==False:
					game=(message.content).split(" ")[1]
					amount=formatok(str(message.content).split(" ")[3], game)

					try:
						int(str(message.content).split(" ")[2][2:3])
						member=message.server.get_member(str(message.content).split(" ")[2][2:-1])
					except:
						member=message.server.get_member(str(message.content).split(" ")[2][3:-1])

					update_money(int(member.id), amount, game)
	
					embed = discord.Embed(description="<@"+str(member.id)+">'s wallet has been updated.", color=5174318)
					embed.set_author(name="Update Request", icon_url=str(message.author.avatar_url))
					await client.send_message(message.channel, embed=embed)
				else:
					None
			else:
				await client.send_message(message.channel, "Admin Command Only!")
		except:
			await client.send_message(message.channel, "An **error** has occured. Make sure you use `!update (rs3 or 07) (@user) (amount)`.")
	############################################
	elif message.content.startswith("!help") or message.content.startswith("!commands"):
		embed = discord.Embed(description=  #"\n `!colorpicker` - Shows a random color\n" +
											#"\n `!start unscramble` - Starts a game where you unscramble a word\n" +
											#"\n `!start hangman` - Starts a game of hangman\n" +
											#"\n `!random (SIZE)` - Starts a game where you guess a number between 1 and the given size\n" +
											#"\n `!poll (QUESTION)` - Starts a Yes/No poll with the given question\n" +
											"\n `!w`, `!wallet`, or `!$` - Checks your own wallet\n" +
											"\n `!w (@USER)`, `!wallet (@USER)`, or `!$ (@USER)` - Checks that user's wallet\n" +
											#"\n `!flower (AMOUNT) (hot or cold)` - Hot or cold gives x2, 5% \\of auto loss\n" +
											"\n `!50 (rs3 or 07) (BET)` - Must roll above 50, x1.8 payout\n" +
											"\n `!53 (rs3 or 07) (BET)` - Must roll above 53, x2 payout\n" +
											"\n `!75 (rs3 or 07) (BET)` - Must roll above 75, x3 payout\n" +
											"\n `!95 (rs3 or 07) (BET)` - Must roll above 95, x7 payout\n" +
											#"\n `!swap (rs3 or 07) (AMOUNT)` - Swaps that amount of gold to the other game" +
											#"\n `!rates` - Shows the swapping rates between currencies" +
											"\n `!bj (rs3 or 07) (AMOUNT)` - Starts a game of blackjack with the bot\n" +
											#"\n `!deposit (rs3 or 07) (AMOUNT)` - Notifes a cashier that you want to deposit the amount to your wallet\n" +
											#"\n `!withdraw (rs3 or 07) (AMOUNT)` - Notifes a cashier that you want to withdraw the amount from your wallet\n" +
											"\n `!transfer (rs3 or 07) (@USER) (AMOUNT)` - Transfers that amount from your wallet to the user's wallet\n" +
											"\n `!wager`, or `!total bet` or `!tb` - Shows your total amount bet for rs3 and 07\n" +
											"\n `!thisweek` - Shows your total amount bet for rs3 and 07 this week\n", color=16771099)

		embed.set_author(name="Bot Commands", icon_url=str(message.server.icon_url))
		await client.send_message(message.channel, embed=embed)
		# await client.send_message(message.channel, "The commands have been sent to your private messages.")
	###################################
	elif ((message.content).lower()).startswith("!transfer rs3") or ((message.content).lower()).startswith("!transfer 07"):
		try:
			transfered=formatok((str(message.content).split(" ")[3]), str(message.content).split(" ")[1])
			enough=True

			if str(message.content).split(" ")[1]=="rs3":
				if transfered<1:
					await client.send_message(message.channel, "You must transfer at least **1k** 07.")
					enough=False

			elif str(message.content).split(" ")[1]=="07":
				if transfered<1:
					await client.send_message(message.channel, "You must transfer at least **1k** RS3.")
					enough=False

			currency=str(message.content).split(" ")[1]
			current=getvalue(int(message.author.id),currency,"rsmoney")

			if enough==True:
				if current>=transfered:
					try:
						int(str(message.content).split(" ")[2][2:3])
						member=message.server.get_member(str(message.content).split(" ")[2][2:-1])
					except:
						member=message.server.get_member(str(message.content).split(" ")[2][3:-1])
					
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
			await client.send_message(message.channel, "An **error** has occured. Make sure you use `!transfer (rs3 or 07) (@user) (Amount you want to give)`.")
	###################################
	# elif ((message.content).lower()).startswith("!withdraw") or ((message.content).lower()).startswith("!deposit"):
	# 	try:
	# 		enough=True
	# 		cashing=formatok(str(message.content).split(" ")[2], str(message.content).split(" ")[1])
	# 		currency=str(message.content).split(" ")[1]
	# 		current=getvalue(int(message.author.id), currency, "rsmoney")

	# 		if message.content.startswith("!withdraw"):
	# 			way="withdraw"
	# 			if currency=="rs3":
	# 				if cashing<10000:
	# 					await client.send_message(message.channel, "<@"+str(message.author.id)+">, You must withdraw at least **10m** rs3.")
	# 					enough=False
	# 			elif currency=="07":
	# 				if cashing<2000:
	# 					await client.send_message(message.channel, "<@"+str(message.author.id)+">, You must withdraw at least **2m** 07.")
	# 					enough=False

	# 			if cashing>current:
	# 				await client.send_message(message.channel, "<@"+str(message.author.id)+">, You don't have that much money to withdraw!")
	# 				enough=False
					
	# 		else:
	# 			way="deposit"
	# 			if currency=="rs3":
	# 				if cashing<5000:
	# 					await client.send_message(message.channel, "<@"+str(message.author.id)+">, You must deposit atleast **5m** rs3.")
	# 					enough=False
	# 			elif currency=="07":
	# 				if cashing<1000:
	# 					await client.send_message(message.channel, "<@"+str(message.author.id)+">, You must deposit atleast **1m** 07.")
	# 					enough=False

	# 		if currency=="rs3" or currency=="07":
	# 			if enough==True:
	# 				cashing=formatfromk(cashing, currency)
	# 				c.execute("SELECT code FROM cash")
	# 				codelist=c.fetchall()
	# 				codes=[]
	# 				for i in codelist:
	# 					codes.append(int(i[0]))
	# 				while True:
	# 					code=random.randint(1,999)
	# 					if code in codes:
	# 						continue
	# 					else:
	# 						break
	# 				c.execute("INSERT INTO cash VALUES (%s, %s, %s)", (str(message.author.id), way, code))
	# 				conn.commit()
	# 				await client.send_message(message.server.get_channel("459923177376579596"), "<@&459899438643675136>, <@"+str(message.author.id)+"> wants to "+way+" **"+cashing+"** "+currency+". Use `!accept "+str(code)+"`.")
	# 				embed = discord.Embed(description="A message has been sent to a cashier. Your request will be processed and you will be messaged soon.", color=5174318)
	# 				embed.set_author(name=way.title(), icon_url=str(message.server.icon_url))
	# 				await client.send_message(message.channel, embed=embed)
	# 			else:
	# 				None
	# 		else:
	# 			await client.send_message(message.channel, "An **error** has occured. Make sure you use `"+str(message.content).split(" ")[0]+" (rs3 or 07) (Amount you want to cash in/out)`.")
	# 	except:
	# 		await client.send_message(message.channel, "An **error** has occured. Make sure you use `"+str(message.content).split(" ")[0]+" (rs3 or 07) (Amount you want to cash in/out)`.")
	###################################
	elif message.content.startswith("!53") or message.content.startswith("!50") or message.content.startswith("!75") or message.content.startswith("!95"):
		try:
			game=str(message.content).split(" ")[1]
			bet=formatok(str(message.content).split(" ")[2], game)
			current=getvalue(message.author.id, game,"rsmoney")

			if isenough(bet, game)[0]:
				if message.content.startswith("!53x2") or message.content.startswith("!53"):
					title="53x2"
					odds=54
					multiplier=2
				elif message.content.startswith("!50x1.8") or message.content.startswith("!50"):
					title="50x1.8"
					odds=51
					multiplier=1.8
				elif message.content.startswith("!75x3") or message.content.startswith("!75"):
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
			await client.send_message(message.channel, "An **error** has occured. Make sure you use `$(50, 53, 75, or 95) (rs3 or 07) (BET)`.")
	#############################
	elif ((message.content).lower()).startswith("!wager") or ((message.content).lower()).startswith("!total bet") or ((message.content).lower()).startswith("!tb"):
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
	elif message.content=="!thisweek":
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
	elif message.content=="!reset thisweek":
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
	elif message.content=="!privacy on":
		c.execute("UPDATE rsmoney SET privacy=True WHERE id={}".format(message.author.id))
		conn.commit()
		embed = discord.Embed(description="<@"+str(message.author.id)+">'s wallet privacy is now enabled.", color=5174318)
		embed.set_author(name="Privacy Mode", icon_url=str(message.author.avatar_url))
		await client.send_message(message.channel, embed=embed)
	#################################
	elif message.content=="!privacy off":
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
	elif message.content.startswith("!bj"):
		try:
			deck="aC|aS|aH|aD|2C|2S|2H|2D|3C|3S|3H|3D|4C|4S|4H|4D|5C|5S|5H|5D|6C|6S|6H|6D|7C|7S|7H|7D|8C|8S|8H|8D|9C|9S|9H|9D|10C|10S|10H|10D|jC|jS|jH|jD|qC|qS|qH|qD|kC|kS|kH|kD"
			currency=(message.content).split(" ")[1]
			bet=formatok((message.content).split(" ")[2], currency)
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
			await client.send_message(message.channel, "An **error** has occured. Make sure you use `!bj (rs3 or 07) (Amount)`.")
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
	# elif message.content.startswith("!accept"):
	# 	if str(message.channel.id)=="459923177376579596":
	# 		code=int((message.content).split(" ")[1])
	# 		c.execute("SELECT code FROM cash")
	# 		codelist=c.fetchall()
	# 		codes=[]
	# 		for i in codelist:
	# 			codes.append(int(i[0]))
	# 		if code in codes:
	# 			c.execute("SELECT id FROM cash WHERE code={}".format(code))
	# 			userid=str(c.fetchone()[0])
	# 			c.execute("SELECT way FROM cash WHERE code={}".format(code))
	# 			way=str(c.fetchone()[0])
	# 			embed = discord.Embed(description="<@"+userid+">, <@"+str(message.author.id)+"> will perform your "+way+".", color=5174318)
	# 			embed.set_author(name=way.title(), icon_url=str(message.server.icon_url))
	# 			await client.send_message(message.server.get_channel("476760411707015168"), embed=embed)
	# 			await client.send_message(message.channel, "Accepted. Please DM them now.")
	# 			c.execute("DELETE FROM cash WHERE code={}".format(code))
	# 			conn.commit()
	# 		else:
	# 			await client.send_message(message.channel, "There is no deposit/withdraw request with that code.")
	# 	else:
	# 		None
	#################################
	# elif message.content.startswith("!top"):
	# 	game=(message.content).split(" ")[1]
	# 	if game=="rs3" or game=="osrs" or game=="07":
	# 		if game=="rs3":
	# 			c.execute("SELECT * From rsmoney ORDER BY rs3week DESC LIMIT 4")
	# 			number=5
	# 			prizes=["500m", "250m", "100m", "50m"]
	# 		elif game=="osrs" or game=="07":
	# 			c.execute("SELECT * From rsmoney ORDER BY osrsweek DESC LIMIT 4")
	# 			number=6
	# 			prizes=["100m", "50m", "25m", "10m"]
				
	# 		top=c.fetchall()
	# 		words=""
	# 		for counter, i in enumerate(top):
	# 			userid=i[0]
	# 			total=i[number]
	# 			total=formatfromk(int(total),game)
	# 			words+=(str(counter+1)+". <@"+str(userid)+"> - **"+total+"** - **"+prizes[counter]+"**\n\n")

	# 		embed = discord.Embed(color=557823, description=words)
	# 		embed.set_author(name="Top "+game.upper()+" Thisweek Wager", icon_url=str(message.server.icon_url))
	# 		days=abs(time.gmtime()[6]-4)
	# 		embed.set_footer(text="Days Until Reset: "+str(days))
	# 		await client.send_message(message.channel, embed=embed)
	# 	else:
	# 		None
	###################################
	# elif message.content.startswith("!flower"):
	# 	try:
	# 		currency=(message.content).split(" ")[1]
	# 		bet=formatok((message.content).split(" ")[2], currency)
	# 		current=getvalue(message.author.id, currency, "rsmoney")
	# 		number=random.randint(0,100)
	# 		if number in range(96,101):
	# 			index=6
	# 		elif number in range(0,16):
	# 			index=0
	# 		elif number in range(16,32):
	# 			index=1
	# 		elif number in range(32,48):
	# 			index=2
	# 		elif number in range(48,64):
	# 			index=3
	# 		elif number in range(64,80):
	# 			index=4
	# 		elif number in range(80,96):
	# 			index=5
	# 		flower=flowers[index]
	# 		sidecolor=sidecolors[index]
	# 		picture=pictures[index]

	# 		if isenough(bet, currency)[0]:	
	# 			if current>=bet:
	# 				win=False
	# 				if (message.content).split(" ")[3]=="hot":
	# 					if flower=="Red" or flower=="Orange" or flower=="Yellow":
	# 						multiplier=2
	# 						win=True
	# 					else:
	# 						multiplier=0
	# 				elif (message.content).split(" ")[3]=="cold":
	# 					if flower=="Blue" or flower=="Pastel" or flower=="Purple":
	# 						multiplier=2
	# 						win=True
	# 					else:
	# 						multiplier=0

	# 				winnings=(bet*multiplier)
	# 				if isinstance(winnings, float):
	# 					if (winnings).is_integer():
	# 						winnings=int(winnings)
	# 				winnings=formatfromk(winnings, currency)

	# 				if win==True:
	# 					words=("Congratulations! The color of the flower was **"+flower+"**. "+str(message.author)+" won **"+winnings+"** "+currency+".")
	# 					update_money(int(message.author.id), bet, currency)
	# 				else:
	# 					words=("Sorry, the color the flower was **"+flower+"**. "+str(message.author)+" lost **"+formatfromk(bet, currency)+"** "+currency+".")
	# 					update_money(int(message.author.id), bet*-1, currency)

	# 				embed = discord.Embed(description=words, color=sidecolor)
	# 				embed.set_author(name=(str(message.author))[:-5]+"'s Gamble", icon_url=str(message.author.avatar_url))
	# 				embed.set_thumbnail(url=picture)
	# 				await client.send_message(message.channel, embed=embed)

	# 				ticketbets(message.author.id, bet, currency)
	# 				profit(win, currency, bet)

	# 			else:
	# 				await client.send_message(message.channel, "<@"+str(message.author.id)+">, You don't have that much gold!")
	# 		else:
	# 			await client.send_message(message.channel, (isenough(bet, currency))[1])
	# 	except:
	# 	 	await client.send_message(message.channel, "An **error** has occured. Make sure you use `!flower (rs3 or 07) (Amount) (hot or cold)`.")
	##########################
	# elif message.content=="!profit":
	# 	if isstaff(message.author.id,message.server.roles,message.author.roles)=="verified":
	# 		c.execute("SELECT osrsprofit FROM data")
	# 		osrsprofit=int(c.fetchone()[0])
	# 		if osrsprofit<0:
	# 			osrsprofit=0
	# 		c.execute("SELECT rs3profit FROM data")
	# 		rs3profit=int(c.fetchone()[0])
	# 		if rs3profit<0:
	# 			rs3profit=0
	# 		total=formatfromk(rs3profit+(osrsprofit*6.5), "rs3")

	# 		embed = discord.Embed(color=16773410)
	# 		embed.add_field(name="RS3 Profit", value=formatfromk(rs3profit, "rs3"), inline=True)
	# 		embed.add_field(name="07 Profit", value=formatfromk(osrsprofit, "07"), inline=True)
	# 		embed.add_field(name="Total Profit (RS3)", value=total, inline=True)
	# 		embed.set_author(name="Casino King Bot Profit", icon_url=str(message.server.icon_url))
	# 		await client.send_message(message.channel, embed=embed)
	# 	else:
	# 		None
	# ###########################
	# elif message.content=="!reset profit":
	# 	if isstaff(message.author.id,message.server.roles,message.author.roles)=="verified":
	# 		c.execute("UPDATE data SET osrsprofit=0")
	# 		c.execute("UPDATE data SET rs3profit=0")
	# 		conn.commit()
	# 		await client.send_message(message.channel, "Reset.")
	# 	else:
	# 		None
	##########################
	# elif message.content=="!claim 07":
	# 	claimed=getvalue(message.author.id, "claimed", "rsmoney")
	# 	if claimed==False:
	# 		c.execute("UPDATE rsmoney SET claimed={}".format(True))
	# 		update_money(message.author.id, 100, "07")
	# 		await client.send_message(message.channel, "Claimed! Use `!w` to view your wallet.")
	# 	else:
	# 		await client.send_message(message.channel, "You have already claimed your free 100k 07!")
	# ###########################
	# elif message.content.startswith("!bet"):
	# 	try:
	# 		try:
	# 			int(str(message.content).split(" ")[2][2:3])
	# 			host=message.server.get_member(str(message.content).split(" ")[2][2:-1])
	# 		except:
	# 			host=message.server.get_member(str(message.content).split(" ")[2][3:-1])
	# 		c.execute("SELECT id FROM hosts")
	# 		hosts=c.fetchall()
	# 		print(hosts[0])
	# 		if int(host.id) in hosts[0]:
	# 			currency=(message.content).split(" ")[1]
	# 			bet=formatok((message.content).split(" ")[3], currency)
	# 			current=getvalue(message.author.id, currency)
	# 			if current>=bet:
	# 				update_money(message.author.id, bet*-1, currency)
	# 				if bet>=5000:
	# 					tickets=getvalue(message.author.id, "tickets")
	# 					c.execute("UPDATE rsmoney SET tickets={} WHERE id={}".format(tickets+5, message.author.id))
	# 					conn.commit()
	# 				c.execute("UPDATE hosts SET bets='{}' WHERE id={}".format("<@"+str(message.author.id)+"> - "+formatfromk(bet, currency)+"\n", host.id))
	# 				conn.commit()
	# 				await client.send_message(message.channel, "You have bet "+formatfromk(bet, currency)+" "+currency+" on <@"+str(host.id)+">.")
	# 			else:
	# 				await client.send_message(message.channel, "You do not have enough gold to bet that much.")
	# 		else:
	# 			await client.send_message(message.channel, "That is not an open host.")
	# 	except:
	# 	 	await client.send_message(message.channel, "An **error** has occured. Make sure you use `!bet (07 or rs3) (@HOST) (Amount)`.")
	###################################
	# elif message.content.startswith("!bets"):
	# 	try:
	# 		int(str(message.content).split(" ")[1][2:3])
	# 		host=message.server.get_member(str(message.content).split(" ")[1][2:-1])
	# 	except:
	# 		host=message.server.get_member(str(message.content).split(" ")[1][3:-1])
	# 	c.execute("SELECT id FROM hosts")
	# 	hosts=c.fetchall()
	# 	if int(host.id) in hosts[0]:
	# 		c.execute("SELECT bets FROM hosts WHERE id={}".format(host.id))
	# 		bets=str(c.fetchone()[0])
	# 		embed = discord.Embed(color=0)
	# 		embed.add_field(name="Bets", value=bets)
	# 		embed.set_author(name="Bets On "+str(host), icon_url=str(host.avatar_url))
	# 		await client.send_message(message.channel, embed=embed)	
	# 	else:
	# 		await client.send_message(message.channel, "That is not an open host.")
	# ################################
	# elif message.content.startswith("!addbet"):
	# 	try:
	# 		c.execute("SELECT id FROM hosts")
	# 		hosts=c.fetchall()
	# 		if int(message.author.id) in hosts[0]:
	# 			try:
	# 				int(str(message.content).split(" ")[1][2:3])
	# 				bettor=message.server.get_member(str(message.content).split(" ")[1][2:-1])
	# 			except:
	# 				bettor=message.server.get_member(str(message.content).split(" ")[1][3:-1])
	# 			bet=formatok((message.content).split(" ")[2], "rs3")
	# 			bets=getvalue(message.author.id,"bets","hosts")
	# 			c.execute("UPDATE hosts SET bets='{}' WHERE id={}".format(str(bets)+"<@"+str(bettor.id)+"> - "+formatfromk(bet, "rs3")+"\n", message.author.id))
	# 			conn.commit()
	# 			await client.send_message(message.channel, "You have added a bet of "+formatfromk(bet, "rs3")+" from "+str(bettor)+" on yourself.")
	# 		else:
	# 			await client.send_message(message.channel, "You must be an open host to add a bet to your pot.")
	# 	except:
	# 	 	await client.send_message(message.channel, "An **error** has occured. Make sure you use `!addbet (@USER) (Amount)`.")
	# ###############################
	# elif message.content==("!open"):
	# 	host=get(message.server.roles, name="Host")
	# 	if host in message.author.roles:
	# 		c.execute("INSERT INTO hosts VALUES (%s, %s, %s)", (int(message.author.id), "", ":fresh: "))
	# 		conn.commit()
	# 		await client.send_message(message.channel, "You are now open.")
	# 	else:
	# 		await client.send_message(message.channel, "You need the host role to open.")

	# elif message.content==("!close"):
	# 	host=get(message.server.roles, name="Host")
	# 	if host in message.author.roles:
	# 		c.execute("DELETE FROM hosts WHERE id={}".format(message.author.id))
	# 		conn.commit()
	# 		await client.send_message(message.channel, "You are now closed. See you later!")
	# 	else:
	# 		await client.send_message(message.channel, "You need the host role to close.")
	# ###########################
	# elif message.content.startswith("!streak"):
	# 	try:
	# 		int(str(message.content[10:11]))
	# 		host=message.server.get_member(message.content[10:28])
	# 	except:
	# 		host=message.server.get_member(message.content[11:29])
	# 	c.execute("SELECT id FROM hosts")
	# 	hosts=c.fetchall()
	# 	if int(host.id) in hosts[0]:
	# 		streak=str(getvalue(host.id,"streak","hosts"))
	# 		embed = discord.Embed(color=0, description=streak)
	# 		embed.set_author(name=str(message.author)[:-5]+"'s Wallet", icon_url=str(host.avatar_url))
	# 		await client.send_message(message.channel, embed=embed)	
	# 	else:
	# 		await client.send_message(message.channel, "That is not an open host.")
	# #########################
	# elif message.content==("!win") or message.content==("!loss"):
	# 	turnout=str(message.content)[1:]
	# 	c.execute("SELECT id FROM hosts")
	# 	hosts=c.fetchall()
	# 	if int(message.author.id) in hosts[0]:
	# 		streak=getvalue(message.author.id,"streak","hosts")
	# 		c.execute("UPDATE hosts SET streak={} WHERE id={}".format(streak+":"+turnout+": ", message.author.id))
	# 		conn.commit()
	# 		await client.send_message(message.channel, "Added a "+turnout+" to your streak!")
	# 	else:
	# 		await client.send_message(message.channel, "You are not an open host.")
	# #############################

client.loop.create_task(my_background_task())
Bot_Token = os.environ['TOKEN']
client.run(str(Bot_Token))
#https://discordapp.com/oauth2/authorize?client_id=580511336598077511&scope=bot&permissions=8
#heroku pg:psql postgresql-adjacent-85932 --app rstable