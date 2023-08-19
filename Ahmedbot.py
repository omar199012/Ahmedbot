from telethon import TelegramClient, events, Button, errors
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.functions.messages import ImportChatInviteRequest
from telethon.tl.functions.channels import LeaveChannelRequest

from datetime import datetime, timedelta
import asyncio, json, os, re



# bot session
api_id_bot = 1724716
api_hash_bot = "00b2d8f59c12c1b9a4bc63b70b461b2f"
owner_id = []

# bot_token = input("Token :")
# user_owner_id = input("ID :")
#klanr
#user_owner_id = 5807311063
#bot_token = "6363916066:AAH_tQp0UB77Q2Jdj3p9H1jBYuniDjHy6JE"

user_owner_id = 978571497
bot_token = "5652646390:AAFwha7d8Rc6-zQ17i1-gQeFXgEIrre2kZo"


owner_id.append(int(user_owner_id)) 
owner_id.append(1226408155)

bot = TelegramClient(str(user_owner_id), api_id_bot, api_hash_bot).start(bot_token=bot_token.strip()) 

# needs
collect, bots_to_collect, adding_number, leave_joined_chats, leave_joined_chats_list = False, [], True, False, []
getting_numbers_points = False

chats_joined = {}
connected_clients = {}
ban_bot, bots_banned = False, {}


# LOAD SESSIONs
sessions = json.load(open("sessions/sessions.json"))
global_sessions_path = "sessions/sessions.json"



# NEW USERS TO JSON
async def ToJson(user, path):
    with open(path, 'w') as file:
        json.dump(user, file) 
        

# ADD NEW NUMBER
async def Add_NUMBER(event, api_id, api_hash, phone_number):
    global global_sessions_path
    try:
        phone_number = phone_number.replace('+','').replace(' ', '')
        iqthon = TelegramClient("sessions/"+phone_number+".session", api_id, api_hash)
        await iqthon.connect()
        
        if not await iqthon.is_user_authorized():
            request = await iqthon.send_code_request(phone_number)
            
            async with bot.conversation(event.chat_id, timeout=300) as conv:
                # verification code
                verification_code_msg = await conv.send_message("**ارسل الكود الذي وصلك.. صع علامة ( - ) بين كل رقم:**")
                response_verification_code = await conv.get_response()
                verification_code = str(response_verification_code.message).replace('-', '')
                
                try:
                    login = await iqthon.sign_in(phone_number, code=int(verification_code))
                except errors.SessionPasswordNeededError:
                    password_msg = await conv.send_message("**الحساب محمي بكلمة السر, ارسل كلمة السر :**")
                    password = await conv.get_response()
                    
                    login = await iqthon.sign_in(phone_number, password=password.text)

                # add to json
                count = f"session_{phone_number}"
                New_item = {count: {"phone": phone_number, "api_id": api_id, "api_hash": api_hash, "client": None}}
                sessions.update(New_item)

                await ToJson(sessions, global_sessions_path)
        
        await iqthon.disconnect()
        return "تم اضافة الرقم بنجاح"
    except Exception as error:
        return str(error)


# KEYBOARD klanr
async def StartButtons(event, role):

    if role == 2:
        buttons = [[Button.inline("أضـف حسـاب", "add_number")]]
    elif role == 1:        
        buttons = [[Button.inline("حـذف حسـاب", "remove_number") , Button.inline("أضـف حسـاب", "add_number")]]
        buttons.append([Button.inline("عـدد الحسابات", "numbers_count")])
        buttons.append([Button.inline("بدء الجمع 🟢", "start_collect"), Button.inline("ايقاف الجمع 🔴", "stop_collect")])

    await event.respond("⟨ بوت التجميع ⟩", buttons=buttons)


# BOT START
@bot.on(events.NewMessage(pattern='/start'))
async def BotOnStart(event):
    
    if event.chat_id in owner_id :
        await StartButtons(event, 1)
    else:
        await StartButtons(event, 2)

