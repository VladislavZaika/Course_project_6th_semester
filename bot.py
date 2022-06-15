import discord
from discord.ext import commands
from discord_components import DiscordComponents, Button, ButtonStyle

import sqlite3
from config import settings

client = commands.Bot(command_prefix = settings['PREFIX'], intents = discord.Intents.all())
client.remove_command('help')

connection = sqlite3.connect('server.db')
cursor = connection.cursor()

@client.event
async def on_ready():
	DiscordComponents(client)
	cursor.execute("""CREATE TABLE IF NOT EXISTS users (
		name TEXT,
		id INT,
		cash BIGINT,
		rep INT,
		lvl INT,
		server_id INT,
		hp INT
	)""")

	cursor.execute("""CREATE TABLE IF NOT EXISTS shop (
		role_id INT,
		id INT,
		cost BIGINT
		)""")


	for guild in client.guilds:
		for member in guild.members:
			if cursor.execute(f"SELECT id FROM users WHERE id = {member.id}").fetchone() is None:
				cursor.execute(f"INSERT INTO users VALUES ('{member}', {member.id}, 0, 0, 1, {guild.id}, 100)") #если что-то добавлять, то стартовые значения писать сюда
			else:
				pass

	connection.commit()
	print('Бот начал работу')

@client.event
async def  on_member_join(member):
	if cursor.execute(f"SELECT id FROM users WHERE id = {member.id}").fetchone() is None:
		cursor.execute(f"INSERT INTO users VALUES ('{member}', {member.id}, 0, 0, 1, {member.guild.id}, 100)") #и сюда тоже
		connection.commit()
	else:
		pass

@client.command(aliases = ['balance', 'cash']) #можно писать и balance, и cash. Результат будет один и тот же
async def __balance(ctx, member: discord.Member = None):
	if member is None:
		await ctx.send(embed = discord.Embed(
			description = f"""Баланс пользователя **{ctx.author}** составляет **{cursor.execute("SELECT cash FROM users WHERE id = {}".format(ctx.author.id)).fetchone()[0]} :coin:**"""
			))
		print('Пользователь {} просмотрел свой баланс'.format(ctx.author))
	else:
		await ctx.send(embed = discord.Embed(
			description = f"""Баланс пользователя **{member}** составляет **{cursor.execute("SELECT cash FROM users WHERE id = {}".format(member.id)).fetchone()[0]} :coin:**"""
			))
		print('Пользователь {} просмотрел баланс пользователя {}'.format(ctx.author, member.name))

@client.command(aliases = ['award'])
async def __award(ctx, member: discord.Member = None, amount: int = None):
	if ctx.author.guild_permissions.administrator:
		if member is None:
			await ctx.send(f"**{ctx.author}**, укажите пользователя, которого Вы желаете наградить")
			print('[ADMIN ERROR] Пользователь {} хотел перевести деньги другому пользователю, но не указал кому именно'.format(ctx.author))
		else:
			if amount is None:
				await ctx.send(f"**{ctx.author}, укажите сумму, которую желаете начислить на счёт пользователя**")
				print('[ADMIN ERROR] Пользователь {} хотел перевести деньги пользователю {}, но не указал сумму перевода'.format(ctx.author, member.name))
			elif amount < 1:
				await ctx.send(f"**{ctx.author}**, укажите сумму больше 1 :coin:")
				print('[ADMIN ERROR] Пользователь {} хотел перевести деньги пользователю {}, но указал сумму меньше 1'.format(ctx.author, member.name))
			else:
				cursor.execute("UPDATE users SET cash = cash + {} WHERE id = {}".format(amount, member.id))
				connection.commit()

				await ctx.message.add_reaction('✅')
				print('[ADMIN ACT] Пользователь {} передал деньги пользователю {} в количестве {}'.format(ctx.author, member.name, amount))
	else:
		await ctx.message.add_reaction('❌')
		await ctx.send(f"**{ctx.author}**, данная команда вам недоступна")
		print('Пользователь {} пытался воспользоваться админской командой'.format(ctx.author))

