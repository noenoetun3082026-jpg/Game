import logging
import random
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InlineQueryResultCachedSticker,
    InlineQueryResultArticle,
    InputTextMessageContent,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    InlineQueryHandler,
    ContextTypes,
)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

GAMES = {}

# ==============================================================================
# STICKER / CUSTOM EMOJI ID MAPPING
# ==============================================================================
DRAW_STICKER_ID = "5463122435425448565" # ❓ (Draw)
PASS_STICKER_ID = "6035380708258615873" # 👤➡👤 (Pass)

STICKER_MAP = {
    (0, 0): "6188005828570654010",
    (0, 1): "6188447716280901762",
    (0, 2): "6188186105527935336",
    (0, 3): "6188506475728479411",
    (0, 4): "6188225898399933672",
    (0, 5): "6188488058908713098",
    (0, 6): "6188171369495145043",
    (1, 1): "6188425807652724648",
    (1, 2): "6188226967846789688",
    (1, 3): "6188423887802343909",
    (1, 4): "6188089129461359082",
    (1, 5): "6187988708831011056",
    (1, 6): "6188144830892229730",
    (2, 2): "6188283425191895933",
    (2, 3): "6188043645757694691",
    (2, 4): "6188461756528992061",
    (2, 5): "6188187750500409617",
    (2, 6): "6188259755627126691",
    (3, 3): "6188196847241142337",
    (3, 4): "6188274126587701177",
    (3, 5): "6188013250274141249",
    (3, 6): "6188072095621062797",
    (4, 4): "6188105665085449320",
    (4, 5): "6188243829888393548",
    (4, 6): "6190672260232127599",
    (5, 5): "6188383772807799235",
    (5, 6): "6188171833351610799",
    (6, 6): "6188251681088612074",
}

def get_sticker_id(tile):
    key = tuple(sorted(tile))
    return STICKER_MAP.get(key)

def generate_domino_deck():
    deck = []
    for i in range(7):
        for j in range(i, 7):
            deck.append((i, j))
    random.shuffle(deck)
    return deck

class DominoGame:
    def __init__(self, chat_id, owner_id):
        self.chat_id = chat_id
        self.owner_id = owner_id
        self.deck = generate_domino_deck()
        self.board = []
        self.players = []
        self.player_names = {}
        self.hands = {}
        self.turn_index = 0
        self.started = False
        self.is_closed = False
        self.drawn_this_turn = False

    def get_current_player_id(self):
        return self.players[self.turn_index] if self.players else None

    def get_ends(self):
        if not self.board:
            return None, None
        return self.board[0][0], self.board[-1][1]

    def can_play_tile(self, tile):
        if not self.board:
            return True
        left_end, right_end = self.get_ends()
        return tile[0] in (left_end, right_end) or tile[1] in (left_end, right_end)

    def next_turn(self):
        self.turn_index = (self.turn_index + 1) % len(self.players)
        self.drawn_this_turn = False

# --- Telegram Commands ---

async def new_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = update.effective_user

    display_name = f"@{user.username}" if user.username else user.first_name

    GAMES[chat_id] = DominoGame(chat_id, user.id)
    GAMES[chat_id].players.append(user.id)
    GAMES[chat_id].player_names[user.id] = display_name

    await update.message.reply_text(
        f"Created a new game! Join the game with /join and start the game with /start"
    )

async def join_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = update.effective_user

    if chat_id not in GAMES:
        await update.message.reply_text("No game running. Create one with /new")
        return

    game = GAMES[chat_id]
    if game.is_closed:
        await update.message.reply_text("The game lobby is closed.")
        return
    if game.started:
        await update.message.reply_text("The game has already started.")
        return
    if user.id in game.players:
        await update.message.reply_text("You already joined!")
        return

    display_name = f"@{user.username}" if user.username else user.first_name
    game.players.append(user.id)
    game.player_names[user.id] = display_name
    await update.message.reply_text(f"{display_name} joined the game!")

