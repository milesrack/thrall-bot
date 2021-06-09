#!/usr/bin/python3
import asyncio
import discord
from discord.ext import commands,tasks
import os
import subprocess
import sys
import signal
import requests
import urllib
from bs4 import BeautifulSoup
import youtube_dl
import socket
from pythonping import ping
import random
import base64
import json
import codecs
import datetime
from math import *
from gtts import gTTS

# Suppress noise about console usage from errors
youtube_dl.utils.bug_reports_message = lambda: ''
ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0' # bind to ipv4 since ipv6 addresses cause issues sometimes
}
ffmpeg_options = {'options': '-vn'}
ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

path = os.path.dirname(__file__)
with open(os.path.join(path,'discord_token.txt'),'r') as discord_token: discord_api_key = discord_token.readline()
with open(os.path.join(path,'ip_geo_token.txt'),'r') as ip_geo_token: ip_geo_api_key = ip_geo_token.readline()
intents = discord.Intents.all()
thrall = commands.Bot(command_prefix='!', intents=intents)
master_id = 762101678752661505 # Replace with your discord ID

class YTDLSource(discord.PCMVolumeTransformer):
	def __init__(self, source, *, data, volume=0.5):
		super().__init__(source, volume)
		self.data = data
		self.title = data.get('title')
		self.url = data.get('url')

	@classmethod
	async def from_url(cls, url, *, loop=None, stream=False):
		loop = loop or asyncio.get_event_loop()
		data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))
		if 'entries' in data:
			# take first item from a playlist
			data = data['entries'][0]
		filename = data['url'] if stream else ytdl.prepare_filename(data)
		return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)