@client.command(aliases = ['take'])
async def __take(ctx, member: discord.Member = None, amount = None):
	if ctx.author.guild_permissions.administrator:
		if member is None:
			await ctx.send(f"**{ctx.author}**, укажите пользователя, у которого желаете забрать деньги")
			print('[ADMIN ERROR] Пользователь {} хотел забрать деньги другому пользователю, но не указал у кого именно'.format(ctx.author))
		else:
			if amount is None:
				await ctx.send(f"**{ctx.author}, укажите сумму, которую желаете забрать у пользователя**")
				print('[ADMIN ERROR] Пользователь {} хотел забрать деньги пользователю {}, но не указал какую сумму'.format(ctx.author, member.name))
			elif amount == 'all':
				cursor.execute("UPDATE users SET cash = {} WHERE id = {}".format(0, member.id))
				connection.commit()

				await ctx.message.add_reaction('✅')
				print('[ADMIN ACT] Пользователь {} забрал все деньги у пользователя {}'.format(ctx.author, member.name, amount))
			elif int(amount) < 1:
				await ctx.send(f"**{ctx.author}**, укажите сумму больше 1 :coin:")
				print('[ADMIN ERROR] Пользователь {} хотел забрать деньги у пользователя {}, но указал сумму меньше 1'.format(ctx.author, member.name))
			elif int(amount) > cursor.execute("SELECT cash FROM users WHERE id = {}".format(member.id)).fetchone()[0]:
				await ctx.send(f"**{ctx.author}**, Вы пытаетесь забрать слишком много денег у {member.name}. Он не настолько богат")
				print('[ADMIN ERROR] Пользователь {} хотел забрать деньги у пользователя {}, но указал слишком большую сумму'.format(ctx.author, member.name))
			else:
				cursor.execute("UPDATE users SET cash = cash - {} WHERE id = {}".format(int(amount), member.id))
				connection.commit()

				await ctx.message.add_reaction('✅')
				print('[ADMIN ACT] Пользователь {} забрал деньги у пользователя {} в количестве {}'.format(ctx.author, member.name, amount))
	else:
		await ctx.message.add_reaction('❌')
		await ctx.send(f"**{ctx.author}**, данная команда вам недоступна")
		print('Пользователь {} пытался воспользоваться админской командой'.format(ctx.author))

@client.command(aliases = ['give'])
async def __give(ctx, member: discord.Member = None, amount: int = None):
	if member is None:
		await ctx.send(f"**{ctx.author}**, укажите пользователя, которому Вы желаете передать деньги")
		print('Пользователь {} хотел перевести деньги другому пользователю, но не указал кому именно'.format(ctx.author))
	else:
		if amount is None:
			await ctx.send(f"**{ctx.author}, укажите сумму, которую Вы желаете передать пользователю {member.name}**")
			print('Пользователь {} хотел перевести деньги пользователю {}, но не указал сумму перевода'.format(ctx.author, member.name))
		elif amount < 1:
			await ctx.send(f"**{ctx.author}**, укажите сумму больше 1 :coin:")
			print('Пользователь {} хотел перевести деньги пользователю {}, но указал сумму меньше 1'.format(ctx.author, member.name))
		elif int(amount) > cursor.execute("SELECT cash FROM users WHERE id = {}".format(ctx.author.id)).fetchone()[0]:
			await ctx.send(f"**{ctx.author}**, Вы пытаетесь передать слишком много денег. Вы не настолько богаты")
			print('Пользователь {} передать деньги пользователю {}, но указал сумму, большую чем имеет сам'.format(ctx.author, member.name))
		else:
			cursor.execute("UPDATE users SET cash = cash + {} WHERE id = {}".format(amount, member.id))
			cursor.execute("UPDATE users SET cash = cash - {} WHERE id = {}".format(int(amount), ctx.author.id))
			connection.commit()

			await ctx.message.add_reaction('✅')
			print('Пользователь {} передал деньги пользователю {} в количестве {}'.format(ctx.author, member.name, amount))

@client.command(aliases = ['add-shop'])
async def __add_shop(ctx, role: discord.Role = None, cost: int = None):
	if role is None:
		await ctx.send(f"**{ctx.author}**, укажите роль, которую вы желаете внести в магазин")
		print('[ADMIN ERROR] Пользователь {} пытался добавить новую роль в магазин, но не указал какую именно'.format(ctx.author))
	else:
		if cost is None:
			await ctx.send(f"**{ctx.author}**, укажите стоимость для данной роли")
			print('[ADMIN ERROR] Пользователь {} пытался добавить новую роль {} в магазин, но не указал её цену'.format(ctx.author, role.name))
		elif cost < 0:
			await ctx.send(f"**{ctx.author}**, стоимость роли не может быть такой маленькой")
			print('[ADMIN ERROR] Пользователь {} пытался добавить новую роль {} в магазин, но указал слишком маленькую цену'.format(ctx.author, role.name))
		else:
			cursor.execute("INSERT INTO shop VALUES ({}, {}, {})".format(role.id, ctx.guild.id, cost))
			connection.commit()

			await ctx.message.add_reaction('✅')
			print('[ADMIN ACT] Пользователь {} добавил новую роль {} в магазин'.format(ctx.author, role.name))

@client.command(aliases = ['remove-shop'])
async def __remove_shop(ctx, role: discord.Role = None):
	if role is None:
		await ctx.send(f"**{ctx.author}**, укажите роль, которую вы желаете удалить из магазина")
		print('[ADMIN ERROR] Пользователь {} пытался удалить роль из магазина, но не указал какую именно'.format(ctx.author))
	else:
		cursor.execute("DELETE FROM shop WHERE role_id = {}".format(role.id))
		connection.commit()

		await ctx.message.add_reaction('✅')
		print('[ADMIN ACT] Пользователь {} удалил роль из магазина'.format(ctx.author))

@client.command(aliases = ['shop'])
async def __shop(ctx):
	embed = discord.Embed(title = 'Магазин ролей')

	for row in cursor.execute("SELECT role_id, cost FROM shop WHERE id = {}".format(ctx.guild.id)):
		if ctx.guild.get_role(row[0]) != None:
			embed.add_field(
				name = f"Стоимость {row[1]}",
				value = f"Вы приобрете роль {ctx.guild.get_role(row[0]).mention}",
				inline = False #С False наши значения будут выводиться в столбик
			)
		else:
			pass

	await ctx.send(embed = embed)
	print('Пользователь {} просмотрел содержимое магазин'.format(ctx.author))

