import logging
import random
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InlineQueryResultArticle,
    InputTextMessageContent,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    InlineQueryHandler,
    ContextTypes,
)

# Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

# Active Games Dictionary {chat_id: GameSession}
GAMES = {}

def generate_domino_deck():
    """Double-Six Dominoes တုံး ၂၈ တုံး ထုတ်လုပ်ခြင်း"""
    deck = []
    for i in range(7):
        for j in range(i, 7):
            deck.append((i, j))
    random.shuffle(deck)
    return deck

class DominoGame:
    def __init__(self, chat_id):
        self.chat_id = chat_id
        self.deck = generate_domino_deck()
        self.board = []       # ဘုတ်ပေါ်မှ တုံးများ [(a,b), (b,c)]
        self.players = []     # Player ID များ [id1, id2, ...]
        self.player_names = {}# {id: name}
        self.hands = {}       # {id: [(a,b), ...]}
        self.turn_index = 0
        self.started = False
        self.drawn_this_turn = False # ယခုအလှည့်တွင် တုံးဆွဲပြီးပြီလား

    def get_current_player_id(self):
        return self.players[self.turn_index]

    def get_ends(self):
        """ဘုတ်၏ ဘယ်ဘက်နှင့် ညာဘက် အစွန်းနံပါတ်များကို ထုတ်ပေးခြင်း"""
        if not self.board:
            return None, None
        return self.board[0][0], self.board[-1][1]

    def can_play_tile(self, tile):
        """တုံးတစ်ခုသည် ဘုတ်ပေါ်တွင် ချ၍ရ/မရ စစ်ဆေးခြင်း"""
        if not self.board:
            return True
        left_end, right_end = self.get_ends()
        return tile[0] in (left_end, right_end) or tile[1] in (left_end, right_end)

    def next_turn(self):
        self.turn_index = (self.turn_index + 1) % len(self.players)
        self.drawn_this_turn = False

# --- Telegram Handlers ---

async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🀀 **Dominoes Game Bot မှ ကြိုဆိုပါတယ်!**\n\n"
        "🎮 ဂိမ်းစတင်ရန်: /new\n"
        "📥 ပါဝင်ရန်: /join\n"
        "🚀 စကစားရန်: /startgame\n"
        "❌ ပွဲဖျက်ရန်: /kill",
        parse_mode="Markdown"
    )

async def new_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    GAMES[chat_id] = DominoGame(chat_id)
    
    # ဆောက်သည့်သူကို တန်း Join စေခြင်း
    user = update.effective_user
    GAMES[chat_id].players.append(user.id)
    GAMES[chat_id].player_names[user.id] = user.first_name

    await update.message.reply_text(
        f"🎲 **Dominoes ပွဲသစ် စတင်လိုက်ပါပြီ!**\n\n"
        f"ပါဝင်သူ: {user.first_name}\n"
        f"အခြားသူများ /join နှိပ်၍ ဝင်ရောက်နိုင်ပါသည်။",
        parse_mode="Markdown"
    )

async def join_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = update.effective_user

    if chat_id not in GAMES:
        await update.message.reply_text("လက်ရှိ ပွဲမရှိသေးပါ။ /new နှိပ်၍ စတင်ပါ။")
        return

    game = GAMES[chat_id]
    if game.started:
        await update.message.reply_text("ဂိမ်း စတင်နေပြီဖြစ်၍ ဝင်ရောက်၍ မရတော့ပါ။")
        return

    if user.id in game.players:
        await update.message.reply_text("သင် ဂိမ်းထဲတွင် ရှိပြီးသားပါ။")
        return

    if len(game.players) >= 4:
        await update.message.reply_text("ကစားသမား ၄ ယောက် ပြည့်သွားပါပြီ။")
        return

    game.players.append(user.id)
    game.player_names[user.id] = user.first_name
    await update.message.reply_text(f"👤 {user.first_name} ဂိမ်းထဲ ဝင်ရောက်လာခဲ့ပါပြီ! (စုစုပေါင်း: {len(game.players)} ယောက်)")

