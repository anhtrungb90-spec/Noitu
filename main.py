import logging
import random
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- Cấu hình Bot ---
TOKEN = "8259250419:AAHsi4w_wZqd5WTVBUqvRJnQLpp-IG8NVrk"  # <-- THAY THẾ TOKEN CỦA BẠN VÀO ĐÂY
DICTIONARY_FILE = "words.txt"  # Tên file từ điển

# Cấu hình logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


def get_last_syllable(text: str) -> str:
    """Tách và lấy tiếng cuối cùng của một cụm từ"""
    words = text.strip().split()
    if not words:
        return ""
    return words[-1].lower()


def get_first_syllable(text: str) -> str:
    """Tách và lấy tiếng đầu tiên của một cụm từ"""
    words = text.strip().split()
    if not words:
        return ""
    return words[0].lower()


def load_dictionary(filename: str) -> dict:
    """
    Đọc file 'words.txt' và xử lý nó thành một dictionary.
    Cấu trúc: { 'tiếng_bắt_đầu': ['từ hoàn chỉnh 1', 'từ hoàn chỉnh 2'] }
    """
    logger.info(f"Đang tải từ điển từ file {filename}...")
    dictionary = {}
    word_count = 0
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            for line in f:
                word = line.strip().lower()
                
                # Bỏ qua các dòng trống hoặc từ chỉ có 1 tiếng
                if not word or len(word.split()) < 2:
                    continue
                
                first_syllable = get_first_syllable(word)
                
                if first_syllable not in dictionary:
                    dictionary[first_syllable] = []
                    
                dictionary[first_syllable].append(word)
                word_count += 1

    except FileNotFoundError:
        logger.error(f"LỖI: Không tìm thấy file từ điển '{filename}'.")
        logger.error("Vui lòng tạo file 'words.txt' và thêm từ vựng vào.")
        return {}
    except Exception as e:
        logger.error(f"LỖI khi đọc file từ điển: {e}")
        return {}
    
    logger.info(f"Tải từ điển thành công. Tổng cộng có {word_count} từ và {len(dictionary)} tiếng bắt đầu.")
    return dictionary

# --- TẢI TỪ ĐIỂN KHI BOT KHỞI ĐỘNG ---
VIETNAMESE_DICT = load_dictionary(DICTIONARY_FILE)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Xử lý lệnh /start"""
    
    # Kiểm tra xem từ điển đã được tải chưa
    if not VIETNAMESE_DICT:
        await update.message.reply_text(
            "LỖI: Từ điển chưa được tải. "
            "Vui lòng kiểm tra lại file `words.txt` và khởi động lại bot."
        )
        return

    try:
        # Chọn một từ ngẫu nhiên để bắt đầu
        start_key = random.choice(list(VIETNAMESE_DICT.keys()))
        start_word = random.choice(VIETNAMESE_DICT[start_key])
        
        # Lấy tiếng cuối của từ bắt đầu để làm "key" cho người dùng
        next_key = get_last_syllable(start_word)
        
        # Lưu "key" này vào bộ nhớ của cuộc hội thoại
        context.chat_data['last_key'] = next_key
        
        await update.message.reply_text(
            "Chào bạn! Chúng ta hãy chơi trò Nối Từ Tiếng Việt.\n"
            "Luật chơi: Bot sẽ ra một từ (ít nhất 2 tiếng), bạn phải đáp lại bằng một từ bắt đầu bằng tiếng cuối cùng của bot.\n\n"
            "Bot ra trước nhé:\n\n"
            f"**{start_word.capitalize()}**\n\n"
            f"(Lượt của bạn, hãy tìm từ bắt đầu bằng: **{next_key}**)",
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Lỗi khi bắt đầu game: {e}")
        await update.message.reply_text("Có lỗi xảy ra khi bắt đầu game. Thử lại sau.")


async def play_word(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Xử lý tin nhắn nối từ của người dùng"""
    user_message = update.message.text.lower().strip()
    
    # Lấy "key" mà bot đã đưa ra ở lượt trước
    last_key = context.chat_data.get('last_key')

    # 1. Kiểm tra xem game đã bắt đầu chưa
    if not last_key:
        await update.message.reply_text("Bạn hãy gõ /start để bắt đầu trò chơi mới nhé.")
        return

    # 2. Phân tích từ của người dùng
    user_first_syllable = get_first_syllable(user_message)
    user_last_syllable = get_last_syllable(user_message)

    if len(user_message.split()) < 2:
        await update.message.reply_text(
            f"Từ của bạn phải có ít nhất 2 tiếng. "
            f"Hãy thử lại (bắt đầu bằng: **{last_key}**).",
            parse_mode="Markdown"
        )
        return

    # 3. Kiểm tra tính hợp lệ (từ của người dùng có bắt đầu bằng "key" không)
    if user_first_syllable != last_key:
        await update.message.reply_text(
            f"Sai rồi! Từ của bạn phải bắt đầu bằng: **{last_key}**\n"
            f"Bạn đã gõ: {user_message}",
            parse_mode="Markdown"
        )
        return

    # 4. Bot tìm từ để đáp trả (dựa trên tiếng cuối của người dùng)
    bot_reply_key = user_last_syllable
    
    if bot_reply_key in VIETNAMESE_DICT:
        # Bot tìm thấy từ
        possible_words = VIETNAMESE_DICT[bot_reply_key]
        bot_response_word = random.choice(possible_words)
        
        # Lấy "key" tiếp theo cho người dùng
        next_key = get_last_syllable(bot_response_word)
        context.chat_data['last_key'] = next_key
        
        await update.message.reply_text(
            f"**{bot_response_word.capitalize()}**\n\n"
            f"(Lượt của bạn, bắt đầu bằng: **{next_key}**)",
            parse_mode="Markdown"
        )
    else:
        # Bot thua!
        await update.message.reply_text(
            f"Bạn thắng! 🏆\n\n"
            f"Tôi không tìm được từ nào bắt đầu bằng: **{bot_reply_key}**\n"
            "Gõ /start để chơi lại ván mới.",
            parse_mode="Markdown"
        )
        # Reset game
        context.chat_data['last_key'] = None


def main():
    """Chạy bot"""
    # Kiểm tra xem từ điển có trống không
    if not VIETNAMESE_DICT:
        print("LỖI: Từ điển trống. Bot không thể khởi động.")
        print(f"Vui lòng kiểm tra file '{DICTIONARY_FILE}' có tồn tại và có nội dung không.")
        return

    application = Application.builder().token(TOKEN).build()

    # Thêm các handler
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, play_word))

    print("Bot đang chạy...")
    # Chạy bot cho đến khi bạn nhấn Ctrl+C
    application.run_polling()

if __name__ == "__main__":
    main()