@client.command(aliases = ['buy', 'buy-role'])
async def __buy(ctx, role: discord.Role = None):
	if role is None:
		await ctx.send(f"**{ctx.author}**, укажите роль, которую вы желаете приобрести")
		print('Пользователь {} пытался купить роль, но не указал какую именно'.format(ctx.author))
	else:
		if role in ctx.author.roles:
			await ctx.send(f"**{ctx.author}**, у вас уже имеется данная роль")
			print('Пользователь {} пытался купить роль {}, но она у него уже была'.format(ctx.author, role.name))
		elif cursor.execute("SELECT cost FROM shop WHERE role_id = {}".format(role.id)).fetchone()[0] > cursor.execute("SELECT cash FROM users WHERE id = {}".format(ctx.author.id)).fetchone()[0]:
			await ctx.send(f"**{ctx.author}**, у вас недостаточно средств для покупки данной роли")
			print('Пользователь {} пытался купить роль {}, но ему не хватило денег'.format(ctx.author, role.name))
		else:
			await ctx.author.add_roles(role)
			cursor.execute("UPDATE users SET cash = cash - {} WHERE id = {}".format(cursor.execute("SELECT cost FROM shop WHERE role_id = {}".format(role.id)).fetchone()[0], ctx.author.id))
			connection.commit()

			await ctx.message.add_reaction('✅')
			print('Пользователь {} успешно приобрел роль {}'.format(ctx.author, role.name))

@client.command(aliases = ['sell', 'sell-role'])
async def __sell(ctx, role: discord.Role = None):
	if role is None:
		await ctx.send(f"**{ctx.author}**, укажите роль, которую вы желаете продать")
		print('Пользователь {} пытался продать роль, но не указал какую именно'.format(ctx.author))
	else:
		if role not in ctx.author.roles:
			await ctx.send(f"**{ctx.author}**, у Вас нету такой роли")
			print('Пользователь {} пытался продать роль {}, но у него её не было'.format(ctx.author, role.name))
		else:
			await ctx.author.remove_roles(role)
			cursor.execute("UPDATE users SET cash = cash + {} WHERE id = {}".format(cursor.execute("SELECT cost FROM shop WHERE role_id = {}".format(role.id)).fetchone()[0], ctx.author.id))
			connection.commit()

			await ctx.message.add_reaction('✅')
			print('Пользователь {} успешно продал роль {}'.format(ctx.author, role.name))

@client.command(aliases = ['+rep'])
async def __rep(ctx, member: discord.Member = None):
	if member is None:
		await ctx.send(f"**{ctx.author}**, укажите пользователя, которому вы респектуете")
		print('Пользователь {} пытался дать респект другому пользователю, но не указал кому именно'.format(ctx.author))
	else:
		if member.id == ctx.author.id:
			await ctx.send(f"**{ctx.author}**, вы не можете респектовать самому себе ||даже если очень хочется||")
			print('Пользователь {} пытался респектовать самому себе'.format(ctx.author))
		else:
			cursor.execute("UPDATE users SET rep = rep + {} WHERE id = {}".format(1, member.id))
			connection.commit()

			await ctx.message.add_reaction('✅')
			print('Пользователь {} дал респект пользователю {}'.format(ctx.author, member.name))

@client.command(aliases = ['leaderboard', 'lb'])
async def __leaderboard(ctx):
	embed = discord.Embed(title = 'Топ 10 пользователей сервера')
	counter = 0

	for row in cursor.execute("SELECT name, cash FROM users WHERE server_id = {} ORDER BY cash DESC LIMIT 10".format(ctx.guild.id)):
		counter += 1
		embed.add_field(
			name = f'# {counter} | {row[0]}',
			value = f'Баланс: {row[1]}',
			inline = False
		)

	await ctx.send(embed = embed)
	print('Пользователь {} просмотрел таблицу лидеров'.format(ctx.author))

@client.command(aliases = ['help_bb'])
async def __help(ctx):
	await ctx.send(
		embed = discord.Embed(title = "Вам необходима помощь в ознакомлении с сервером?"),
		components = [
			Button(style = ButtonStyle.green, label = "Да", emoji = "✔️"),
			Button(style = ButtonStyle.red, label = "Нет", emoji = "❌")
		]
	)

	response = await client.wait_for("button_click")
	if response.channel == ctx.channel:
		if response.component.label == "Да":
			await response.respond(content = "*Вывод информации о сервере*")
		else:
			await ctx.channel.purge(limit = 1)

@client.command(pass_context = True, aliases = ['clear'])
async def __clear(ctx, amount = 100):
	if ctx.author.guild_permissions.administrator:
		await ctx.channel.purge(limit = amount + 1)
	else:
		await ctx.message.add_reaction('❌')
		await ctx.send(f"**{ctx.author}**, данная команда вам недоступна")


client.run(settings['TOKEN'])