async def startgame_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id not in GAMES:
        return

    game = GAMES[chat_id]
    if len(game.players) < 2:
        await update.message.reply_text("အနည်းဆုံး ကစားသမား ၂ ယောက် လိုအပ်ပါသည်။")
        return

    # ဝေငှခြင်း (၁ ယောက်လျှင် ၇ တုံး)
    for p_id in game.players:
        game.hands[p_id] = [game.deck.pop() for _ in range(7)]

    game.started = True

    # စတင်တုံးကို အလယ်တွင် ချခြင်း
    first_tile = game.deck.pop()
    game.board.append(first_tile)

    current_player_id = game.get_current_player_id()
    current_player_name = game.player_names[current_player_id]

    # UI Display
    board_str = f"[{first_tile[0]}|{first_tile[1]}]"
    text = (
        f"🀀 **First Tile:** {board_str}\n\n"
        f"First player: [{current_player_name}](tg://user?id={current_player_id})"
    )

    keyboard = [[InlineKeyboardButton("Make your choice!", switch_inline_query_current_chat="")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")

# --- Inline Query Handler (ကဒ်ပြသခြင်းနှင့် ရွေးချယ်ခြင်း) ---
async def inline_query_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.inline_query
    user_id = query.from_user.id

    # ကစားနေသော Game Session ရှာခြင်း
    active_game = None
    for g in GAMES.values():
        if g.started and user_id in g.players:
            active_game = g
            break

    results = []

    if not active_game:
        results.append(
            InlineQueryResultArticle(
                id="no_game",
                title="❌ သင် လက်ရှိ ဂိမ်းထဲတွင် မရှိပါ",
                input_message_content=InputTextMessageContent("သင် လက်ရှိ ဂိမ်းထဲတွင် မရှိပါ။")
            )
        )
        await query.answer(results, cache_time=1)
        return

    # မိမိ အလှည့် မဟုတ်ပါက
    if active_game.get_current_player_id() != user_id:
        results.append(
            InlineQueryResultArticle(
                id="not_your_turn",
                title="⏳ သင့်အလှည့် မဟုတ်သေးပါ",
                input_message_content=InputTextMessageContent("သင့်အလှည့် ရောက်မှ တုံးချပါ။")
            )
        )
        await query.answer(results, cache_time=1)
        return

    hand = active_game.hands[user_id]
    left_end, right_end = active_game.get_ends()

    # 1. တုံးဆွဲရန် / Pass ခလုတ်များ
    if not active_game.drawn_this_turn:
        # မေးခွန်းသင်္ကေတ ? (Draw)
        results.append(
            InlineQueryResultArticle(
                id="draw_tile",
                title="❓ Draw Tile (တုံးအသစ် ကောက်မည်)",
                description=f"Deck ထဲတွင် {len(active_game.deck)} တုံး ကျန်သေးသည်",
                input_message_content=InputTextMessageContent("/draw_action")
            )
        )
    else:
        # လူနှစ်ယောက်ပုံ (Pass)
        results.append(
            InlineQueryResultArticle(
                id="pass_turn",
                title="👤➡️👤 Pass Turn (အလှည့် ကျော်မည်)",
                description="ဆွဲလိုက်သော တုံးလည်း ချ၍ မရပါက အလှည့် ကျော်ပါ",
                input_message_content=InputTextMessageContent("/pass_action")
            )
        )

    # 2. လက်ထဲရှိ Dominoes တုံးများ ပြသခြင်း
    for idx, tile in enumerate(hand):
        can_play = active_game.can_play_tile(tile)
        status = "✅ ချ၍ရသည်" if can_play else "🚫 ချ၍မရပါ"
        
        results.append(
            InlineQueryResultArticle(
                id=f"tile_{idx}_{tile[0]}_{tile[1]}",
                title=f"🀀 [{tile[0]} | {tile[1]}] - {status}",
                input_message_content=InputTextMessageContent(f"/play_tile {idx}")
            )
        )

    await query.answer(results, cache_time=1)

# --- Play / Draw / Pass Commands Processing ---

async def handle_play_tile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    if chat_id not in GAMES or not GAMES[chat_id].started:
        return

    game = GAMES[chat_id]
    if game.get_current_player_id() != user_id:
        return

    try:
        tile_idx = int(context.args[0])
        tile = game.hands[user_id][tile_idx]
    except Exception:
        return

    if not game.can_play_tile(tile):
        await update.message.reply_text("❌ ထိုတုံးသည် ဘုတ်ပေါ်တွင် ချ၍ မရပါ။")
        return

    # တုံးချခြင်း Logic
    left_end, right_end = game.get_ends()
    a, b = tile

    # ဘုတ်ထဲသို့ ထည့်ခြင်း
    if a == right_end:
        game.board.append((a, b))
    elif b == right_end:
        game.board.append((b, a))
    elif a == left_end:
        game.board.insert(0, (b, a))
    elif b == left_end:
        game.board.insert(0, (a, b))

    # လက်ထဲမှ တုံးထုတ်ခြင်း
    game.hands[user_id].pop(tile_idx)

    # နိုင်/မနိုင် စစ်ဆေးခြင်း
    if len(game.hands[user_id]) == 0:
        await update.message.reply_text(f"🎉 **{game.player_names[user_id]} အနိုင်ရရှိသွားပါပြီ!** 🏆")
        del GAMES[chat_id]
        return

    # Next Turn
    game.next_turn()
    await send_next_turn_message(update, context, game)

async def handle_draw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    game = GAMES.get(chat_id)

    if not game or game.get_current_player_id() != user_id:
        return

    if len(game.deck) == 0:
        await update.message.reply_text("❌ Deck ထဲတွင် တုံးများ ကုန်သွားပါပြီ။ Pass နှိပ်ပါ။")
        return

    drawn_tile = game.deck.pop()
    game.hands[user_id].append(drawn_tile)
    game.drawn_this_turn = True

    await update.message.reply_text(
        f"📥 {game.player_names[user_id]} တုံးအသစ် ၁ တုံး ဆွဲလိုက်ပါပြီ။\n"
        f"**Make your choice!** ကို ပြန်နှိပ်၍ စစ်ဆေးပါ။",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Make your choice!", switch_inline_query_current_chat="")]])
    )

async def handle_pass(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    game = GAMES.get(chat_id)

    if not game or game.get_current_player_id() != user_id:
        return

    game.next_turn()
    await send_next_turn_message(update, context, game)

async def send_next_turn_message(update, context, game):
    board_str = " ".join([f"[{t[0]}|{t[1]}]" for t in game.board])
    current_player_id = game.get_current_player_id()
    current_player_name = game.player_names[current_player_id]

    text = (
        f"📋 **Board:** {board_str}\n\n"
        f"Next turn: [{current_player_name}](tg://user?id={current_player_id})"
    )
    keyboard = [[InlineKeyboardButton("Make your choice!", switch_inline_query_current_chat="")]]
    await context.bot.send_message(
        chat_id=game.chat_id,
        text=text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

# --- Main App ---
if __name__ == "__main__":
    BOT_TOKEN = "8988526962:AAGdIJbT8Bg4KpI270mlt8JlS5mLvPS6eMM"  # @BotFather မှ Token ထည့်ပါ

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("new", new_cmd))
    app.add_handler(CommandHandler("join", join_cmd))
    app.add_handler(CommandHandler("startgame", startgame_cmd))
    app.add_handler(CommandHandler("play_tile", handle_play_tile))
    app.add_handler(CommandHandler("draw_action", handle_draw))
    app.add_handler(CommandHandler("pass_action", handle_pass))
    app.add_handler(InlineQueryHandler(inline_query_handler))

    print("Bot is running...")
    app.run_polling()
