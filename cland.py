import discord
import asyncio
import random
from time import sleep
import datetime
import os
import psycopg2
import hashslingingslasher as hasher

DATABASE_URL = os.environ['DATABASE_URL']
conn = psycopg2.connect(DATABASE_URL, sslmode='require')
c=conn.cursor()

c.execute("DROP TABLE rsmoney")
c.execute("""CREATE TABLE rsmoney (
				id bigint,
				rs3 integer,
				osrs integer,
				usd float(2),
				rs3total bigint,
				osrstotal bigint,
				usdtotal float(2),
				clientseed text,
				tickets integer,
				privacy boolean
				)""")
conn.commit()


client = discord.Client()



def add_member(userid,rs3,osrs,usd):
	c.execute("INSERT INTO rsmoney VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", (userid,rs3,osrs,usd,0,0,0,"CryptoLandClientSeed",0,False))
	conn.commit()

def getvalue(userid,value):
	if value=="07":
		value="osrs"
	try:
		c.execute("SELECT rs3 FROM rsmoney WHERE id={}".format(userid))
		tester=int(c.fetchone()[0])
	except:
		print("New Member")
		add_member(int(userid),0,0,0)
		return 0

	c.execute("SELECT {} FROM rsmoney WHERE id={}".format(value, userid))

	if value=="usd" or value=="usdtotal":
		return float(c.fetchone()[0])
	elif value=="privacy":
		return bool(c.fetchone()[0])
	else:
		return int(c.fetchone()[0])

#amount should be in K not M
def update_money(userid,amount,currency):
	rs3=getvalue(int(userid),currency)
	osrs=getvalue(int(userid),currency)
	usd=getvalue(int(userid),currency)
	if currency=="07":
		c.execute("UPDATE rsmoney SET osrs={} WHERE id={}".format(osrs+amount, userid))
	elif currency=="rs3":
		c.execute("UPDATE rsmoney SET rs3={} WHERE id={}".format(rs3+amount, userid))
	elif currency.lower()=="usd":
		c.execute("UPDATE rsmoney SET usd={} WHERE id={}".format(float(usd)+float(amount), userid))
	conn.commit()

def isstaff(checkedid):
	for i in open("staff.txt"):
		if str(i.split(" ")[0])==str(checkedid):
			return "verified"

def formatok(amount, currency):
	#takes amount as string from message.content
	#returns an integer in K
	if (str(currency)).lower()=="usd":
		if (amount[-1:])=="$":
			return float(str(amount)[:-1])
		elif (amount[:1])=="$":
			return float(str(amount)[1:])
		else:
			return float(amount)
	if (amount[-1:]).lower()=="m":
		return int(float(str(amount[:-1]))*1000)
	elif (amount[-1:]).lower()=="k":
		return int(str(amount[:-1]))
	elif (amount[-1:]).lower()=="b":
		return int(float(str(amount[:-1]))*1000000)
	else:
		return int(float(amount)*1000)

def formatfromk(amount, currency):
	#takes amount as integer in K
	#returns a string to be printed
	if (str(currency)).lower()=="usd":
		if len(str(amount))==4:
			return "$"+'{0:.4g}'.format(amount)
		elif len(str(amount))==5:
			return "$"+'{0:.5g}'.format(amount)
		else:
			return "$"+'{0:.6g}'.format(amount)	

	amount=round((amount*0.001), 2)
	if isinstance(amount, float):
		if (amount).is_integer():
			amount=int(amount)
	return str(amount)+"M"

	# if amount>=1000000:
	# 	if len(str(amount))==7:
	# 		return '{0:.3g}'.format(amount*0.000001)+"B"
	# 	elif len(str(amount))==8:
	# 		return '{0:.4g}'.format(amount*0.000001)+"B"
	# 	else:
	# 		return '{0:.5g}'.format(amount*0.000001)+"B"
	# elif amount>=10000:
	# 	if len(str(amount))==5:
	# 		return '{0:.4g}'.format(amount*0.001)+"M"
	# 	elif len(str(amount))==6:
	# 		return '{0:.5g}'.format(amount*0.001)+"M"
	# else:
	# 	return str(amount)+"k"

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
	elif currency=="usd":
		if amount<1.00:
			words="The minimum amount you can bet is **$1** USD."
			return False, words
		else:
			return True, " "

