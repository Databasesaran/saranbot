import re
import logging
import asyncio

from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from pyrogram.errors import ButtonDataInvalid, FloodWait

from bot.database import Database # pylint: disable=import-error
from bot.bot import Bot # pylint: disable=import-error


FIND = {}
INVITE_LINK = {}
ACTIVE_CHATS = {}
db = Database()

@Bot.on_message(filters.text & filters.group, group=0)
async def auto_filter(bot, update):
    """
    A Funtion To Handle Incoming Text And Reply With Appropriate Results
    """
    group_id = update.chat.id

    if re.findall(r"((^\/|^,|^\.|^[\U0001F600-\U000E007F]).*)", update.text):
        return
    
    if ("https://" or "http://") in update.text:
        return
    
    query = re.sub(r"[1-2]\d{3}", "", update.text) # Targetting Only 1000 - 2999 😁
    
    if len(query) < 2:
        return
    
    results = []
    
    global ACTIVE_CHATS
    global FIND
    
    configs = await db.find_chat(group_id)
    achats = ACTIVE_CHATS[str(group_id)] if ACTIVE_CHATS.get(str(group_id)) else await db.find_active(group_id)
    ACTIVE_CHATS[str(group_id)] = achats
    
    if not configs:
        return
    
    allow_video = configs["types"]["video"]
    allow_audio = configs["types"]["audio"] 
    allow_document = configs["types"]["document"]
    
    max_pages = configs["configs"]["max_pages"] # maximum page result of a query
    pm_file_chat = configs["configs"]["pm_fchat"] # should file to be send from bot pm to user
    max_results = configs["configs"]["max_results"] # maximum total result of a query
    max_per_page = configs["configs"]["max_per_page"] # maximum buttom per page 
    show_invite = configs["configs"]["show_invite_link"] # should or not show active chat invite link
    
    show_invite = (False if pm_file_chat == True else show_invite) # turn show_invite to False if pm_file_chat is True
    
    filters = await db.get_filters(group_id, query)
    
    if filters:
        #results.append(
        #        [
        #            InlineKeyboardButton("⭕️ MAIN CHANNEL ⭕️", url="https://t.me/joinchat/4-Quex2FaFhjMDM1")
        #        ]
        #    ) 
        for filter in filters: # iterating through each files
            file_name = filter.get("file_name")
            file_type = filter.get("file_type")
            file_link = filter.get("file_link")
            file_size = int(filter.get("file_size", ""))
            file_size = round((file_size/1024),2) # from B to KB
            size = ""
            file_KB = ""
            file_MB = ""
            file_GB = ""
            
            if file_size < 1024:
                file_KB = f"[{str(round(file_size,2))} KB]"
                size = file_KB
            elif file_size < (1024*1024):
                file_MB = f"[{str(round((file_size/1024),2))} MB]"
                size = file_MB
            else:
                file_GB = f"[{str(round((file_size/(1024*1024)),2))} GB]"
                size = file_GB
                
            file_name = size + " 🎥 " + file_name
            
            print(file_name)
            #file_size = str(file_size) + " KB" if file_size < 1024 elif file_size < 1024 else str(round(file_size/1024)) + " GiB"  #"📁 " + 
            
            if file_type == "video":
                if allow_video: 
                    pass
                else:
                    continue
                
            elif file_type == "audio":
                if allow_audio:
                    pass
                else:
                    continue
                
            elif file_type == "document":
                if allow_document:
                    pass
                else:
                    continue
            
            if len(results) >= max_results:
                break
            
            if pm_file_chat: 
                unique_id = filter.get("unique_id")
                if not FIND.get("bot_details"):
                    try:
                        bot_= await bot.get_me()
                        FIND["bot_details"] = bot_
                    except FloodWait as e:
                        asyncio.sleep(e.x)
                        bot_= await bot.get_me()
                        FIND["bot_details"] = bot_
                
                bot_ = FIND.get("bot_details")
                file_link = f"https://t.me/{bot_.username}?start={unique_id}"
            
            
            
            results.append(
                [
                    InlineKeyboardButton(file_name, url=file_link)
                ]
            )
        #https://telegra.ph/file/f3ea3421859204e383b03.jpg
    else:
        Send_message=await bot.send_photo(
                chat_id=update.chat.id,
                photo="https://telegra.ph/file/eeed28e24189e59e6255c.jpg",
                caption=f"<b>നിങ്ങൾ ഉദ്ദേശിക്കുന്ന മൂവി ഏതാണ് എന്ന് എനിക്ക് 🙄അറിയാൻ കഴിയുന്നില്ല‌‌\nI do not know what movie you mean‌‌</b>\n\n<i>⚠️Just Send Me Movie/Series Name Without Spelling Mistake.Search Google To Get Currect Movie Name⚠️</i>\n"
                        f"<i>⭕️You can only get a movie if you hit the correct spelling of the movie‌‌</i>\n\n"
                        f"<b>Try to find a movie in👉 @On_air_Filter_bot </b>",
                parse_mode="html",
                reply_to_message_id=update.message_id
            )
        await asyncio.sleep(15) # in seconds
        await Send_message.delete()
        # await bot.delete_messages(update.chat.id,update.message_id)
        return  # return if no files found for that query
    
    if len(results) == 0:   # double check
        return
    
    else:
    
        result = []
        # seperating total files into chunks to make as seperate pages
        result += [results[i * max_per_page :(i + 1) * max_per_page ] for i in range((len(results) + max_per_page - 1) // max_per_page )]
        len_result = len(result)
        len_results = len(results)
        results = None   # Free Up Memory
        
        FIND[query] = {"results": result, "total_len": len_results, "max_pages": max_pages} # TrojanzHex's Idea Of Dicts😅

        # Add next buttin if page count is not equal to 1
        if len_result != 1:
            result[0].append(
                [
                    InlineKeyboardButton("Next 👉", callback_data=f"navigate(0|next|{query})")
                ]
            )
        
        # Just A Decaration
        result[0].append([
            InlineKeyboardButton(f"⭕️ Page 1/{len_result if len_result < max_pages else max_pages} ⭕️", callback_data="ignore")
        ])
        
        
        # if show_invite is True Append invite link buttons
        if show_invite:
            
            ibuttons = []
            achatId = []
            await gen_invite_links(configs, group_id, bot, update)
            
            for x in achats["chats"] if isinstance(achats, dict) else achats:
                achatId.append(int(x["chat_id"])) if isinstance(x, dict) else achatId.append(x)

            ACTIVE_CHATS[str(group_id)] = achatId
            
            for y in INVITE_LINK.get(str(group_id)):
                
                chat_id = int(y["chat_id"])
                
                if chat_id not in achatId:
                    continue
                
                chat_name = y["chat_name"]
                invite_link = y["invite_link"]
                
                if ((len(ibuttons)%2) == 0):
                    ibuttons.append(
                        [
                            InlineKeyboardButton(f"⚜ {chat_name} ⚜", url=invite_link)
                        ]
                    )

                else:
                    ibuttons[-1].append(
                        InlineKeyboardButton(f"⚜ {chat_name} ⚜", url=invite_link)
                    )
                
            for x in ibuttons:
                result[0].insert(0, x) #Insert invite link buttons at first of page
                
            ibuttons = None     # Free Up Memory...
            achatId = None
        
        ibuttonss = []
        ibuttonss.append(
                        [
                            InlineKeyboardButton("🎬 📌click and share📌 🎬", url="https://telegram.me/share/url?url=t.me/joinchat/q4xMr02fvA9jNzQ1")
                        ]
                    )
        for x in ibuttonss:
                result[0].insert(0, x) #Insert invite link buttons at first of page
        
        reply_markup = InlineKeyboardMarkup(result[0])

        try:
            await bot.send_photo(
                chat_id=update.chat.id,
                photo="https://telegra.ph/file/9075ca7cbad944afaa823.jpg",
                caption=f"<b>🎬 ᴍᴏᴠɪᴇ ɴᴀᴍᴇ :</b> <code><b><i>{query}</i></b></code>\n"
                        f"<b>🔺 𝙽𝙾 𝙾𝙵 𝙵𝙸𝙻𝙴𝚂 : </b> <code><b><i>{len_results}</i></b></code>\n"
                        f"<b>🧞‍♂️ 𝚁𝚎𝚚𝚞𝚎𝚜𝚝𝚎𝚍 𝙱𝚢 :</b> <b><code>{update.from_user.first_name}</code></b>\n\n<b>👮‍♂️ ⁱᶠ ʸᵒᵘ ᵈᵒⁿ'ᵗ ˢᵉᵉ ᵗʰᵉ ᶠⁱˡᵉˢ ᵒᶠ ᵗʰᵉ ᵐᵒᵛⁱᵉ ʸᵒᵘ ᵃˢᵏᵉᵈ ᶠᵒʳ 👀ˡᵒᵒᵏ ᵃᵗ ⁿᵉˣᵗ ᵖᵃᵍᵉ </b>",
                reply_markup=reply_markup,
                parse_mode="html",
                reply_to_message_id=update.message_id
            )
            # await bot.send_message(
            #     chat_id = update.chat.id,
            #     text=f"We Found <code><b><i>{len_results}</i></b></code> "
            #          f"Results For Your Query: <code><b><i>{query}</i></b></code>, "
            #          f"Requested By <b><code>{update.from_user.first_name}</code></b>",
            #     reply_markup=reply_markup,
            #     parse_mode="html",
            #     reply_to_message_id=update.message_id
            # )

        except ButtonDataInvalid:
            print(result[0])
        
        except Exception as e:
            print(e)


async def gen_invite_links(db, group_id, bot, update):
    """
    A Funtion To Generate Invite Links For All Active 
    Connected Chats In A Group
    """
    chats = db.get("chat_ids")
    global INVITE_LINK
    
    if INVITE_LINK.get(str(group_id)):
        return
    
    Links = []
    if chats:
        for x in chats:
            Name = x["chat_name"]
            
            if Name == None:
                continue
            
            chatId=int(x["chat_id"])
            
            Link = await bot.export_chat_invite_link(chatId)
            Links.append({"chat_id": chatId, "chat_name": Name, "invite_link": Link})

        INVITE_LINK[str(group_id)] = Links
    return 


async def recacher(group_id, ReCacheInvite=True, ReCacheActive=False, bot=Bot, update=Message):
    """
    A Funtion To rechase invite links and active chats of a specific chat
    """
    global INVITE_LINK, ACTIVE_CHATS

    if ReCacheInvite:
        if INVITE_LINK.get(str(group_id)):
            INVITE_LINK.pop(str(group_id))
        
        Links = []
        chats = await db.find_chat(group_id)
        chats = chats["chat_ids"]
        
        if chats:
            for x in chats:
                Name = x["chat_name"]
                chat_id = x["chat_id"]
                if (Name == None or chat_id == None):
                    continue
                
                chat_id = int(chat_id)
                
                Link = await bot.export_chat_invite_link(chat_id)
                Links.append({"chat_id": chat_id, "chat_name": Name, "invite_link": Link})

            INVITE_LINK[str(group_id)] = Links
    
    if ReCacheActive:
        
        if ACTIVE_CHATS.get(str(group_id)):
            ACTIVE_CHATS.pop(str(group_id))
        
        achats = await db.find_active(group_id)
        achatId = []
        if achats:
            for x in achats["chats"]:
                achatId.append(int(x["chat_id"]))
            
            ACTIVE_CHATS[str(group_id)] = achatId
    return