async def start_game_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id not in GAMES:
        await update.message.reply_text("No game created. Use /new first.")
        return

    game = GAMES[chat_id]
    if game.started:
        await update.message.reply_text("Game is already running.")
        return
    if len(game.players) < 2:
        await update.message.reply_text("Need at least 2 players to start!")
        return

    for p_id in game.players:
        game.hands[p_id] = [game.deck.pop() for _ in range(7)]

    game.started = True
    first_tile = game.deck.pop()
    game.board.append(first_tile)

    current_id = game.get_current_player_id()
    name = game.player_names[current_id]

    text = (
        f"First player: {name}\n"
        f"Initial tile: [{first_tile[0]}|{first_tile[1]}]\n\n"
        f"Use /close to stop people from joining the game."
    )
    keyboard = [[InlineKeyboardButton("Make your choice!", switch_inline_query_current_chat="")]]
    
    first_sticker = get_sticker_id(first_tile)
    if first_sticker:
        try:
            await update.message.reply_sticker(first_sticker)
        except Exception:
            pass

    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def leave_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = update.effective_user
    game = GAMES.get(chat_id)

    if not game or user.id not in game.players:
        await update.message.reply_text("You are not in a game.")
        return

    if game.started:
        await update.message.reply_text("You cannot leave a running game. Use /kill to end it.")
        return

    game.players.remove(user.id)
    name = game.player_names.pop(user.id, user.first_name)
    await update.message.reply_text(f"{name} left the game.")

async def close_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    game = GAMES.get(update.effective_chat.id)
    if game:
        game.is_closed = True
        await update.message.reply_text("Game lobby is now closed.")

async def open_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    game = GAMES.get(update.effective_chat.id)
    if game:
        game.is_closed = False
        await update.message.reply_text("Game lobby is now open.")

async def kill_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id in GAMES:
        del GAMES[chat_id]
        await update.message.reply_text("Game terminated.")
    else:
        await update.message.reply_text("No game running.")

async def skip_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    game = GAMES.get(update.effective_chat.id)
    if game and game.started:
        current_name = game.player_names[game.get_current_player_id()]
        game.next_turn()
        await update.message.reply_text(f"Skipped {current_name}'s turn.")
        await send_next_turn_message(context, game)

async def kick_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    game = GAMES.get(update.effective_chat.id)
    if not game or update.effective_user.id != game.owner_id:
        return

    if context.args:
        try:
            target_id = int(context.args[0])
            if target_id in game.players:
                game.players.remove(target_id)
                await update.message.reply_text("Player kicked.")
        except Exception:
            pass

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("How to play: Join game, click 'Make your choice!' button to play your matching domino tile.")

async def stats_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Statistics feature coming soon!")

# --- Inline Query Handler ---

async def inline_query_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.inline_query
    user_id = query.from_user.id

    active_game = None
    for g in GAMES.values():
        if g.started and user_id in g.players:
            active_game = g
            break

    results = []
    if not active_game or active_game.get_current_player_id() != user_id:
        results.append(
            InlineQueryResultArticle(
                id="not_turn",
                title="⏳ Not your turn!",
                input_message_content=InputTextMessageContent("It's not your turn!")
            )
        )
        await query.answer(results, cache_time=1)
        return

    hand = active_game.hands[user_id]

    # DRAW သို့မဟုတ် PASS ခလုတ်
    if len(active_game.deck) > 0 and not active_game.drawn_this_turn:
        results.append(
            InlineQueryResultCachedSticker(
                id="draw_action",
                sticker_file_id=DRAW_STICKER_ID,
                input_message_content=InputTextMessageContent("/draw_action")
            )
        )
    else:
        results.append(
            InlineQueryResultCachedSticker(
                id="pass_action",
                sticker_file_id=PASS_STICKER_ID,
                input_message_content=InputTextMessageContent("/pass_action")
            )
        )

    for idx, tile in enumerate(hand):
        sticker_id = get_sticker_id(tile)
        if sticker_id:
            results.append(
                InlineQueryResultCachedSticker(
                    id=f"tile_{idx}",
                    sticker_file_id=sticker_id,
                    input_message_content=InputTextMessageContent(f"/play_tile {idx}")
                )
            )

    await query.answer(results, cache_time=1)