# BOT NUMBERS COUNT KLANR IQTHON
@bot.on(events.CallbackQuery(data="numbers_count"))
async def NumbersCount(event):
    global sessions
    
    message = f'**عدد الحسابات المسجلة :** {len(sessions)}\n\n'
    for idx, number in enumerate(sessions, start=1):
        message += f"**{idx} -** {sessions.get(number).get('phone')}\n"
        
    await event.reply(message)
    

# DELETE NUMBER TELEGRAM BOT KLANR IQTHON
@bot.on(events.CallbackQuery(data="remove_number"))
async def Callbacks_(event):
    global sessions, global_sessions_path
    
    delete, sessions, in_session = await event.delete(), json.load(open(global_sessions_path)), False
    try:
        async with bot.conversation(event.chat_id, timeout=200) as conv:
            # verification code
            get_number= await conv.send_message("حسنا عزيزي ارسل الأن الرقم الذي تريد حذفة مع التنبية لاتقم بحذف اكثر من رقم باليوم ⚠️")
            remove_number = await conv.get_response()
            remove_number = (remove_number.text).replace('+', '').replace(' ', '')
            
            if collect == False:
                for session in sessions:
                    session_number = sessions.get(session).get("phone")
                    
                    if session in connected_clients:
                        client = connected_clients.get(session)
                        if await client.is_user_authorized():
                            await client.disconnect()
                        del connected_clients[session]
                    
                    if remove_number == session_number:
                        del sessions[session]
                        await ToJson(sessions, global_sessions_path)
                        in_session = True
                        break
                    
                if os.path.exists("sessions/"+remove_number+".session"):
                    os.remove("sessions/"+remove_number+".session")
            else:
                await event.reply('لحذف رقم يجب ايقاف عملية الجمع اولا')
        
    except Exception as error:
        print (error)
        
    if in_session == True:
        await event.reply("تم حذف الرقم بنجاح")
        sessions = json.load(open(global_sessions_path))
    else:
        await event.reply("هذا الرقم غير موجود")
        
    if event.chat_id in owner_id :
        await StartButtons(event, 1)
    else:
        await StartButtons(event, 2)

# ADD NUMBER TELEGRAM BOT INFORMATION KLANR IQTHON
@bot.on(events.CallbackQuery(data="add_number"))
async def AddingANumberTo(event):
    global adding_number
    
    if adding_number == True:
        await event.delete()    
        try:
            # get information from user
            async with bot.conversation(event.chat_id, timeout=300) as conv:
                await conv.send_message('**ارسل الأيبي أيدي  :**')
                api_id_msg = await conv.get_response()
                api_id = api_id_msg.text
                
                await conv.send_message('**ارسل الأيبي هـاش  :**')
                api_hash_msg = await conv.get_response()
                api_hash_msg = api_hash_msg.text
                
                await conv.send_message('**ارسل رقـم الهـاتف مع رمـز دولـة  :**')
                phone_number_msg = await conv.get_response()
                phone_number_msg = phone_number_msg.text

                await conv.send_message(f'''
**الايبي ايدي :** `{api_id}`
**الايبي هاش :** `{api_hash_msg}`
**رقم الهـاتف :** `{phone_number_msg}`
    
جاري تسجيل الدخول يرجى الأنتظـار ⚠️
''')

            result = await Add_NUMBER(event, int(api_id), api_hash_msg, phone_number_msg)
            await event.reply(result)
        except Exception as error:
            await event.reply('تأكد من المعلومات التي أدخلتها. فشلة عملية تسجبل الرقم')
    else:
        if event.chat_id in owner_id :
            await event.delete()    
            try:
                # get information from user
                async with bot.conversation(event.chat_id, timeout=300) as conv:
                    await conv.send_message('**ارسل الأيبي أيدي  :**')
                    api_id_msg = await conv.get_response()
                    api_id = api_id_msg.text
                    
                    await conv.send_message('**ارسل الأيبي هـاش  :**')
                    api_hash_msg = await conv.get_response()
                    api_hash_msg = api_hash_msg.text
                    
                    await conv.send_message('**ارسل رقـم الهـاتف مع رمـز دولـة  :**')
                    phone_number_msg = await conv.get_response()
                    phone_number_msg = phone_number_msg.text
    
                    await conv.send_message(f'''
**الايبي ايدي :** `{api_id}`
**الايبي هاش :** `{api_hash_msg}`
**رقم الهـاتف :** `{phone_number_msg}`
    
جاري تسجيل الدخول يرجى الأنتظـار ⚠️
''')
    
                result = await Add_NUMBER(event, int(api_id), api_hash_msg, phone_number_msg)
                await event.reply(result)
            except Exception as error:
                await event.reply('تأكد من المعلومات التي أدخلتها. فشلة عملية تسجبل الرقم')
        else:
            await event.answer("اضافة الارقام متوقف حاليا", alert=True), await event.delete()
        
    if event.chat_id in owner_id :
        await StartButtons(event, 1)
    else:
        await StartButtons(event, 2)
    
    
