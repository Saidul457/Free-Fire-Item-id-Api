import telebot
import os
import gzip
import json
import io

def float_division_without_decimal(numerator, denominator):
    return int(numerator / denominator)

def decimal_to_varint_hex(decimal_number):
    if decimal_number < 0:
        raise ValueError("Decimal number must be non-negative.")
    
    varint_bytes = []
    while True:
        byte = decimal_number & 0x7F
        decimal_number >>= 7
        if decimal_number:
            byte |= 0x80
        varint_bytes.append(byte)
        if not decimal_number:
            break
    return ''.join(f'{byte:02X}' for byte in varint_bytes)

def count_text_file_bytes(file_path):
    try:
        with open(file_path, 'rb') as file:
            content = file.read()

        byte_count = len(content)
        numerator = byte_count
        denominator = 2
        result = float_division_without_decimal(numerator, denominator)
        hexa = decimal_to_varint_hex(result)
        if len(hexa) > 4:
            newhexa = (result + 6)
            hexadecimal = decimal_to_varint_hex(newhexa)
            return hexadecimal, hexa
        else:
            newhexa = (result + 5)
            hexadecimal = decimal_to_varint_hex(newhexa)
            return hexadecimal, hexa
    except Exception as e:
        return f"Error: {e}"

def replace_data(file_path, start_hex, end_hex, new_data_txt_path):
    try:
        start_bytes = bytes.fromhex(start_hex)
        end_bytes = bytes.fromhex(end_hex)
        hexadecimal, hexa = count_text_file_bytes(new_data_txt_path)

        pre_hex_data = bytes.fromhex(f'0A{hexadecimal}0A{hexa}')

        with open(new_data_txt_path, 'r') as new_data_file:
            hex_data = new_data_file.read().strip()
            new_data_bytes = bytes.fromhex(hex_data)

        with open(file_path, 'rb') as file:
            data = file.read()

        start_pos = data.find(start_bytes)
        if start_pos == -1:
            return "Your Provided File isn't Valid. If you think I made a Mistake, Please Contact @Garena420"

        end_pos = data.find(end_bytes, start_pos)
        if end_pos == -1:
            return "Your Provided File isn't Valid. If you think I made a Mistake, Please Contact @Garena420"

        end_pos += len(end_bytes)

        modified_data = pre_hex_data + new_data_bytes + data[end_pos - len(end_bytes):]

        with open(file_path, 'wb') as file:
            file.write(modified_data)

        return "Data successfully replaced. If Your File has been Damaged or if You Think I made a Mistake, Please Contact @Garena420"
    except Exception as e:
        return f"Please Upload a Valid Text File. If you think I made a Mistake, Please Contact @Garena420"

def json_to_gzipped_hex(json_file_path, output_hex_file_path):
    try:
        with open(json_file_path, 'r') as file:
            data = json.load(file)

        json_str = json.dumps(data, indent=2)
        json_bytes = json_str.encode('utf-8')

        buf = io.BytesIO()
        with gzip.GzipFile(fileobj=buf, mode='wb') as f:
            f.write(json_bytes)

        compressed_data = buf.getvalue()
        hex_string = compressed_data.hex().upper()

        with open(output_hex_file_path, 'w') as file:
            file.write(hex_string)

        return output_hex_file_path
    except Exception as e:
        return f"Please Upload a Valid Text File. If you think I made a Mistake, Please Contact @Garena420"

bot = telebot.TeleBot("7252401849:AAEhh7ZyTj2QeI0BtgyktaytNvLt5NFIyQQ")

user_files = {}

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Welcome! Please upload your file.")

@bot.message_handler(commands=['cancel'])
def cancel_operation(message):
    chat_id = message.chat.id
    if chat_id in user_files:
        # Remove all files associated with the user
        files_to_remove = user_files[chat_id].values()
        for file_path in files_to_remove:
            if os.path.exists(file_path):
                os.remove(file_path)
        del user_files[chat_id]
        bot.reply_to(message, "Operation canceled and files deleted.")
    else:
        bot.reply_to(message, "No ongoing operation to cancel.")

@bot.message_handler(content_types=['document'])
def handle_file(message):
    if message.document:
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        file_name = message.document.file_name
        file_path = f"./{file_name}"
        with open(file_path, 'wb') as new_file:
            new_file.write(downloaded_file)

        chat_id = message.chat.id
        if chat_id not in user_files:
            user_files[chat_id] = {}

        if 'main_file' not in user_files[chat_id]:
            if file_name.endswith(".bytes"):
                user_files[chat_id]['main_file'] = file_path
                bot.reply_to(message, "First file uploaded successfully. Now please upload the text file.")
            else:
                os.remove(file_path)
                bot.reply_to(message, "Error: The first file must be named 'ProjectData_slot_(Your Slot Number).bytes'. Please try again.")
        else:
            if file_name.endswith(('.json', '.txt', '.dat')):
                user_files[chat_id]['json_file'] = file_path

                main_file = user_files[chat_id]['main_file']
                json_file_path = user_files[chat_id]['json_file']
                hex_file_path = './temp_hex_file.txt'
                hex_file = json_to_gzipped_hex(json_file_path, hex_file_path)

                if not os.path.exists(hex_file):
                    bot.reply_to(message, hex_file)
                    return

                start_hex = '1F8B0800'
                end_hex = '10031A'

                result = replace_data(main_file, start_hex, end_hex, hex_file)

                bot.reply_to(message, result)

                if "successfully replaced" in result:
                    with open(main_file, 'rb') as modified_file:
                        bot.send_document(message.chat.id, modified_file)

                os.remove(main_file)
                os.remove(json_file_path)
                os.remove(hex_file)

                del user_files[chat_id]
            else:
                os.remove(file_path)
                bot.reply_to(message, "Error: The second file isn't valid. Please try again.")

print("Bot Started...")
bot.polling()