def ticketbets(userid, bet, currency):
	ticket=0
	if currency=="rs3":
		if bet>=1000:
			ticket=int(bet/1000)
		totalbet=getvalue(userid, "rs3total")
		c.execute("UPDATE rsmoney SET rs3total={} WHERE id={}".format(totalbet+bet, userid))
	elif currency=="07":
		if bet>=1000:
			ticket=6*int(bet/1000)
		totalbet=getvalue(userid, "osrstotal")
		c.execute("UPDATE rsmoney SET osrstotal={} WHERE id={}".format(totalbet+bet, userid))
	elif currency=="usd":
		if bet>=1.00:
			ticket=8*int(bet)
		totalbet=getvalue(userid, "usdtotal")
		c.execute("UPDATE rsmoney SET usdtotal={} WHERE id={}".format(totalbet+bet, userid))

	tickets=getvalue(userid, "tickets")
	c.execute("UPDATE rsmoney SET tickets={} WHERE id={}".format(tickets+ticket, userid))
	conn.commit()
######################################################################################

#Predefined Variables
colors=["A","B","C","D","E","F","0","1","2","3","4","5","6","7","8","9"]
flowers=["Red","Orange","Yellow","Pastel","Blue","Purple"]
sidecolors=[16711680, 16743712, 16776960, 7399068, 1275391, 16730111]
duel=False

# async def my_background_task():
# 	await client.wait_until_ready()
# 	while not client.is_closed:
# 		await asyncio.sleep(1800)




@client.event
async def on_ready():
	print("Bot Logged In!");

@client.event
async def on_reaction_add(reaction, user):
	None

@client.event
async def on_message_delete(message):
	None
	# for attachment in message.attachments:
	# 	await client.send_message(message.server.get_channel("465634969633554443"), "\"*"+str(attachment.get('proxy_url'))+"*\" was posted by **"+str(message.author)+"**.")
	# if message.content=="":	
	# 	None
	# else:
	# 	await client.send_message(message.server.get_channel("465634969633554443"), "\""+str(message.content)+"\" was posted by "+str(message.author)+".")