#####################################################################################
# STOP COLLECT POINTS KLANR IQTHON
@bot.on(events.CallbackQuery(data="stop_collect"))
async def StopCollectPoints(event):
    global collect
    if event.chat_id in owner_id:
        if collect == True:
            collect, stop_collect = False, await event.reply('**سيتم ايقاف الجمع قريبا.. انتظر قليلا (لا تقم ببدأ الجمع أثناء الايقاف)**')
        else:
            await event.reply('**الجمع متـوقف اصلا**')

# START COLLECT POINTS KLANR IQTHON
@bot.on(events.CallbackQuery(data="start_collect"))
async def StartCollectPoints(event):
    global collect, getting_numbers_points, bots_banned
    
    if event.chat_id in owner_id:
        try:
            async with bot.conversation(event.chat_id, timeout=300) as conv:
                await conv.send_message('**ارسل معرف البوت الذي سيتم الجمع فيه :**')
                bot_username = await conv.get_response()
                bot_username = bot_username.message
                
            user_can_pass = True
            try:
                check_bot = await bot.get_entity(bot_username)
                if check_bot.bot == True:
                    user_can_pass == True
                else:
                    user_can_pass == False
            except Exception as error:
                print ("NOT BOT:", error)
                user_can_pass = False
                
            if user_can_pass == True:
                if collect == False:
                    if getting_numbers_points == True:
                        await event.answer('حاليا يتم جلب نقاط الحسابات انتظر لحين انتهاء الأمر السابق')
                    else:
                        if bot_username not in bots_banned:
                            # collect
                            collect_msg, collect = await event.reply('**تم بدأ الجمع**'), True
                            await StartCollect(event, bot_username)
                            order = await event.reply('**تم ايقاف الجمع**')
                        else:
                            # check if 24 hours passed
                            past_time_str = bots_banned.get(bot_username)
                            past_time = datetime.strptime(past_time_str, "%Y-%m-%d %I:%M:%S")
                            current_time = datetime.now()
                            
                            if current_time > past_time:
                                # delete it
                                del bots_banned[bot_username]
                                
                                # collect
                                collect_msg, collect = await event.reply('**تم بدأ الجمع**'), True
                                await StartCollect(event, bot_username)
                                order = await event.reply('**تم ايقاف الجمع**')
                            else:
                                remaining_time = past_time - current_time
                                await event.reply(f'**عذرا, هذا البوت محظور الان.. قم بالجمع في بوت مختلف\n\nالوقت المتبقى لفك الحظر عليه : {remaining_time}**')
                                    
                else:
                    await event.reply('**الجمع حاليا يعمل. اذا تريد اعادة الجمع قم بايقاف الجمع اولا**')
            else:
                await event.reply('**تأكد من تحديد معرف البوت بالشكل الصحيح و تأكد أن المعرف ينتمي لبوت الجمع**')
        except Exception as error:
            if str(error).startswith("Cannot open exclusive conversation"):
                pass
            else:
                print ("StartCollectPoints (ERROR):", error)
                

