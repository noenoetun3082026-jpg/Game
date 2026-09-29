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
# 🎯 CORRECTED STICKER FILE ID MAPPING (အမှတ်နှင့် စတစ်ကာ ID တိကျစွာ Mapping လုပ်ထားသည်)
# ==============================================================================
DRAW_STICKER_ID = "CAACAgIAAxkBAAER95pqu8twsjF5O8hhtNFV-w8UThc37gAC7CgAAjPGKUjt4hLF81JA6D0E" # ? (Draw)
PASS_STICKER_ID = "CAACAgIAAxkBAAER95tqu8twG9aoGiJa5OLWasXZQuC_9gACozEAAp2mKEjmlX9mPoG7ZD0E" # 👤➡️️👤 (Pass)

STICKER_MAP = {
    (0, 0): "CAACAgIAAxkBAAER935qu8twVcl764Y0UWYM6rCBcwhLgQACNy0AAgOcKEivdNWrUipUpD0E",
    (0, 1): "CAACAgIAAxkBAAER939qu8twCWrLrA93EBlvw4z0Smm4-gAChCIAAqeRKEgTAAEWOhiabFQ9BA",
    (0, 2): "CAACAgIAAxkBAAER94Bqu8twgIDTDb7sgkOI1EY2pRbkjQACxSoAAzkpSBfcTTva3k2yPQQ",
    (0, 3): "CAACAgIAAxkBAAER94Fqu8twKjsefjuNCfEDMUq7H8IWIAACzCIAAlUzKEgwNgLCZ5NSdj0E",
    (0, 4): "CAACAgIAAxkBAAER94Jqu8twwTTcfmRZvm6XXspK0nmjmgACWi4AAgsxKUgP6QidgPU_vD0E",
    (0, 5): "CAACAgIAAxkBAAER94Nqu8twu5IfB1d9jprwNDE82Muf3gACxicAAskcKUh81whuSWBy_T0E",
    (0, 6): "CAACAgIAAxkBAAER94Rqu8twI-L2y55lnLbrDrNZjRT1gQACMjAAAgFpKEhl1mjg5_SJrz0E",
    (1, 1): "CAACAgIAAxkBAAER94Vqu8twcip5UBKk3DeeEd7fstHgwwACDC8AAgSYKEg8MYiXVi3CEz0E",
    (1, 2): "CAACAgIAAxkBAAER94Zqu8twfrphRB3TuCaCLIlHJUvg1AACoioAAtByKEjs38uspde1Oj0E",
    (1, 3): "CAACAgIAAxkBAAER94dqu8twqSeH7cofeknhRxzBArFsRgAClCkAAtSwKEi3Jin4UkiYBj0E",
    (1, 4): "CAACAgIAAxkBAAER94hqu8twNuXd46bf-PYqGoZDJpisygAC1ywAAlJgKUjdSeYyascWjT0E",
    (1, 5): "CAACAgIAAxkBAAER94lqu8tw9dysIW2duZGYyjLpjxKTkwACfi4AAiZlKUjPHT845PZoXz0E",
    (1, 6): "CAACAgIAAxkBAAER94pqu8tw10ll5ogtYaUyD3A27ZtB-QACgCwAAgq2KEjINjh0yLySGT0E",
    (2, 2): "CAACAgIAAxkBAAER94tqu8twt5rKtGKpQSL1E2P5BQO0AgACLS8AApHKKUjrJ6XTdPZ5dT0E",
    (2, 3): "CAACAgIAAxkBAAER94xqu8twtX_fjku0B_bBK1RtzT4WwQACdygAAkNVKEgTNuyp4WueTz0E",
    (2, 4): "CAACAgIAAxkBAAER941qu8twICjRsmXRwR3jl-6Ok43r2gAC7DAAAnF-KUiIS-7mDqfQbT0E",
    (2, 5): "CAACAgIAAxkBAAER945qu8tw4oH2MFJ477WPyKAH8D6U8wACeiMAAhBsKEhkx_xhsFaacj0E",
    (2, 6): "CAACAgIAAxkBAAER949qu8tw74JeNt9QMwfrJP3edPDeNwACvyoAAtWsKUhe7Ja3ko9u7D0E",
    (3, 3): "CAACAgIAAxkBAAER95Bqu8tw4qP7yG_Ev-jHCviofm1MbwAC9ykAAsPWKEjvFFYcR9YNqj0E",
    (3, 4): "CAACAgIAAxkBAAER95Fqu8twMY7mrKGPqSB5EBPrBAtKygACGCsAAoPQKEiE4DMWKSFr1D0E",
    (3, 5): "CAACAgIAAxkBAAER95Jqu8twPTgiHFTOhYU9WBBzWZyGTAACIjAAAiwCKEiCzoCKNkWSKT0E",
    (3, 6): "CAACAgIAAxkBAAER95Nqu8twwBh96xi8I7w_CNyNYIg3ZgACPC0AAnjfKEjwBdsYe03Mrj0E",
    (4, 4): "CAACAgIAAxkBAAER95Rqu8twdiY3ygke7kTktECuATS9QwACBiUAAtelKEjS0WFULFDPRj0E",
    (4, 5): "CAACAgIAAxkBAAER95Vqu8twgC3BZuIU_6GNgn2vKCfyZwACySwAAr1xKEjXp_YUUrIP-D0E",
    (4, 6): "CAACAgIAAxkBAAER95Zqu8twO26vn_pBWuUerKKQ-i0jtQACty0AAuXeKUiMg4qb-JOhtT0E",
    (5, 5): "CAACAgIAAxkBAAER95dqu8twxxPl2spBayM2ErNf8kpHKwACqyoAAp__KEhtVSbeNa-kUz0E",
    (5, 6): "CAACAgIAAxkBAAER95hqu8twEUyizau1abtTpIHUVmLMtgACaicAAvynKEhmSDuYND3Utz0E",
    (6, 6): "CAACAgIAAxkBAAER95lqu8twBWtMMe5Wuqu-GCqTK4fhCAACRSwAAtL_KUhgtv4jhI40RT0E",
}

