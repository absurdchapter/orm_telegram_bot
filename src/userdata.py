import os
import json

user_data_folder = 'user_data'
user_data_filename_template = 'user_%s.json'


def get_user_data(user_id):
    user_data_filename = user_data_filename_template % user_id
    user_data_filepath = os.path.join(user_data_folder, user_data_filename)

    if not os.path.exists(user_data_filepath):
        return None

    with open(user_data_filepath, 'r', encoding='utf-8') as fp:
        user_data = json.load(fp)

    return user_data


def write_user_data(user_id, user_data):
    user_data_filename = user_data_filename_template % user_id
    user_data_filepath = os.path.join(user_data_folder, user_data_filename)

    os.makedirs(user_data_folder, exist_ok=True)

    with open(user_data_filepath, 'w', encoding='utf-8') as f:
        json.dump(user_data, f, ensure_ascii=False, indent=4)