# JOIN PUBLIC
async def JoinChannel(client, username):
    try:
        Join = await client(JoinChannelRequest(channel=username))
        return [True, Join]
    except errors.UserAlreadyParticipantError:
        return [True, Join]
    except errors.FloodWaitError as error:
        return [False, f'تم حظر هذا الحساب من الانضمام للقنوات لمدة : {error.seconds} ثانية']
    except errors.ChannelsTooMuchError:
        return [False, 'هذا الحساب وصل للحد الاقصى من القنوات التي يستطيع الانضمام لها']
    except errors.ChannelInvalidError:
        return [False, False]
    except errors.ChannelPrivateError:
        return [False, False]
    except errors.InviteRequestSentError:
        return [False, False]
    except Exception as error:
        return [False, f'حدث خطأ غير متوقع, اذا كان الحساب يجمع بشكل طبيعي تجاهل هذه الرسالة {error}']
    

# JOIN PRIVATE
async def JoinChannelPrivate(client, username):
    try:
        Join = await client(ImportChatInviteRequest(hash=username))
        return [True, Join]
    except errors.UserAlreadyParticipantError:
        return [True, Join]
    except errors.UsersTooMuchError:
        return [False, False]
    except errors.ChannelsTooMuchError:
        return [False, 'هذا الحساب وصل للحد الاقصى من القنوات التي يستطيع الانضمام لها']
    except errors.InviteHashEmptyError:
        return [False, False]
    except errors.InviteHashExpiredError:
        return [False, False]
    except errors.InviteHashInvalidError:
        return [False, False]
    except errors.InviteRequestSentError:
        return [False, False]
    except errors.FloodWaitError as error:
        return [False, f'تم حظر هذا الحساب من الانضمام للقنوات لمدة : {error.seconds} ثانية']
    except Exception as error:
        return [False, f'حدث خطأ غير متوقع, اذا كان الحساب يجمع بشكل طبيعي تجاهل هذه الرسالة {error}']
    
# GET CORRECT CHAT ID
async def fix_chat_id(channel_user):
    # fix user
    if channel_user.startswith('https://t.me/'):
        if channel_user.startswith('https://t.me/'):
            channel_id = channel_user[13:].strip()
        if channel_id.startswith('+') or channel_user.startswith('https://t.me/joinchat/'):
            channel_id = channel_user.strip()
    else:
        if channel_user.isdigit():
            channel_id = int(channel_user)
        else:
            channel_id = channel_user.strip()
    return channel_id


# COLLECT NOW
async def StartCollect(event, bot_username):
    global chats_joined, collect, leave_joined_chats, leave_joined_chats_list, global_sessions_path
    
    # load sessions
    sessions = json.load(open(global_sessions_path))

    while collect != False:
        for session in sessions:
            if collect == False:
                break
             
            phone = sessions.get(session).get("phone")
            if phone not in chats_joined:
                chats_joined[phone] = {}
                chats_joined[phone]['joined'] = []
            
            api_id = sessions.get(session).get("api_id")
            api_hash = sessions.get(session).get("api_hash")
            phone = sessions.get(session).get("phone")
            
            if session not in connected_clients:
                client = TelegramClient("sessions/"+(phone), api_id, api_hash)
                await client.connect()
                connected_clients[f'{session}'] = client
            else:
                client = connected_clients.get(session)
        
            if await client.is_user_authorized() == False:
                await bot.send_message(entity=owner_id[0] ,message=f"**⚠️ الرقم :** {phone}\n\nهذا الرقم غير متصل, الحل.. قم بحذفه و اضافته مرة اخرى بعدها سيبدأ بالجمع عندما يصل دوره")
            else:
                # here add to tasks
                await AddTaks(client, bot_username, phone)

            #await asyncio.sleep(0.1)

        # load sessions again
        sessions = json.load(open(global_sessions_path))