# --- Action Handlers ---

async def handle_play_tile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    game = GAMES.get(chat_id)

    if not game or not game.started or game.get_current_player_id() != user_id:
        return

    try:
        tile_idx = int(context.args[0])
        tile = game.hands[user_id][tile_idx]
    except Exception:
        return

    if not game.can_play_tile(tile):
        await update.message.reply_text("❌ ဒီအတုံးကို ချလို့မရပါဘူး! ဘုတ်ပေါ်က အစွန်းနဲ့ မကိုက်ညီပါဘူး။")
        return

    left_end, right_end = game.get_ends()
    a, b = tile

    if a == right_end:
        game.board.append((a, b))
    elif b == right_end:
        game.board.append((b, a))
    elif b == left_end:
        game.board.insert(0, (a, b))
    elif a == left_end:
        game.board.insert(0, (b, a))

    played_sticker = get_sticker_id(tile)
    game.hands[user_id].pop(tile_idx)

    if played_sticker:
        try:
            await update.message.reply_sticker(played_sticker)
        except Exception:
            pass

    if len(game.hands[user_id]) == 0:
        await update.message.reply_text(f"🎉 {game.player_names[user_id]} အနိုင်ရသွားပါပြီ! 🏆")
        del GAMES[chat_id]
        return

    game.next_turn()
    await send_next_turn_message(context, game)

async def handle_draw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    game = GAMES.get(chat_id)

    if not game or game.get_current_player_id() != user_id:
        return

    if len(game.deck) == 0:
        await update.message.reply_text("ဆွဲစရာ ကဒ် မရှိတော့ပါဘူး။ Pass ကို နှိပ်ပါ။")
        return

    drawn_tile = game.deck.pop()
    game.hands[user_id].append(drawn_tile)
    game.drawn_this_turn = True

    await update.message.reply_text(
        f"{game.player_names[user_id]} ကဒ်တစ်ကဒ် ဆွဲလိုက်ပါတယ်။\n'Make your choice!' ကို ပြန်နှိပ်ပြီး ချပါ သို့မဟုတ် Pass လုပ်ပါ။",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Make your choice!", switch_inline_query_current_chat="")]])
    )

async def handle_pass(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    game = GAMES.get(chat_id)

    if not game or game.get_current_player_id() != user_id:
        return

    current_name = game.player_names[user_id]
    game.next_turn()
    await update.message.reply_text(f"⏩ {current_name} အလှည့်ကျော် (Pass) လုပ်လိုက်ပါတယ်။")
    await send_next_turn_message(context, game)

async def send_next_turn_message(context, game):
    board_str = " ".join([f"[{t[0]}|{t[1]}]" for t in game.board])
    current_id = game.get_current_player_id()
    name = game.player_names[current_id]

    text = (
        f"Board: {board_str}\n\n"
        f"Next player: {name}"
    )
    keyboard = [[InlineKeyboardButton("Make your choice!", switch_inline_query_current_chat="")]]
    await context.bot.send_message(
        chat_id=game.chat_id,
        text=text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

if __name__ == "__main__":
    import os
    BOT_TOKEN = os.environ.get("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("new", new_cmd))
    app.add_handler(CommandHandler("join", join_cmd))
    app.add_handler(CommandHandler("start", start_game_cmd))
    app.add_handler(CommandHandler("leave", leave_cmd))
    app.add_handler(CommandHandler("close", close_cmd))
    app.add_handler(CommandHandler("open", open_cmd))
    app.add_handler(CommandHandler("kill", kill_cmd))
    app.add_handler(CommandHandler("skip", skip_cmd))
    app.add_handler(CommandHandler("kick", kick_cmd))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("stats", stats_cmd))

    app.add_handler(CommandHandler("play_tile", handle_play_tile))
    app.add_handler(CommandHandler("draw_action", handle_draw))
    app.add_handler(CommandHandler("pass_action", handle_pass))

    app.add_handler(InlineQueryHandler(inline_query_handler))

    app.run_polling()
