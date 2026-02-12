import re
import asyncio
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ChatPermissions
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.enums.chat_member_status import ChatMemberStatus

# ===== НАСТРОЙКИ =====
BOT_TOKEN = "8232445082:AAGhkxdf_DvBx4d5BWlILynrzif5uVYgLXQ"
MUTE_DURATION_MINUTES = 40
# =====================

# ===== СЕЛЬСКИЙ ФИЛЬТР =====
VILLAGE_TRIGGERS = ["сельский", "село", "селавый", "деревня", "сило", "силоо", "силооо"]
VILLAGE_RESPONSE = "ыыы силооо сельский 😕🧐😝😟😝😕😜😕селавый деревня 😕🤩😟😝😟😝😟😕как ти живещдщщщ 🧐😍😜🙂🤓🙂🧐🙃🤓🙃😎🙁алио умри😙🤓😍🧐🤩🙂🤩🙂🥳🤓голубинная почта 😃🙄🤓🤓😎😌🥳силоооо😢🤑😄🙄😊ыыыы затролел🥵🥺🥵🥵🥺😨🥺😓😣😓"
# ============================

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

# Регулярные выражения
TG_CHANNEL_LINK_PATTERN = r'(https?://)?(www\.)?(t\.me|telegram\.me|telegram\.dog)/[a-zA-Z0-9_]+'
ANY_LINK_PATTERN = r'(https?://|www\.)[^\s]+'
MENTION_PATTERN = r'@(\w+)'

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "👮‍♂️ <b>kirill_dalbaeb</b> - бот защиты\n\n"
        "<b>Добавьте меня в группу и сделайте админом!</b>"
    )

@dp.message(Command("unmute"))
async def cmd_unmute(message: types.Message):
    """Команда для размута пользователя"""
    if message.chat.type not in ["group", "supergroup"]:
        await message.answer("❌ Эта команда работает только в группах!")
        return
    
    try:
        bot_member = await message.chat.get_member(bot.id)
        if bot_member.status != ChatMemberStatus.ADMINISTRATOR:
            await message.answer("⚠️ Я не администратор! Выдайте права для работы.")
            return
        
        user_member = await message.chat.get_member(message.from_user.id)
        if user_member.status not in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.CREATOR]:
            await message.answer("❌ Только администраторы могут использовать эту команду!")
            return
        
        user_to_unmute = None
        
        if message.reply_to_message:
            user_to_unmute = message.reply_to_message.from_user
        elif len(message.text.split()) > 1:
            username = message.text.split()[1]
            if username.startswith('@'):
                username = username[1:]
            try:
                chat_member = await bot.get_chat_member(message.chat.id, username)
                user_to_unmute = chat_member.user
            except:
                await message.answer("❌ Пользователь не найден в этом чате!")
                return
        else:
            await message.answer(
                "❌ Укажите пользователя!\n\n"
                "Использование:\n"
                "• /unmute - ответом на сообщение\n"
                "• /unmute @username"
            )
            return
        
        permissions = ChatPermissions(
            can_send_messages=True,
            can_send_media_messages=True,
            can_send_polls=True,
            can_send_other_messages=True,
            can_add_web_page_previews=True,
            can_change_info=False,
            can_invite_users=False,
            can_pin_messages=False
        )
        
        await bot.restrict_chat_member(
            chat_id=message.chat.id,
            user_id=user_to_unmute.id,
            permissions=permissions
        )
        
        await message.answer(
            f"🔓 <b>Пользователь размучен</b>\n"
            f"👤 {user_to_unmute.mention_html(user_to_unmute.full_name)}\n"
            f"👮‍♂️ Администратор: {message.from_user.mention_html(message.from_user.full_name)}"
        )
        
    except Exception as e:
        await message.answer(f"❌ Ошибка при размуте: {str(e)[:100]}")

async def is_channel(username: str) -> bool:
    """
    Проверяет, является ли @username каналом
    """
    try:
        chat = await bot.get_chat(f"@{username}")
        return chat.type in ["channel", "supergroup"]
    except:
        return False

@dp.message()
async def check_for_spam(message: types.Message):
    """
    Проверяет сообщение на наличие:
    - Ссылок на Telegram каналы
    - Любых внешних ссылок
    - Упоминаний КАНАЛОВ
    - Слова "сельский"/"село"
    """
    if not message.text or message.text.startswith('/'):
        return
    
    if message.from_user and message.from_user.id == bot.id:
        return
    
    if message.chat.type not in ["group", "supergroup"]:
        return
    
    # ===== СЕЛЬСКИЙ ФИЛЬТР =====
    text_lower = message.text.lower()
    for trigger in VILLAGE_TRIGGERS:
        if trigger in text_lower:
            await message.reply(VILLAGE_RESPONSE)
            break
    # ============================
    
    try:
        bot_member = await message.chat.get_member(bot.id)
        if bot_member.status != ChatMemberStatus.ADMINISTRATOR:
            return
        
        user_member = await message.chat.get_member(message.from_user.id)
        if user_member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.CREATOR]:
            return
        
        # Проверяем наличие ссылок
        has_link = re.search(ANY_LINK_PATTERN, message.text, re.IGNORECASE)
        has_tg_link = re.search(TG_CHANNEL_LINK_PATTERN, message.text, re.IGNORECASE)
        
        # Ищем все упоминания @username в тексте
        mentions = re.findall(MENTION_PATTERN, message.text)
        
        # Проверяем каждое упоминание - является ли оно каналом
        channel_mentions = []
        for mention in mentions:
            if await is_channel(mention):
                channel_mentions.append(f"@{mention}")
        
        # Если есть что-то из списка - мутим
        if has_link or has_tg_link or channel_mentions:
            
            permissions = ChatPermissions(
                can_send_messages=False,
                can_send_media_messages=False,
                can_send_polls=False,
                can_send_other_messages=False,
                can_add_web_page_previews=False,
                can_change_info=False,
                can_invite_users=False,
                can_pin_messages=False
            )
            
            mute_until = datetime.now() + timedelta(minutes=MUTE_DURATION_MINUTES)
            
            # Определяем причину
            if channel_mentions:
                reason = f"упоминание канала(ов): {', '.join(channel_mentions)}"
            elif has_tg_link:
                reason = "ссылка на Telegram канал"
            else:
                reason = "внешняя ссылка"
            
            try:
                await bot.restrict_chat_member(
                    chat_id=message.chat.id,
                    user_id=message.from_user.id,
                    permissions=permissions,
                    until_date=int(mute_until.timestamp())
                )
                
                await message.delete()
                
                notification = (
                    f"🔇 <b>Пользователь замучен</b>\n"
                    f"👤 {message.from_user.mention_html(message.from_user.full_name)}\n"
                    f"⏱ Длительность: {MUTE_DURATION_MINUTES} минут\n"
                    f"📝 Причина: Далбаеб ебаны\n"
                    f"🆘 Для размута: /unmute (только админы)"
                )
                
                await message.answer(notification)
                
            except Exception as mute_error:
                print(f"Ошибка при муте: {mute_error}")
                
    except Exception as e:
        print(f"Общая ошибка: {e}")

async def main():
    print("🚀 Бот kirill_dalbaeb запущен...")
    print("🤖 Автоматически определяю каналы и людей!")
    print("🔇 Мут за: ссылки + упоминания каналов")
    print("🌾 Сельский фильтр: АКТИВИРОВАН")
    print("✅ Игнорирую: упоминания людей")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())