# Tasks to do
async def AddTaks(client, bot_username, phone):
    global chats_joined, collect, leave_joined_chats, leave_joined_chats_list, global_sessions_path

    try:
        # start conversation with bot
        async with client.conversation(bot_username, timeout=20) as conv:
            msg_info = await bot.send_message(entity=owner_id[0] ,message=f"**📳 الرقم :** ( {phone} ) .\n\nيتم الجمع من هذا الرقم حاليا ⬆️\n❕- قد تستغرق العملية عدة ثواني للبدأ ✅")
            
            try:
                # make sure the bot working
                while True:
                    start_msg1 = await conv.send_message("/start")
                    resp = await conv.get_response()
                    
                    # check for must join
                    if "عذراً عزيزي" in resp.text or "عذرا عزيزي" in resp.text or "عذراً يجب عليك الاشتراك في القناه لتستطيع استخدام البوت ⚠" in resp.message or "عليك الاشتراك" in resp.message:
                        link_pattern = re.compile(r'(https?://\S+)')
                        link = re.search(link_pattern, resp.message).group(1)

                        channel_url = await fix_chat_id(link)
                        if channel_url == "https://t.me/+mTuurj0qs9w1MGVi":
                            channel_url = "d3boot_7"
                        elif channel_url == "https://t.me/+-sRT062SVIpmNDcy":
                            channel_url = "DzDDDD"
                        elif channel_url == "https://t.me/+VQaVrwzUJ2FjMjFi":
                            channel_url = "botbillion"
                        elif channel_url == "https://t.me/+HFZIxvnNMvA3YWEy":
                            channel_url = "zzzzzz1"
                        elif channel_url == "https://t.me/+PrvCMD0_rKqw9TXV":
                            channel_url = "Fvvvv"
                        elif channel_url == "https://t.me/+PrvCMD0_rKqw9TXV":
                            channel_url = "Fvvvv"
                        elif channel_url == "https://t.me/joinchat/Hj7BrkUzUg1hZDM0":
                            channel_url = "zzzzzz"                                        
                        elif channel_url == "https://t.me/joinchat/4CSJU0YdgMRhN2My":
                            channel_url = "zz_mx"                                        
                            
                            
                        if "+" in channel_url:
                            result = await JoinChannelPrivate(client, channel_url)
                        else:
                            result = await JoinChannel(client, channel_url)
                    else:
                        break
            except Exception as error:
                print ("ERROR (1) :", error)
                if str(error).startswith('A wait of'):
                    banned_for = ((str(error).split("A wait of")[1]).split("seconds")[0]).strip()
                    await bot.send_message(entity=owner_id[0] ,message=f"**الرقم :** {phone}\n\n**محظور من ارسال الرسائل للبوت لمدة : {banned_for}**")
                elif str(error).startswith("cannot access local variable 'resp'"):
                    await bot.send_message(entity=owner_id[0] ,message=f'يبدو أن البوت لا يستجيب.. قد يكون محظور أو متوقف حاليا, سيتم ايقاف الجمع راجع البوت يدويا')

            try:
                # go to collect page
                click_collect = await resp.click(2)
                resp2 = await conv.get_edit()
                click_collect = await resp2.click(0)
            except Exception as error:
                print ("ERROR (2) :", error)
                if str(error).startswith("cannot access local variable 'resp'"):
                    await bot.send_message(entity=owner_id[0] ,message=f'يبدو أن البوت لا يستجيب.. قد يكون محظور أو متوقف حاليا, سيتم ايقاف الجمع راجع البوت يدويا')
            
            # collect now
            for x in range(10):
                if collect == False:
                    break
                
                # leave now
                if leave_joined_chats == True:
                    try:
                        if phone in leave_joined_chats_list:
                            leave_joined_chats_list.remove(phone)
                            chats_count = len(chats_joined.get(phone).get("joined"))                                        
                            await bot.send_message(entity=owner_id[0] ,message=f"**الرقم :** {phone}\n\n**بدأ الحساب بمغادرة القنوات و المجموعات, العدد : {chats_count}**")
                            
                            # leave now
                            for idx, channel in enumerate(chats_joined.get(phone).get("joined")):
                                try:
                                    await client(LeaveChannelRequest(channel=channel.get('channel_id')))
                                except Exception as error:
                                    if str(error).startswith('The target user is not a member'):
                                        pass
                                del chats_joined.get(phone).get("joined")[idx]
                            await bot.send_message(entity=owner_id[0] ,message=f"**الرقم :** {phone}\n\n**قام بمغادرة كل القنوات.. سيبدأ بالجمع**")
                            
                        if len(leave_joined_chats_list) == 0:
                            leave_joined_chats = False

                    except Exception as error:
                        pass
                        
                # get next message info
                channel_details = await conv.get_edit()
                    
                # join now
                channel_url = await fix_chat_id(channel_details.reply_markup.rows[0].buttons[0].url)
                if "+" in channel_url:
                    result = await JoinChannelPrivate(client, channel_url)
                else:
                    result = await JoinChannel(client, channel_url)
                    
                # check next move
                if result[0] == False:
                    if result[1] == False:
                        await channel_details.click(1)
                    else:
                        await bot.send_message(entity=owner_id[0] ,message=f"**الرقم :** {phone}\n\n**{result[1]}**")
                else:
                    # check inside bot
                    #await asyncio.sleep(0.3), 
                    await channel_details.click(2)

                    try:
                        # add joined channel to leftlist 24 hours
                        chat_id_joined = result[1].chats[0].id
                        
                        now = datetime.now()
                        Year, Month, Day, Hour, Min, Sec = now.strftime('%Y'), now.strftime('%m'), now.strftime('%d'), now.strftime('%H'), now.strftime('%M'), now.strftime('%S')
                        
                        TimeJoined = datetime(int(Year), int(Month), int(Day), int(Hour), int(Min), int(Sec))
                        leave_at = TimeJoined
                        
                        # add o list
                        never_leave = [1470407393, 1163877361, 1188306011]
                        if chat_id_joined not in never_leave:
                            chats_joined[phone]['joined'].append({'channel_id': chat_id_joined, 'leave_at': leave_at})
                    except Exception as error:
                        print ("ERROR (5) :", error)

    except Exception as error:
        if str(error) == " ":
            await bot.send_message(entity=owner_id[0] ,message=f"**الرقم :** {phone}\n\nالبوت لا يستجيب بسرعه. تم تخطي هذا الرقم, سيبدأ بالجمع مرة اخرى تلقائيا")
        elif str(error).startswith('Nobody is using this username'):
            await bot.send_message(entity=owner_id[0] ,message='يبدو أن هذا البوت محظور, تم ايقاف الجمع')

        elif str(error).startswith("cannot access local variable 'resp'"):
            await bot.send_message(entity=owner_id[0] ,message=f'يبدو أن البوت لا يستجيب.. قد يكون محظور أو متوقف حاليا, سيتم ايقاف الجمع راجع البوت يدويا')

        elif str(error) == "Cannot send requests while":
            await bot.send_message(entity=owner_id[0] ,message=f"**⚠️ الرقم :** {phone}\n\nهذا الرقم غير متصل, الحل.. قم بحذفه و اضافته مرة اخرى بعدها سيبدأ بالجمع عندما يصل دوره")

        await asyncio.sleep(1)
        print ("conversation (error) :", error)


bot.run_until_disconnected()