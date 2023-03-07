import csv
import random
import re
import sys
import time
from pathlib import Path
from typing import Optional

from tkinter import Tk
from tkinter.filedialog import askopenfilename
from hanspell import spell_checker
from konlpy.tag import Okt, Mecab, Hannanum, Kkma

hannanum = Hannanum()
kkma = Kkma()
okt = Okt()
mecab = Mecab()


def write_csv(
        row_data: list,
        filename: str,
) -> None:

    with open(filename, 'a', newline='', encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(row_data)


# 받는 문자열을 토큰화 하여 리스트로 반환
def tokenizer(
        content: str,
        use_class: Optional[str]
) -> list:
    if not use_class:
        use_class = 'okt'

    exception_nouns = [
        '것', '등', '곳', '겸', '지지', '를', '고', '또', '버티고', '전혀', '계속', '탁',
        '이후', '로서', '내', '씨', '이전', '가량', '가까이', '로', '더욱', '속', '조금', '위해', '미리', '깜짝', '땐',
        '거나', '더', '다시', '찬', '막', '뽁뽁', '면서', '지난달', '뒤', '의', '끌', '또한', '여러', '뚝', '훌쩍', '진짜',
        '껑충', '다른', '중', '그다음', '통해', '스스로', '한편', '읏', '클리', '갑작스레', '다만', '다음', '과', '뿐', '달리',
        '외', '오', '류', '즉', '등등', '및', '저희', '꽉', '후', '때', '매우', '놀', '거', '디', '두', '때', '제법',
        '제일', '쪽', '한참', '좀', '가끔', '조그만', '몇', '무슨', '별로', '한번' '혼자', '카', '키'
    ]

    nouns = []
    if use_class == 'mecab':
        nouns: list = mecab.nouns(content)
    elif use_class == 'okt':
        nouns: list = okt.nouns(content)
    elif use_class == 'hannanum':
        nouns: list = hannanum.nouns(content)
    elif use_class == 'kkma':
        nouns: list = kkma.nouns(content)

    noun_result = [noun for noun in nouns if noun not in exception_nouns]

    return noun_result


# 문자열을 리스트로 반환하는데 500자 이상의 문자열인 경우, 그 이하로 나누어서 리스트로 반환
def text_to_slice_list(text) -> list:
    texts = []
    if len(text) > 500:
        splitted_last_index: int = text[:500].rfind('.')
        front_text = text[:splitted_last_index]
        texts.append(front_text)
        rear_text = text[splitted_last_index:]

        if len(rear_text) > 500:
            splitted_last_index = rear_text[:500].rfind('.')
            texts.append(rear_text[:splitted_last_index])
            texts.append(rear_text[splitted_last_index:])
        else:
            texts.append(rear_text)
    else:
        texts = [text]
    return texts


def removed_special_characters(text: str) -> str:
    reformatted_text = re.sub(
        r'[^\uAC00-\uD7A30-9a-zA-Z.\s]', '', text
    )
    return reformatted_text


# 문자열의 맞춤법 검사
def check_spell(text: str) -> str:
    text_list = []

    for t in text_to_slice_list(text):

        checked_text = spell_checker.check(t)
        checked_text_dict = checked_text.as_dict()

        if checked_text_dict['result']:
            corrected_text = checked_text_dict['checked']

            text_list.append(corrected_text)
        time.sleep(random.uniform(0.1, 0.3))
    new = ''.join(t + ' ' for t in text_list)
    return new


def check_exists_file(file) -> bool:
    file_path = Path(file)
    return file_path.exists()


def get_news_from_file():
    new_data = dict()
    opened_file = None
    if check_exists_file('crawled_naver_news.csv'):
        opened_file = open(f'crawled_naver_news.csv', 'r')
        datas = csv.DictReader(opened_file)
        new_data = datas

    return new_data, opened_file


def get_review_from_file():
    Tk().withdraw()
    file_name: str = askopenfilename(filetypes=(('csv', '*.csv'), ('all files', '*.*')))
    if not file_name:
        raise FileNotFoundError({'status': f'{file_name} 을/를 찾을 수 없습니다.'})

    if check_exists_file(file_name):
        opened_file = open(file_name, 'r', encoding='utf-8-sig')
        datas = csv.reader(opened_file)
        new_data = datas
    else:
        raise FileNotFoundError({'status': f'{file_name} 을/를 찾을 수 없습니다.'})

    return new_data, opened_file


def make_tokenizer(category: str, tokenizer_class: str) -> None:
    if 'news' in category:
        print('news tokenizer')
        datas, opened_file = get_news_from_file()
        # tokenizer_class = input('"mecab" or "okt"? : ')
        noun_list = []
        for i, data in enumerate(datas, start=1):
            # if i < 2:
            corrected_text: str = check_spell(data['내용'])
            noun_list += tokenizer(content=corrected_text, use_class=tokenizer_class)
            print(f'저장: [{i}]')

        if opened_file:
            opened_file.close()

        results = list(set(noun_list))
        results.sort()

        file_name = 'token_list.csv'

        write_csv(['n', '단어'], file_name)
        for i, result in enumerate(results, start=1):
            write_csv([i, result], file_name)

    elif 'review' in category:
        print('review tokenizer')
        datas, opened_file = get_review_from_file()
        file_name = 'review_token_list.csv'

        if not check_exists_file(file_name):
            write_csv(['no', 'review_id', 'nickname', 'place_name', 'words'], file_name)

        for i, row in enumerate(datas, start=1):
            if i < 188:
                continue
            elif i > 190:
                break

            noun_list = []
            review_id = int(row[0])
            user_character = row[1]
            user_nickname = row[2]
            user_id = row[3]
            user_profile = row[4]
            place_id = row[5]
            place_name = row[6]
            place_address = row[7]
            review_content = removed_special_characters(row[8])
            visited_at = row[9]
            created_at = row[10]
            s3_path = row[11]
            image_url = row[12]

            corrected_text: str = check_spell(review_content)
            noun_list += tokenizer(content=corrected_text, use_class=tokenizer_class)
            noun_list = list(set(noun_list))
            noun_list.sort()
            noun_one_line = ';'.join(noun for noun in noun_list)
            write_csv([
                i,
                review_id,
                user_nickname,
                place_name,
                noun_one_line
            ], file_name)
            print(f'저장: [{i}]')

        opened_file.close()


category_argument = sys.argv[1] if len(sys.argv) > 1 else '--news'
extra_argument = sys.argv[2] if len(sys.argv) > 2 else '--okt'


def error_message(n):
    usage = f'\n\nUsage:\n  python3 tokenizer.py --[options] --[options]\n'\
            f'\n\nOptions:\n  --news    tokenize news content\n' \
            f'  --review    tokenize review content\n\n' \
            f'  [content type] --okt    tokenize with okt class\n' \
            f'  [content type] --mecab    tokenize with mecab class\n' \
            f'  [content type] --hannanum    tokenize with hannanum class\n' \
            f'  [content type] --kkma    tokenize with kkma class\n\n' \
            f'no such option: {sys.argv[n] if len(sys.argv) > n else None}'
    return usage


if '--' not in category_argument:
    raise Exception(error_message(1))

if '--' not in extra_argument:
    raise Exception(error_message(2))

arg_text = category_argument.replace('--', '')
if arg_text not in ['review', 'news']:
    raise Exception(error_message(1))

extra_arg_text = extra_argument.replace('--', '')
if extra_arg_text not in ['okt', 'mecab', 'hannanum', 'kkma']:
    raise Exception(error_message(2))


make_tokenizer(category_argument, extra_arg_text)


# def make_token_image(word_dic):
#     font_path = ''
#     wc = WordCloud(
#         width=1000, height=600, background_color='white', font_path=font_path
#     )
#     wc.generate_from_frequencies(word_dic)
#
#     plt.figure(figsize=(15, 15))
#
#     plt.imshow(wc)
#     plt.axis('off')
#     plt.tight_layout(pad=0)
#     plt.show()