def get_sticker_id(tile):
    # tile ကို အငယ် မှ အကြီးသို့ စီစဉ်၍ Key အဖြစ် ရှာဖွေခြင်း
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

    GAMES[chat_id] = DominoGame(chat_id, user.id)
    GAMES[chat_id].players.append(user.id)
    GAMES[chat_id].player_names[user.id] = user.first_name

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

    game.players.append(user.id)
    game.player_names[user.id] = user.first_name
    await update.message.reply_text(f"{user.first_name} joined the game!")

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

    first_sticker = get_sticker_id(first_tile)
    
    text = (
        f"First player: {name}\n"
        f"Initial tile: [{first_tile[0]}|{first_tile[1]}]\n\n"
        f"Use /close to stop people from joining the game."
    )
    keyboard = [[InlineKeyboardButton("Make your choice!", switch_inline_query_current_chat="")]]
    
    if first_sticker:
        await update.message.reply_sticker(first_sticker)
        
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
    del game.player_names[user.id]
    await update.message.reply_text(f"{user.first_name} left the game.")

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

# --- Inline Query Handler (Stickers UI) ---

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

    if not active_game.drawn_this_turn:
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
        await update.message.reply_text("❌ You cannot play this tile!")
        return

    left_end, right_end = game.get_ends()
    a, b = tile

    if a == right_end:
        game.board.append((a, b))
    elif b == right_end:
        game.board.append((b, a))
    elif a == left_end:
        game.board.insert(0, (b, a))
    elif b == left_end:
        game.board.insert(0, (a, b))

    played_sticker = get_sticker_id(tile)
    game.hands[user_id].pop(tile_idx)

    if played_sticker:
        await update.message.reply_sticker(played_sticker)

    if len(game.hands[user_id]) == 0:
        await update.message.reply_text(f"🎉 {game.player_names[user_id]} won the game! 🏆")
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
        await update.message.reply_text("No tiles left in deck. Use Pass!")
        return

    drawn_tile = game.deck.pop()
    game.hands[user_id].append(drawn_tile)
    game.drawn_this_turn = True

    await update.message.reply_text(
        f"{game.player_names[user_id]} drew a tile.\nClick 'Make your choice!' again to play or pass.",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Make your choice!", switch_inline_query_current_chat="")]])
    )

async def handle_pass(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    game = GAMES.get(chat_id)

    if not game or game.get_current_player_id() != user_id:
        return

    game.next_turn()
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
    BOT_TOKEN = os.environ.get("BOT_TOKEN", "8988526962:AAGdIJbT8Bg4KpI270mlt8JlS5mLvPS6eMM")

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