class Music(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

	@commands.command(description='Joins a voice channel')
	async def join(self, ctx):
		if ctx.author.voice is None or ctx.author.voice.channel is None:
			return await ctx.send('You need to be in a voice channel to use this command!')

		voice_channel = ctx.author.voice.channel
		if ctx.voice_client is None:
			vc = await voice_channel.connect()
		else:
			await ctx.voice_client.move_to(voice_channel)
			vc = ctx.voice_client

	@commands.command(description='Plays music')
	async def play(self, ctx, *, url):
		player = await YTDLSource.from_url(url, loop=self.bot.loop, stream=True)
		ctx.voice_client.play(player, after=lambda e: print('Player error: %s' % e) if e else None)
		await ctx.send(f'Now playing: **{player.title}**')
    
	@commands.command(description='Stops the music and disconnects the bot')
	async def leave(self, ctx):
		await ctx.voice_client.disconnect()

	@play.before_invoke
	async def ensure_voice(self, ctx):
		if ctx.voice_client is None:
			if ctx.author.voice:
				await ctx.author.voice.channel.connect()
			else:
				await ctx.send('You are not connected to a voice channel!')
				raise commands.CommandError('Author not connected to a voice channel!')
		elif ctx.voice_client.is_playing():
			ctx.voice_client.stop()

class Misc(commands.Cog):
	@commands.command(description='Echoes back a string of text')
	async def echo(self, ctx, *args):
		message = ' '.join(args)
		await ctx.send(f'{message}')
	
	@commands.command(description='Spells out a string using regional indicators')
	async def say(self, ctx, *args):
		number_dict = {
		'0':'zero',
		'1':'one',
		'2':'two',
		'3':'three',
		'4':'four',
		'5':'five',
		'6':'six',
		'7':'seven',
		'8':'eight',
		'9':'nine'
		}
		new_words = []
		for word in args:
			new_word = ''
			for letter in word:
				if letter.lower() in 'abcdefghijklmnopqrstuvwxyz':
					letter = letter.lower()
					new_word += f':regional_indicator_{letter}:'
				elif letter in '0123456789':
					new_word += f':{number_dict[letter]}:'
			new_words.append(new_word)
		message = '\t\t'.join(new_words)
		await ctx.send(message)
	
	@commands.command(description='Speaks a string of text')
	async def speak(self, ctx, *args):
		message = ' '.join(args)
		if len(message) == 0:
			message = 'You fucking idiot. You did not specify a message for me to speak.'
		filename = os.path.join(path,f'output-{datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}.mp3')
		tts = gTTS(message, 'com')
		tts.save(filename)
		await ctx.send(file=discord.File(filename))
		os.remove(filename)
	
	@commands.command(description='Tells a random joke')
	async def joke(self, ctx):
		jokes = ['I would tell you a UDP joke, but you might not get it.','Hello, would you like to hear a TCP joke?\nYes, I\'d like to hear a TCP joke.\nOK, I\'ll tell you a TCP joke.\nOK, I\'ll hear a TCP joke.\nAre you ready to hear a TCP joke?\nYes, I am ready to hear a TCP joke.\nOK, I\'m about to send the TCP joke. It will last 10 seconds, it has two characters, it does not have a setting, it ends with a punchline.\nOK, I\'m ready to hear the TCP joke that will last 10 seconds, has two characters, does not have a setting and will end with a punchline.\nI\'m sorry, your connection has timed out... ...Hello, would you like to hear a TCP joke?','I like my women like my kernels, about 6 years old and stable','Have you heard there\'s a new disease you can get from using Linux? It\'s terminal!','A Linux user, a vegan, and an atheist walk into a bar.... I know because they told everybody there','Daddy, what are clouds made of? Linux servers, mostly.','Why do Assembly programmers have so much free time at school? They can\'t have any classes.','What did the programmer’s suicide note say? "Goodbye world"','Why did the programmer need glasses? He couldn’t C#.','Why did the Programmer quit his job? ["Because", "he", "didnt", "get", "Arrays"]','A programmer was arrested for writing unreadable code, He refused to comment.','A programmer walks into a bar...\nHe orders 1.000000119 root beers.\nThe bartender says, "I\'m gonna have to charge you extra, that’s a root beer float."\nThe programmer says, "Well in that case make it a double."','Why can\'t Communists be programmers? Because there is a hierarchy of classes, inheritance, and private properties.','`sudo rm -fr /` removes all the French files from your Linux machine!']
		await ctx.send(random.choice(jokes))
	
	@commands.command(description='Fetches an image from https://thispersondoesnotexist.com')
	async def person(self, ctx):
		await ctx.send(f'Fetching image from https://thispersondoesnotexist.com/image...')
		try:
			r = requests.get('https://thispersondoesnotexist.com/image')
			image = r.content
			imgpath = os.path.join(path,'out.jpg')
			with open (imgpath,'wb') as img:
				img.write(image)
			await ctx.send(file=discord.File(imgpath))
			os.remove(imgpath)
		except:
			await ctx.send(f'Failed to get an image from https://thispersondoesnotexist.com')
	@commands.command(description='Searches for images on DuckDuckGo')
	async def img(self,ctx, *args):
		message = ' '.join(args)
		headers = {
		'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:88.0) Gecko/20100101 Firefox/88.0',
		'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
		'Accept-Encoding': 'gzip, deflate, br',
		'Accept-Language': 'en-US,en;q=0.5',
		'Connection': 'keep-alive',
		}
		await ctx.send(f'Searching for images of **{message}**...')
		r = requests.get(f'https://www.google.com/search?hl=en&tbm=isch&q={urllib.parse.quote_plus(message)}',headers=headers)
		soup = BeautifulSoup(r.content,'html.parser')
		images = []
		for item in soup.find_all('img', {'class':'rg_i Q4LuWd'}):
			try:
				if len(images) < 5:
					images.append(item['data-src'])
			except:
				continue
		if len(images) == 0:
			await ctx.send(f'No results found for **{message}**')
		for i,image in enumerate(images):
			r = requests.get(image)
			safe_chars = (' ','.','_')
			imgpath = os.path.join(path,f'{"".join(char for char in message if char.isalnum() or char in safe_chars).rstrip()}_{i}.jpg')
			with open(imgpath,'wb') as img:
				img.write(r.content)
			await ctx.send(file=discord.File(imgpath))
			os.remove(imgpath)
		#await ctx.send('**Google Image search failed!**')

class Cryptography(commands.Cog):
	@commands.command(description='Encodes/decodes a string using rot13')
	async def rot13(self, ctx, *args):
		string = ' '.join(args)
		await ctx.send(f'```\n{codecs.encode(string,"rot_13")}\n```')

	@commands.command(description='Converts a number or string into binary')
	async def binary(self, ctx, *args):
		string = ' '.join(args)
		new_string = ''
		try:
			number = int(string)
			new_string += format(number,'08b')
		except:
			for char in string:
				new_string += format(ord(char),'08b')
		finally:
			await ctx.send(f'```\n{new_string}\n```')

	@commands.command(description='Converts binary back into a number or string')
	async def from_binary(self, ctx, string):
		new_string = ''
		number = int(string,2)
		for i in range(int(len(string)/8)):
			new_string += chr(int(string[i*8:i*8+8],2))
		await ctx.send(f'```\nDecimal: {number}\nASCII: {new_string}\n```')

	@commands.command(name='hex',description='Converts a number or string into hexadecimal')
	async def _hex(self, ctx, *args):
		string = ' '.join(args)
		try:
			await ctx.send(f'```\n{hex(int(string))}\n```')
		except:
			await ctx.send(f'```\n0x{string.encode("utf-8").hex()}\n```')

	@commands.command(description='Converts hexadecimal back into a number or string')
	async def from_hex(self, ctx, string):
		try:
			dec = int(string,16)
			binary_str = codecs.decode(string.lower().strip('0x'), 'hex')
			_ascii = str(binary_str,'utf-8')
		except (TypeError,ValueError):
			await ctx.send(f'**{string}** is not a valid hexadecimal string!')
		else:
			await ctx.send(f'```\nDecimal: {dec}\nASCII: {_ascii}\n```')

	@commands.command(name='base64',description='Base64 encodes a string of text')
	async def _base64(self, ctx, *args):
		string = ' '.join(args)
		bytes_string = bytes(string,'utf-8')
		await ctx.send(f'```\n{base64.b64encode(bytes_string).decode("utf-8")}\n```')

	@commands.command(description='Base64 decodes a string of text')
	async def from_base64(self, ctx, string):
		try:
			await ctx.send(f'```\n{base64.b64decode(string).decode("utf-8")}\n```')
		except:
			await ctx.send(f'**{string}** is not a valid base64 string!')

class Networking(commands.Cog):
	def validateip(self, ctx, ip):
		global ip_valid
		ip_valid = False
		octets = ip.split('.')
		for i,octet in enumerate(octets):
			try:
				if int(octet) == 0 and octet != '0':
					#await ctx.send(f'**{ip}** is not a valid IP address!')
					return
				octet = int(octet)
				valid_range = 0 <= octet <= 255
				if i == 0 and octet == 0:
					#await ctx.send(f'**{ip}** is not a valid IP address!')
					return
			except ValueError:
				#await ctx.send(f'**{ip}** is not a valid IP address!')
				return
			if valid_range:
				pass
			else:
				#await ctx.send(f'**{ip}** is not a valid IP address!')
				return
		if len(octets) == 4:
				pass
		else:
			#await ctx.send(f'**{ip}** is not a valid IP address!')
			return
		if octets[0] == '10' or octets[0] == '127' or '.'.join(octets[0:2]) == '192.168' or (octets[0] == '172' and 16 <= int(octets[1]) <= 31):
			#await ctx.send(f'**{ip}** is a private IP address!')
			return
		ip_valid = True
		return

	def validateport(self, ctx,port):
		global port_valid
		port_valid = False
		try:
			if port[0] == '0':
				#await ctx.send(f'**{port}** is not a valid port!')
				return		
			port = int(port)
			if port > 0 and port <= 65535:
				pass
			else:
				#await ctx.send(f'**{port}** is not a valid port!')
				return
		except ValueError:
			#await ctx.send(f'**{port}** is not a valid port!')
			return
		port_valid = True
		return

	@commands.command(description='Makes a GET request to a URL and returns the response in an HTML file')
	async def curl(self, ctx, url):
		try:
			r = requests.get(url)
		except:
			await ctx.send(f'Could not make a GET requests to **{url}**')
		else:
			data = r.text
			pretty_data = BeautifulSoup(data, 'html.parser').prettify()
			outfile = os.path.join(path,'out.html')
			with open(outfile,'wb') as out:
				out.write(bytes(pretty_data,'utf-8'))
			await ctx.send(file=discord.File(outfile))
		os.remove(outfile)

	@commands.command(description='Checks if a given TCP port is open on a host')
	async def port(self, ctx, ip, port):
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		Networking.validateip(self,ctx,ip)
		Networking.validateport(self,ctx,port)
		if ip_valid and port_valid:
			try:
				s.settimeout(10)
				s.connect((ip,int(port)))
				s.close()
			except:
				await ctx.send(f'Port {port} is **closed** on {ip}')
			else:
				await ctx.send(f'Port {port} is **open** on {ip}')
		elif not ip_valid:
			await ctx.send(f'**{ip}** is not a valid IP address')
		elif not port_valid:
			await ctx.send(f'**{port}** is not a valid port')

	@commands.command(description='Checks the top 1000 TCP ports on a host')
	async def ports(self, ctx, ip):
		Networking.validateip(self,ctx,ip)
		if ip_valid:
			ports = ['1','3','4','6','7','9','13','17','19','20','21','22','23','24','25','26','30','32','33','37','42','43','49','53','70','79','80','81','82','83','84','85','88','89','90','99','100','106','109','110','111','113','119','125','135','139','143','144','146','161','163','179','199','211','212','222','254','255','256','259','264','280','301','306','311','340','366','389','406','407','416','417','425','427','443','444','445','458','464','465','481','497','500','512','513','514','515','524','541','543','544','545','548','554','555','563','587','593','616','617','625','631','636','646','648','666','667','668','683','687','691','700','705','711','714','720','722','726','749','765','777','783','787','800','801','808','843','873','880','888','898','900','901','902','903','911','912','981','987','990','992','993','995','999','1000','1001','1002','1007','1009','1010','1011','1021','1022','1023','1024','1025','1026','1027','1028','1029','1030','1031','1032','1033','1034','1035','1036','1037','1038','1039','1040','1041','1042','1043','1044','1045','1046','1047','1048','1049','1050','1051','1052','1053','1054','1055','1056','1057','1058','1059','1060','1061','1062','1063','1064','1065','1066','1067','1068','1069','1070','1071','1072','1073','1074','1075','1076','1077','1078','1079','1080','1081','1082','1083','1084','1085','1086','1087','1088','1089','1090','1091','1092','1093','1094','1095','1096','1097','1098','1099','1100','1102','1104','1105','1106','1107','1108','1110','1111','1112','1113','1114','1117','1119','1121','1122','1123','1124','1126','1130','1131','1132','1137','1138','1141','1145','1147','1148','1149','1151','1152','1154','1163','1164','1165','1166','1169','1174','1175','1183','1185','1186','1187','1192','1198','1199','1201','1213','1216','1217','1218','1233','1234','1236','1244','1247','1248','1259','1271','1272','1277','1287','1296','1300','1301','1309','1310','1311','1322','1328','1334','1352','1417','1433','1434','1443','1455','1461','1494','1500','1501','1503','1521','1524','1533','1556','1580','1583','1594','1600','1641','1658','1666','1687','1688','1700','1717','1718','1719','1720','1721','1723','1755','1761','1782','1783','1801','1805','1812','1839','1840','1862','1863','1864','1875','1900','1914','1935','1947','1971','1972','1974','1984','1998','1999','2000','2001','2002','2003','2004','2005','2006','2007','2008','2009','2010','2013','2020','2021','2022','2030','2033','2034','2035','2038','2040','2041','2042','2043','2045','2046','2047','2048','2049','2065','2068','2099','2100','2103','2105','2106','2107','2111','2119','2121','2126','2135','2144','2160','2161','2170','2179','2190','2191','2196','2200','2222','2251','2260','2288','2301','2323','2366','2381','2382','2383','2393','2394','2399','2401','2492','2500','2522','2525','2557','2601','2602','2604','2605','2607','2608','2638','2701','2702','2710','2717','2718','2725','2800','2809','2811','2869','2875','2909','2910','2920','2967','2968','2998','3000','3001','3003','3005','3006','3007','3011','3013','3017','3030','3031','3052','3071','3077','3128','3168','3211','3221','3260','3261','3268','3269','3283','3300','3301','3306','3322','3323','3324','3325','3333','3351','3367','3369','3370','3371','3372','3389','3390','3404','3476','3493','3517','3527','3546','3551','3580','3659','3689','3690','3703','3737','3766','3784','3800','3801','3809','3814','3826','3827','3828','3851','3869','3871','3878','3880','3889','3905','3914','3918','3920','3945','3971','3986','3995','3998','4000','4001','4002','4003','4004','4005','4006','4045','4111','4125','4126','4129','4224','4242','4279','4321','4343','4443','4444','4445','4446','4449','4550','4567','4662','4848','4899','4900','4998','5000','5001','5002','5003','5004','5009','5030','5033','5050','5051','5054','5060','5061','5080','5087','5100','5101','5102','5120','5190','5200','5214','5221','5222','5225','5226','5269','5280','5298','5357','5405','5414','5431','5432','5440','5500','5510','5544','5550','5555','5560','5566','5631','5633','5666','5678','5679','5718','5730','5800','5801','5802','5810','5811','5815','5822','5825','5850','5859','5862','5877','5900','5901','5902','5903','5904','5906','5907','5910','5911','5915','5922','5925','5950','5952','5959','5960','5961','5962','5963','5987','5988','5989','5998','5999','6000','6001','6002','6003','6004','6005','6006','6007','6009','6025','6059','6100','6101','6106','6112','6123','6129','6156','6346','6389','6502','6510','6543','6547','6565','6566','6567','6580','6646','6666','6667','6668','6669','6689','6692','6699','6779','6788','6789','6792','6839','6881','6901','6969','7000','7001','7002','7004','7007','7019','7025','7070','7100','7103','7106','7200','7201','7402','7435','7443','7496','7512','7625','7627','7676','7741','7777','7778','7800','7911','7920','7921','7937','7938','7999','8000','8001','8002','8007','8008','8009','8010','8011','8021','8022','8031','8042','8045','8080','8081','8082','8083','8084','8085','8086','8087','8088','8089','8090','8093','8099','8100','8180','8181','8192','8193','8194','8200','8222','8254','8290','8291','8292','8300','8333','8383','8400','8402','8443','8500','8600','8649','8651','8652','8654','8701','8800','8873','8888','8899','8994','9000','9001','9002','9003','9009','9010','9011','9040','9050','9071','9080','9081','9090','9091','9099','9100','9101','9102','9103','9110','9111','9200','9207','9220','9290','9415','9418','9485','9500','9502','9503','9535','9575','9593','9594','9595','9618','9666','9876','9877','9878','9898','9900','9917','9929','9943','9944','9968','9998','9999','10000','10001','10002','10003','10004','10009','10010','10012','10024','10025','10082','10180','10215','10243','10566','10616','10617','10621','10626','10628','10629','10778','11110','11111','11967','12000','12174','12265','12345','13456','13722','13782','13783','14000','14238','14441','14442','15000','15002','15003','15004','15660','15742','16000','16001','16012','16016','16018','16080','16113','16992','16993','17877','17988','18040','18101','18988','19101','19283','19315','19350','19780','19801','19842','20000','20005','20031','20221','20222','20828','21571','22939','23502','24444','24800','25734','25735','26214','27000','27352','27353','27355','27356','27715','28201','30000','30718','30951','31038','31337','32768','32769','32770','32771','32772','32773','32774','32775','32776','32777','32778','32779','32780','32781','32782','32783','32784','32785','33354','33899','34571','34572','34573','35500','38292','40193','40911','41511','42510','44176','44442','44443','44501','45100','48080','49152','49153','49154','49155','49156','49157','49158','49159','49160','49161','49163','49165','49167','49175','49176','49400','49999','50000','50001','50002','50003','50006','50300','50389','50500','50636','50800','51103','51493','52673','52822','52848','52869','54045','54328','55055','55056','55555','55600','56737','56738','57294','57797','58080','60020','60443','61532','61900','62078','63331','64623','64680','65000','65129','65389']
			for port in ports:
				try:
					s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
					s.settimeout(0.1)
					s.connect((ip,int(port)))
					s.close()
				except:
					pass
				else:
					await ctx.send(f'```\nPort {port} is open\n```')
		else:
			await ctx.send(f'**{ip}** is not a valid IP address')

	@commands.command(name='ping',description='Pings a host')
	async def _ping(self, ctx, ip):
		try:
			response = ping(ip)
			await ctx.send(f'```\n{response}\n```')
		except:
			Networking.validateip(self, ctx, ip)
			if not ip_valid:
				await ctx.send(f'**{ip}** is not a valid IP address or domain name')
			else:
				await ctx.send(f'Failed to ping **{ip}**')

	@commands.command(description='Returns IP geolocation data for an IP address')
	async def ip_geo(self, ctx, ip):
		Networking.validateip(self,ctx, ip)
		if ip_valid:
			try:
				r = requests.get(f'https://api.ipgeolocation.io/ipgeo?apiKey={ip_geo_api_key}&ip={ip}')
				data = r.json()
				pretty_data = json.dumps(data, indent=1)
				await ctx.send(f'```json\n{pretty_data}\n```')
			except:
				await ctx.send(f'IP lookup for **{ip}** failed!')

class Admin(commands.Cog):
	def _restart():
		pid = os.getpid()
		os.system(f'python3 {os.path.join(path,os.path.basename(__file__))}')
		os.system(f'powershell.exe kill {pid}')

	def _exit():
		os.kill(os.getpid(),signal.SIGTERM)

	@commands.is_owner()
	@commands.command(description='Restarts the bot')
	async def restart(self, ctx):
		await ctx.send('**Restarting...**')
		await Admin._restart()
		#await os.kill(pid,signal.SIGTERM)

	@commands.is_owner()
	@commands.command(description='Exits the bot')
	async def exit(self, ctx):
		await ctx.send('**Exiting...**')
		await Admin._exit()

	#This function is unsafe (remote code execution)
	#@commands.is_owner()
	#@commands.command(description='Evaluates a math equation')
	#async def math(self, ctx,*args):
	#	expression = ' '.join(args)
	#	try:
	#		answer = eval(expression)
	#	except:
	#		await ctx.send(f'**{expression}** is not a valid expression!')
	#	else:
	#		await ctx.send(f'```\n{answer}\n```')

class Colors:
	BLACK = '\033[0;30m'
	RED = '\033[0;31m'
	GREEN = '\033[0;32m'
	BROWN = '\033[0;33m'
	BLUE = '\033[0;34m'
	PURPLE = '\033[0;35m'
	CYAN = '\033[0;36m'
	LIGHT_GRAY = '\033[0;37m'
	DARK_GRAY = '\033[1;30m'
	LIGHT_RED = '\033[1;31m'
	LIGHT_GREEN = '\033[1;32m'
	YELLOW = '\033[1;33m'
	LIGHT_BLUE = '\033[1;34m'
	LIGHT_PURPLE = '\033[1;35m'
	LIGHT_CYAN = '\033[1;36m'
	LIGHT_WHITE = '\033[1;37m'
	BOLD = '\033[1m'
	FAINT = '\033[2m'
	ITALIC = '\033[3m'
	UNDERLINE = '\033[4m'
	BLINK = '\033[5m'
	NEGATIVE = '\033[7m'
	CROSSED = '\033[9m'
	END = '\033[0m'

def log_event(user,text,server=''):
	server = f' [{server}] '
	if user == thrall.user:
		event = f'{Colors.YELLOW}[{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}]{Colors.END}{Colors.RED}{server}{Colors.END}{Colors.PURPLE}{user}:{Colors.END} {text}'
	else:
		event = f'{Colors.YELLOW}[{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}]{Colors.END}{Colors.RED}{server}{Colors.END}{Colors.BLUE}{user}:{Colors.END} {text}'
	return event

@thrall.event
async def on_ready():
	if os.name == 'nt':
		os.system('cls')
	else:
		os.system('clear')
	invite = f'{Colors.LIGHT_BLUE}https://discordapp.com/oauth2/authorize?client_id={thrall.user.id}&scope=bot&permissions={8}{Colors.END}'
	print(log_event(thrall.user,f'{Colors.GREEN}Is online{Colors.END}'))
	for guild in thrall.guilds: 
		print('-'*50)
		print(f'|{Colors.RED}{guild.name}{Colors.END}{" "*(48-len(guild.name))}|')
		print('-'*50)
		for member in guild.members:
			print(f'|{Colors.BLUE}{member.name}{Colors.END}{" "*(29-len(member.name))}|{Colors.GREEN}{member.id}{Colors.END}|')
		print('-'*50)
		print()

@thrall.event
async def on_member_join(member):
    print(log_event(member.name,'Joined',member.guild))

@thrall.event
async def on_member_leave(member):
	print(log_event(member.name,'Left',member.guild))

@thrall.event
async def on_message(message):
	print(log_event(message.author,message.content,message.guild))
	await thrall.process_commands(message)

@thrall.event
async def on_command_error(ctx, error):
	if isinstance(error, commands.CommandNotFound):
		await ctx.send(f'That command does not exist!')

thrall.add_cog(Music(thrall))
thrall.add_cog(Cryptography(thrall))
thrall.add_cog(Networking(thrall))
thrall.add_cog(Misc(thrall))
thrall.add_cog(Admin(thrall))
thrall.run(discord_api_key)
