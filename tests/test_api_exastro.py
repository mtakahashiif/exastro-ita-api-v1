import exastro_ita_api_v1 as apiv1
import dotenv
import json
import collections.abc
from typing import *

import importlib.resources as resources
import importlib.abc as resabc


#def test_add_record():
#    dotenv.load_dotenv()
#    api_exastro = apiv1.ApiExastro()
#
#    edit_data_entries = [
#        {
#            'operation': '登録',
#            'body': {
#                'ホスト名': 'test-00-01',
#                'IPアドレス': '192.168.0.1',
#                'ssh鍵認証情報/ssh秘密鍵ファイル': 'private.key',
#                'Ansible利用情報/Ansible Automation Controller利用情報/接続タイプ': 'machine'
#            },
#            'upload_file': {
#                'ssh鍵認証情報/ssh秘密鍵ファイル': 'tests/data_private_keys/private-01.key'
#            }
#        },
#        {
#            'operation': '登録',
#            'strategy': apiv1.sequence_register(range(10, 20)),
#            'body': {
#                'ホスト名': 'test-00-{sequence:0>2d}',
#                'IPアドレス': '192.168.0.{sequence:d}',
#                'ssh鍵認証情報/ssh秘密鍵ファイル': 'private.key',
#                'Ansible利用情報/Ansible Automation Controller利用情報/接続タイプ': 'machine',
#            },
#            'upload_file': {
#                'ssh鍵認証情報/ssh秘密鍵ファイル': 'tests/data_private_keys/private-{sequence:0>2d}.key'
#            }
#        },
#    ]
#
#    api_exastro.edit(apiv1.MenuId.基本コンソール.機器一覧, edit_data_entries)
#

def test_update_record():
    dotenv.load_dotenv()
    api_exastro = apiv1.ApiExastro()

    edit_data_entries = [
        {
            'operation': '登録',
            'body': {
                'ホスト名': 'test-01-01',
                'IPアドレス': '192.168.1.1',
                'ssh鍵認証情報/ssh秘密鍵ファイル': 'private.key',
                'Ansible利用情報/Ansible Automation Controller利用情報/接続タイプ': 'machine'
            },
            'upload_file': {
                'ssh鍵認証情報/ssh秘密鍵ファイル': 'tests/data_private_keys/private-01.key'
            }
        },
        {
            'operation': '登録',
            'strategy': apiv1.sequence_register(range(10, 20)),
            'body': {
                'ホスト名': 'test-01-{sequence:0>2d}',
                'IPアドレス': '192.168.1.{sequence:d}',
                'ssh鍵認証情報/ssh秘密鍵ファイル': 'private.key',
                'Ansible利用情報/Ansible Automation Controller利用情報/接続タイプ': 'machine',
            },
            'upload_file': {
                'ssh鍵認証情報/ssh秘密鍵ファイル': 'tests/data_private_keys/private-{sequence:0>2d}.key'
            }
        },
    ]

    api_exastro.edit(apiv1.MenuId.基本コンソール.機器一覧, edit_data_entries)

    edit_data_entries = [
        {
            'operation': '更新',
            'strategy': {
                'ホスト名': 'test-01-postfix-01',
                'IPアドレス': '192.168.1.1',
            },
            'body': {
                'ホスト名': 'test-01-01-koushin',
                'ssh鍵認証情報/ssh秘密鍵ファイル': 'private-10.key',
                '備考': '更新'
            },
            'upload_file': {
                'ssh鍵認証情報/ssh秘密鍵ファイル': 'tests/data_private_keys/private-10.key'
            }
        },
        {
            'operation': '更新',
            'strategy': apiv1.regexp_selector({
                'ホスト名': r'test-01-1(1|2)',
                'IPアドレス': r'192\.168\.1\..*',
            }),
            'body': {
                'ホスト名': r'test-01-postfix-2{regexp_groups["ホスト名"][1]}',
                'IPアドレス': r'192.168.1.2{regexp_groups["ホスト名"][1]}',
                'ssh鍵認証情報/ssh秘密鍵ファイル': r'private-2{regexp_groups["ホスト名"][1]}.key',
                '備考': r'元のIPアドレス {regexp_groups["IPアドレス"][0]}'
            },
            'upload_file': {
                'ssh鍵認証情報/ssh秘密鍵ファイル': r'tests/data_private_keys/private-2{regexp_groups["ホスト名"][1]}.key'
            }
        },
    ]

    api_exastro.edit(apiv1.MenuId.基本コンソール.機器一覧, edit_data_entries)