@client.event
async def on_message(message):
	global words, duel
	message.content=(message.content).lower()

	#############################################
	if message.content.startswith("!input"):
		print(message.content)
    ###########################################
	elif message.content==("!log"):
		if str(message.author.id)==("199630284906430465"):
			await client.send_message(message.channel, "Goodbye!")
			await client.logout()
	################################################
	elif message.content.startswith('!colorpicker') or message.content.startswith('!colourpicker'):
		color=('')
		for i in range(6):
			color+=random.choice(colors)
		if message.content.startswith("!colorpicker"):
			await client.send_message(message.channel, "Your random color is https://www.colorhexa.com/"+color)
		elif message.content.startswith("!colourpicker"):
			await client.send_message(message.channel, "Your random colour is https://www.colorhexa.com/"+color)
	###############################################
	elif message.content.startswith("!emoji"):
		try:
			await client.delete_message(message)
		except:
			print("No permissions to delete messages. RIP")
		finalmessage=("")
		characters=[]
		characters+=(str(message.content).lower())[7:]
		for i in characters:
			if i==" ":
				finalmessage+=":white_small_square: "
			elif i in "abcdefghijklmnopqrstuvwxyz":
				finalmessage+=":regional_indicator_"+i+": "
			elif i=="!":
				finalmessage+=":grey_exclamation: "
		await client.send_message(message.channel, finalmessage)
	############################################
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
	#####################################
	elif message.content.startswith("!setseed"):
		clientseed=str((message.content)[15:])
		if len(clientseed)>20:
			await client.send_message(message.channel, "That client seed is too long. Please try a shorter one. (20 Character Limit)")
		else:
			await client.send_message(message.channel, "Your client seed has been set to "+(message.content)[15:]+".")
			c.execute("UPDATE rsmoney SET clientseed={} WHERE id={}".format(clientseed, int(message.author.id)))
	#####################################








	###################################################
	elif (message.content).lower()==("!wallet") or (message.content).lower()==("!w") or message.content=="!$":
		if getvalue(int(message.author.id), "privacy")==True:
			await client.send_message(message.channel, "Sorry, that user has wallet privacy mode enabled.")
		else:
			osrs=getvalue(int(message.author.id),"07")
			rs3=getvalue(int(message.author.id),"rs3")
			usd=getvalue(int(message.author.id),"usd")
			tickets=getvalue(int(message.author.id),"tickets")

			if osrs>=1000000 or rs3>=1000000 or usd>=100.00:
				sidecolor=2693614
			elif osrs>=10000 or rs3>=10000 or usd>=10.00:
				sidecolor=2490163
			else:
				sidecolor=12249599
			osrs=formatfromk(osrs, "osrs")
			rs3=formatfromk(rs3, "rs3")
			usd=formatfromk(usd, "usd")
			if rs3=="0k":
				rs3="0 k"
			if osrs=="0k":
				osrs="0 k"
			embed = discord.Embed(color=sidecolor)
			embed.set_author(name=(str(message.author))[:-5]+"'s Wallet", icon_url=str(message.author.avatar_url))
			embed.add_field(name="07 Balance", value=osrs, inline=True)
			embed.add_field(name="RS3 Balance", value=rs3, inline=True)
			embed.add_field(name="USD Balance", value=usd, inline=True)
			embed.add_field(name="Tickets", value=tickets, inline=True)
			embed.set_footer(text="Wallet checked on: "+str(datetime.datetime.now())[:-7])
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

		if getvalue(int(member.id), "privacy")==True:
			await client.send_message(message.channel, "Sorry, that user has wallet privacy mode enabled.")
		else:
			osrs=getvalue(int(member.id),"07")
			rs3=getvalue(int(member.id),"rs3")
			usd=getvalue(int(member.id),"usd")
			tickets=getvalue(int(member.id),"tickets")

			if osrs>=1000000 or rs3>=1000000 or usd>=100.00:
				sidecolor=2693614
			elif osrs>=10000 or rs3>=10000 or usd>=10.00:
				sidecolor=2490163
			else:
				sidecolor=12249599
			osrs=formatfromk(osrs, "osrs")
			rs3=formatfromk(rs3, "rs3")
			usd=formatfromk(usd, "usd")
			if rs3=="0k":
				rs3="0 k"
			if osrs=="0k":
				osrs="0 k"
			embed = discord.Embed(color=sidecolor)
			embed.set_author(name=(str(member))[:-5]+"'s Wallet", icon_url=str(member.avatar_url))
			embed.add_field(name="07 Balance", value=osrs, inline=True)
			embed.add_field(name="RS3 Balance", value=rs3, inline=True)
			embed.add_field(name="USD Balance", value=usd, inline=True)
			embed.add_field(name="Tickets", value=tickets, inline=True)
			embed.set_footer(text="Wallet checked on: "+str(datetime.datetime.now())[:-7])
			await client.send_message(message.channel, embed=embed)
	##########################################
	elif message.content.startswith("!reset"):
		try:
			if isstaff(message.author.id)=="verified":
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
				elif str(message.content).split(" ")[1]=="usd":
					currency="usd"
					c.execute("UPDATE rsmoney SET usd={} WHERE id={}".format(0, member.id))
				conn.commit()

				await client.send_message(message.channel, str(member)+"'s "+currency+" currency has been reset to 0. RIP")
			else:
				await client.send_message(message.channel, "DON'T TOUCHA MY SPAGHET!")
		except:
			await client.send_message(message.channel, "An **error** occured. Make sure you use `!reset (rs3, 07, or usd) (@user)`")
	###########################################
	elif (message.content).startswith("!update 07") or (message.content).startswith("!update rs3") or (message.content).startswith("!update usd"):
		try:
			if isstaff(message.author.id)=="verified":
				maximum=False
				if (str(message.content).split(" ")[3][-1:]).lower()=="b":
					if int(str(message.content).split(" ")[3][:-1])>100:
						await client.send_message(message.channel, "You can only give up to 100b at one time for...reasons.")
						maximum=True
				elif (str(message.content).split(" ")[1]).lower()=="usd":
					if formatok((str(message.content).split(" ")[3]), "usd")>1000.0:
						await client.send_message(message.channel, "You can only give up to $1000 at one time for...reasons.")
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
			
					await client.send_message(message.channel, str(member)+"'s wallet has been updated.")
				else:
					None
			else:
				await client.send_message(message.channel, "DON'T TOUCHA MY SPAGHET!")
		except:
			await client.send_message(message.channel, "An **error** has occured. Make sure you use `!update (rs3, 07, or usd) (@user) (amount)`.")
	###################################################
	# elif ((message.content).lower()).startswith("!swap"):
	# 	#try:
	# 	amountink=formatok(str(message.content).split(" ")[3], str(message.content).split(" ")[1])
	# 	original=(message.content).split(" ")[1]
	# 	new=(message.content).split(" ")[2]
	# 	enough=True

	# 	if original=="07":
	# 		if amountink<100:
	# 			enough=False
	# 	elif original=="rs3":
	# 		if amountink<1000:
	# 			enough=False
	# 	elif original.lower()=="usd":
	# 		if amountink<1.00:
	# 			enough==False

	# 	if ((message.content).lower()).startswith("!swap 07 rs3"):
	# 		newamount=formatfromk(round((amountink*5.8), 2), "rs3")
	# 	elif ((message.content).lower()).startswith("!swap 07 usd"):
	# 		newamount=formatfromk(round((amountink*0.62), 2), "usd")
	# 	elif ((message.content).lower()).startswith("!swap rs3 07"):
	# 		newamount=formatfromk(round((amountink/7.8), 2), "07")
	# 	elif ((message.content).lower()).startswith("!swap rs3 usd"):
	# 		newamount=formatfromk(round((amountink*0.09), 2), "usd")
	# 	elif ((message.content).lower()).startswith("!swap usd rs3"):
	# 		newamount=formatfromk(round((amountink*8.3333), 2), "rs3")
	# 	elif ((message.content).lower()).startswith("!swap usd 07"):
	# 		newamount=formatfromk(round((amountink*1.47058824), 2), "07")

	# 	current=getvalue(int(message.author.id), original)

	# 	if enough==True:
	# 		if current>=amountink:
	# 			words="For "+str(message.content).split(" ")[3]+" "+original+", you will get "+newamount+" "+new+".\n\nUse `!confirm` to confirm this swap or `!abort` to stop the swap."
	# 			embed = discord.Embed(description=words, color=16777215)
	# 			embed.set_author(name=(str(message.author))[:-5], icon_url=str(message.author.avatar_url))
	# 			await client.send_message(message.channel, embed=embed)
	# 			messagechecked = await client.wait_for_message(timeout=30.0, channel=message.channel, author=message.author)

	# 			if str(messagechecked.content).lower()=="!confirm":
	# 				update_money(message.author.id, (amountink*-1), original)
	# 				update_money(message.author.id, formatok(newamount, new), new)
	# 				await client.send_message(message.channel, "The money has been swapped.")
	# 			elif str(messagechecked.content).lower()=="!abort":
	# 				await client.send_message(message.channel, "The swap has been aborted.")
	# 			else:
	# 				await client.send_message(message.channel, "An **error** has occured. Swap has been aborted.")
	# 		else:
	# 			await client.send_message(message.channel, "You don't have enough money to swap that amount!")
	# 	else:
	# 		await client.send_message(message.channel, "The minimum amount to swap is `100k 07`, `1m rs3`, and `$1 USD`.")
	# 	#except:
	# 	#	await client.send_message(message.channel, "An **error** has occured. Make sure you use `!swap (RS3 or 07) (amount you want to swap)`.")
	# ############################################
	# elif ((message.content).lower()).startswith("!rates"):
	# 	embed = discord.Embed(description="\n7.8M RS3 = 1M 07  | 1M 07 = 5.8M RS3\n"+
	# 										"0.68 USD = 1M 07  | 1M 07 = 0.62 USD\n"+
	# 										"0.12 USD = 1M rs3  | 1M rs3 = 0.09 USD", color=16771099)
	# 	embed.set_author(name="Crypto Land Swapping Rates", icon_url=str(message.server.icon_url))
	# 	await client.send_message(message.channel, embed=embed)
	############################################
	elif message.content.startswith("!help") or message.content.startswith("!commands"):
		embed = discord.Embed(description=  "\n `!colorpicker` - Shows a random color\n" +
											#"\n `!start unscramble` - Starts a game where you unscramble a word\n" +
											#"\n `!start hangman` - Starts a game of hangman\n" +
											#"\n `!random (SIZE)` - Starts a game where you guess a number between 1 and the given size\n" +
											"\n `!poll (QUESTION)` - Starts a Yes/No poll with the given question\n" +
											"\n `!w`, `!wallet`, or `!$` - Checks your own wallet\n" +
											"\n `!w (@USER)`, `!wallet (@USER)`, or `!$ (@USER)` - Checks that user's wallet\n" +
											"\n `!flower (AMOUNT) (hot, cold, red, orange, yellow, green, blue, or purple)` - Hot or cold gives x2, specific color gives x6\n" +
											"\n `!45x1.5 (rs3, 07, or usd) (BET)` - Must roll above 45, x1.5 payout\n" +
											"\n `!50x1.9 (rs3, 07, or usd) (BET)` - Must roll above 50, x1.9 payout\n" +
											"\n `!54x2 (rs3, 07, or usd) (BET)` - Must roll above 54, x2 payout\n" +
											"\n `!75x3 (rs3, 07, or usd) (BET)` - Must roll above 75, x3 payout\n" +
											"\n `!90x7 (rs3, 07, or usd) (BET)` - Must roll above 90, x7 payout\n" +
											"\n `!95x10 (rs3, 07, or usd) (BET)` - Must roll above 95, x10 payout\n" +
											"\n `!dd (rs3, 07, or usd) (BET)` - Hosts a dice duel of the given amount\n" +
											#"\n `!swap (rs3 or 07) (AMOUNT)` - Swaps that amount of gold to the other game" +
											#"\n `!rates` - Shows the swapping rates between currencies" +
											#"\n `!cashin (rs3 or 07) (AMOUNT)` - Notifes a cashier that you want to cash in that amount" +
											#"\n `!cashout (rs3 or 07) (AMOUNT)` - Notifes a cashier that you want to cash out that amount"
											"\n `!transfer (rs3, 07, or usd) (@USER) (AMOUNT)` - Transfers that amount from your wallet to the user's wallet\n"+
											"\n `!wager`, or `!total bet` or `!tb` - Shows your total amount bet for rs3 and 07\n", color=16771099)

		embed.set_author(name="Crypto Land Bot Commands", icon_url=str(message.server.icon_url))
		await client.send_message(message.author, embed=embed)
		await client.send_message(message.channel, "The commands have been sent to your private messages.")
	###################################
	elif ((message.content).lower()).startswith("!cashin") or ((message.content).lower()).startswith("!cashout"):
		#try:
		enough=True
		cashing=formatok(str(message.content).split(" ")[2], str(message.content).split(" ")[1])
	
		if message.content.startswith("!cashout"):
			way="out"
			if str(message.content).split(" ")[1]=="rs3":
				if cashing<10000:
					await client.send_message(message.channel, "<@"+str(message.author.id)+">, You must cash out atleast **10m** rs3.")
					enough=False
			elif str(message.content).split(" ")[1]=="07":
				if cashing<2000:
					await client.send_message(message.channel, "<@"+str(message.author.id)+">, You must cash out atleast **2m** 07.")
					enough=False
			elif str(message.content).split(" ")[1]=="usd":
				if cashing<1.00:
					await client.send_message(message.channel, "<@"+str(message.author.id)+">, You must cash out atleast **$1** USD.")
					enough=False

				current=getvalue(int(message.author.id), str(message.content).split(" ")[1])

			if cashing>current:
				await client.send_message(message.channel, "<@"+str(message.author.id)+">, You don't have that much money to cash out!")
				enough=False
				
		else:
			way="in"
			if str(message.content).split(" ")[1]=="rs3":
				if cashing<5000:
					await client.send_message(message.channel, "<@"+str(message.author.id)+">, You must cash in atleast **5m** rs3.")
					enough=False
			elif str(message.content).split(" ")[1]=="07":
				if cashing<1000:
					await client.send_message(message.channel, "<@"+str(message.author.id)+">, You must cash in atleast **1m** 07.")
					enough=False
			elif str(message.content).split(" ")[1]=="usd":
				if cashing<1.00:
					await client.send_message(message.channel, "<@"+str(message.author.id)+">, You must cash out atleast **$1** USD.")
					enough=False

		if (str(message.content).split(" ")[1]).lower()=="rs3" or (str(message.content).split(" ")[1]).lower()=="07" or (str(message.content).split(" ")[1]).lower()=="usd":
			if enough==True:
				await client.send_message(message.channel, "Remember that fake cash-ins are kickable.")
				await client.send_message(message.server.get_channel("459923177376579596"), "<@&459899438643675136>, <@"+str(message.author.id)+"> wants to cash "+way+" **"+str(message.content).split(" ")[2]+"** "+str(message.content).split(" ")[1]+".")
				await client.send_message(message.channel, "A message has been sent to a cashier. Your request will be processed and you will be messaged soon. :D")
			else:
				None
		else:
			await client.send_message(message.channel, "An **error** has occured. Make sure you use `"+str(message.content).split(" ")[0]+" (rs3, 07, or usd) (Amount you want to cash in/out)`.")
		#except:
		#	await client.send_message(message.channel, "An **error** has occured. Make sure you use `"+str(message.content).split(" ")[0]+" (rs3, 07, or usd) (Amount you want to cash in/out)`.")

	###########################3
	elif ((message.content).lower()).startswith("!transfer rs3") or ((message.content).lower()).startswith("!transfer 07") or ((message.content).lower()).startswith("!transfer usd"):
		#try:
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

		elif str(message.content).split(" ")[1]=="usd":
			if transfered<0.01:
				await client.send_message(message.channel, "You must transfer at least **1 cent** USD.")
				enough=False

		currency=str(message.content).split(" ")[1]
		current=getvalue(int(message.author.id),currency)

		if enough==True:
			if current>=transfered:
				try:
					int(str(message.content).split(" ")[2][2:3])
					member=message.server.get_member(str(message.content).split(" ")[2][2:-1])
				except:
					member=message.server.get_member(str(message.content).split(" ")[2][3:-1])
				
				taker=getvalue(int(member.id),currency)
		
				if currency=="rs3":
					c.execute("UPDATE rsmoney SET rs3={} WHERE id={}".format(current-transfered, message.author.id))
					c.execute("UPDATE rsmoney SET rs3={} WHERE id={}".format(taker+transfered, member.id))
				elif currency=="07":
					c.execute("UPDATE rsmoney SET osrs={} WHERE id={}".format(current-transfered, message.author.id))
					c.execute("UPDATE rsmoney SET osrs={} WHERE id={}".format(taker+transfered, member.id))
				elif currency.lower()=="usd":
					c.execute("UPDATE rsmoney SET usd={} WHERE id={}".format(current-transfered, message.author.id))
					c.execute("UPDATE rsmoney SET usd={} WHERE id={}".format(taker+transfered, member.id))
				conn.commit()

				await client.send_message(message.channel, "<@"+str(message.author.id)+"> has transfered "+str(formatfromk(transfered, currency))+" "+currency+" to <@"+str(member.id)+">'s wallet.")
			else:
				await client.send_message(message.channel, "<@"+str(message.author.id)+">, You don't have enough money to transfer that amount!")
		else:
			None
		#except:
		#	await client.send_message(message.channel, "An **error** has occured. Make sure you use `!transfer (rs3, 07, or usd) (@user) (Amount you want to give)`.")
	###################################
	elif message.content.startswith("!total wallet"):
		c.execute("SELECT SUM(rs3) FROM rsmoney")
		rs3=formatfromk(int(str(c.fetchall())[2:-3]), "rs3")
		c.execute("SELECT SUM(osrs) FROM rsmoney")
		osrs=formatfromk(int(str(c.fetchall())[2:-3]), "osrs")
		c.execute("SELECT SUM(usd) FROM rsmoney")
		usd=formatfromk(float(str(c.fetchall())[2:-3]), "usd")

		embed = discord.Embed(color=16766463)
		embed.set_author(name="Everyone's Wallet", icon_url="https://images.ecosia.org/xSQHmzfpe-a49ZZX3B8q8kX9ycs=/0x390/smart/https%3A%2F%2Fjustmeint.files.wordpress.com%2F2012%2F08%2Fearth-small.jpg")
		embed.add_field(name="07 Balance", value=osrs, inline=True)
		embed.add_field(name="RS3 Balance", value=rs3, inline=True)
		embed.add_field(name="USD Balance", value=usd, inline=True)
		embed.set_footer(text="Total Wallet checked on: "+str(datetime.datetime.now())[:-7])
		await client.send_message(message.channel, embed=embed)
	################################

# def starts_w(content, starts):
# 		for s in starts:
# 			if content.startswith(s):
# 				return True
# 			else:
# 				return False
	
	# elif starts_w(message.content):
	elif message.content.startswith("!54") or message.content.startswith("!50") or message.content.startswith("!75") or message.content.startswith("!45") or message.content.startswith("!90") or message.content.startswith("!95"):
		try:
			game=str(message.content).split(" ")[1]
			bet=formatok(str(message.content).split(" ")[2], game)
			current=getvalue(message.author.id, game)

			if isenough(bet, game)[0]:
				if message.content.startswith("!54x2") or message.content.startswith("!54"):
					title="54x2"
					odds=56
					multiplier=2
				elif message.content.startswith("!75x3") or message.content.startswith("!75"):
					title="75x3"
					odds=77
					multiplier=3
				elif message.content.startswith("!50x2") or message.content.startswith("!50"):
					title="50x2"
					odds=52
					multiplier=1.9
				elif message.content.startswith("!45x1.5") or message.content.startswith("!45"):
					title="45x1.5"
					odds=47
					multiplier=1.5
				elif message.content.startswith("!90x7") or message.content.startswith("!90"):
					title="90x7"
					odds=92
					multiplier=7
				elif message.content.startswith("!95x10") or message.content.startswith("!95"):
					title="95x10"
					odds=97
					multiplier=10

				if current>=bet:
					roll=random.randint(1,100)

					if roll in range(1,odds):
						win=False
						sidecolor=16718121
						gains=bet*-1
						winnings=bet*-1
					else:
						win=True
						sidecolor=3997475
						gains=(bet*multiplier)-(bet)
						winnings=(bet*multiplier)

					if isinstance(winnings, float):
						if (winnings).is_integer():
							winnings=int(winnings)

					winnings=formatfromk(winnings, game)
					update_money(int(message.author.id), gains, game)

					if win==False:
						words="Rolled **"+str(roll)+"** out of **100**. You lost **"+str(formatfromk(bet, game))+"** "+str(game)+"."
					elif win==True:
						words="Rolled **"+str(roll)+"** out of **100**. You won **"+str(winnings)+"** "+str(game)+"."	

					embed = discord.Embed(color=sidecolor)
					embed.set_author(name=str(message.author), icon_url=str(message.author.avatar_url))
					embed.add_field(name=title, value=words, inline=True)
					embed.set_footer(text="Gambled on: "+str(datetime.datetime.now())[:-7])
					await client.send_message(message.channel, embed=embed)

					ticketbets(message.author.id, bet, game)

				else:
					await client.send_message(message.channel, "<@"+str(message.author.id)+">, you don't have that much gold!")
			else:
				await client.send_message(message.channel, (isenough(bet, game))[1])
		except:
			await client.send_message(message.channel, "An **error** has occured. Make sure you use `!(50, 54, or 75) (rs3 or 07) (BET)`.")
	#############################
	elif ((message.content).lower()).startswith("!wager") or ((message.content).lower()).startswith("!total bet") or ((message.content).lower()).startswith("!tb"):
		rs3total=getvalue(message.author.id, "rs3total")
		osrstotal=getvalue(message.author.id, "osrstotal")
		usdtotal=getvalue(message.author.id, "usdtotal")

		osrs=formatfromk(osrstotal, "osrs")
		rs3=formatfromk(rs3total, "rs3")
		usd=formatfromk(usdtotal, "usd")

		embed = discord.Embed(color=16766463)
		embed.set_author(name=(str(message.author))[:-5]+"'s Total Bets", icon_url=str(message.author.avatar_url))
		embed.add_field(name="07 Total Bets", value=osrs, inline=True)
		embed.add_field(name="RS3 Total Bets", value=rs3, inline=True)
		embed.add_field(name="USD Total Bets", value=usd, inline=True)
		embed.set_footer(text="Total Bets checked on: "+str(datetime.datetime.now())[:-7])
		await client.send_message(message.channel, embed=embed)
	#############################
	elif message.content.startswith("!flower"):
		try:
			currency=(message.content).split(" ")[1]
			bet=formatok((message.content).split(" ")[2], currency)
			current=getvalue(int(message.author.id), currency)
			commission=0.05
			index=random.randint(0,5)
			flower=flowers[index]
			sidecolor=sidecolors[index]

			if isenough(bet, currency)[0]:	
				if current>=bet:
					win=False
					if (message.content).split(" ")[3]=="hot":
						if flower=="Red" or flower=="Orange" or flower=="Yellow":
							multiplier=2
							win=True
						else:
							multiplier=0
					elif (message.content).split(" ")[3]=="cold":
						if flower=="Blue" or flower=="Pastel" or flower=="Purple":
							multiplier=2
							win=True
						else:
							multiplier=0
					elif ((message.content).split(" ")[3]).title() in flowers:
						if flower==((message.content).split(" ")[3]).title():
							multiplier=6
							win=True
						else:
							multiplier=0


					winnings=(bet*multiplier)-(commission*bet*multiplier)
					if isinstance(winnings, float):
						if (winnings).is_integer():
							winnings=int(winnings)
					winnings=formatfromk(winnings, currency)

					if win==True:
						words=("Congratulations! The color of the flower was `"+flower+"`. "+str(message.author)+" won `"+winnings+"` "+currency+".")
						update_money(int(message.author.id), (bet)-(bet*commission*multiplier), currency)
					else:
						words=("Sorry, the color the flower was `"+flower+"`. "+str(message.author)+" lost `"+formatfromk(bet, currency)+"` "+currency+".")
						update_money(int(message.author.id), bet*-1, currency)

					embed = discord.Embed(description=words, color=sidecolor)
					embed.set_author(name=(str(message.author))[:-5]+"'s Gamble", icon_url=str(message.author.avatar_url))
					embed.set_footer(text="Gambled on: "+str(datetime.datetime.now())[:-7])
					await client.send_message(message.channel, embed=embed)	

					ticketbets(message.author.id, bet, currency)

				else:
					await client.send_message(message.channel, "<@"+str(message.author.id)+">, You don't have that much gold!")
			else:
				await client.send_message(message.channel, (isenough(bet, currency))[1])
		except:
		 	await client.send_message(message.channel, "An **error** has occured. Make sure you use `!flower (rs3, 07, or usd) (Amount) (hot, cold, red, orange, yellow, green, blue, or purple)`.")
	#############################
	elif message.content.startswith("!dd"):
		#try:
		if duel==True:
			await client.send_message(message.channel, "There is a dice duel already going on. Please wait until that one finishes.")
		else:
			currency=(message.content).split(" ")[1]
			bet=formatok((message.content).split(" ")[2], currency)
			current=getvalue(int(message.author.id), currency)

			if isenough(bet, currency)[0]:
				update_money(message.author.id, current-bet, currency)
				await client.send_message(message.channel, "<@"+str(message.author.id)+"> wants to duel for `"+formatfromk(bet, currency)+" "+currency+"`. Use `!call` to accept the duel.")
				while True:
					call = await client.wait_for_message(timeout=60, channel=message.channel, content="!call")
					if call is None:
						await client.send_message(message.channel, "<@"+str(message.author.id)+">'s duel request has timed out.")
						update_money(message.author.id, current, currency)
						break
					caller=call.author
					current2=getvalue(int(caller.id), currency)
					if str(caller.id)==str(message.author.id):
						await client.send_message(message.channel, "As exciting as it may sound, you cannot duel yourself ._.")
						continue
					if current2<bet:
						await client.send_message(message.channel, "You don't have enough money to call that duel.")
						continue
					else:
						update_money(caller.id, current2-bet, currency)
						duel=True
						break

				if duel==True:
					await client.send_message(message.channel, "Duel Initiated. Use `!roll` to roll.")
					gamblerroll=random.randint(2,12)
					callerroll=random.randint(2,12)
					roll = await client.wait_for_message(timeout=30, channel=message.channel, content="!roll")
					if roll is None:
						await client.send_message(message.channel, "<@"+str(message.author.id)+"> rolled a `"+str(gamblerroll)+"` :game_die: ")
						second=caller
					if str(roll.author.id)==str(message.author.id):
						await client.send_message(message.channel, "<@"+str(message.author.id)+"> rolled a `"+str(gamblerroll)+"` :game_die: ")
						second=caller
					elif str(roll.author.id)==str(caller.id):
						await client.send_message(message.channel, "<@"+str(caller.id)+"> rolled a `"+str(callerroll)+"` :game_die: ")
						second=message.author

					roll = await client.wait_for_message(timeout=30, channel=message.channel, author=second, content="!roll")
					if roll is None:
						await client.send_message(message.channel, "<@"+str(caller.id)+"> rolled a `"+str(callerroll)+"` :game_die: ")
					if str(roll.author.id)==str(message.author.id):
						await client.send_message(message.channel, "<@"+str(message.author.id)+"> rolled a `"+str(gamblerroll)+"` :game_die: ")
					elif str(roll.author.id)==str(caller.id):
						await client.send_message(message.channel, "<@"+str(caller.id)+"> rolled a `"+str(callerroll)+"` :game_die: ")

					embed = discord.Embed(color=16766463)
					embed.set_author(name="Dice Duel", icon_url=str(message.server.icon_url))
					embed.add_field(name=str(message.author)+" Roll", value=str(gamblerroll), inline=True)
					embed.add_field(name=str(caller)+" Roll", value=str(callerroll), inline=True)
					embed.set_footer(text="Dueled On: "+str(datetime.datetime.now())[:-7])
					await client.send_message(message.channel, embed=embed)

					if gamblerroll==callerroll:
						await client.send_message(message.channel, "Tie. Money Back.")
						update_money(message.author.id, current, currency)
						update_money(caller.id, current2, currency)
					elif gamblerroll>callerroll:
						await client.send_message(message.channel, "<@"+str(message.author.id)+"> rolled higher and won `"+formatfromk(bet, currency)+" "+currency+"`!")
						update_money(int(message.author.id), bet+current, currency)
					elif callerroll>gamblerroll:
						await client.send_message(message.channel, "<@"+str(caller.id)+"> rolled higher and won `"+formatfromk(bet, currency)+" "+currency+"`!")
						update_money(int(caller.id), bet+current, currency)

					ticketbets(message.author.id, bet, currency)
					ticketbets(caller.id, bet, currency)

					duel=False
				else:
					None
			else:
				await client.send_message(message.channel, (isenough(bet, currency))[1])
		#except:
	################################
	elif message.content=="!privacy on":
		c.execute("UPDATE rsmoney SET privacy=True WHERE id={}".format(message.author.id))
		await client.send_message(message.channel, "<@"+str(message.author.id)+">'s wallet privacy is now enabled.")
	#################################
	elif message.content=="!privacy off":
		c.execute("UPDATE rsmoney SET privacy=False WHERE id={}".format(message.author.id))
		await client.send_message(message.channel, "<@"+str(message.author.id)+">'s wallet privacy is now disabled.")

#client.loop.create_task(my_background_task())
Bot_Token = os.environ['TOKEN']
client.run(str(Bot_Token))
#https://discordapp.com/oauth2/authorize?client_id=478960758114484224&scope=bot&permissions=0

#flowers
#multiple dice duel
#duel takes money


