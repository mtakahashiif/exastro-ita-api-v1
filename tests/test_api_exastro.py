import exastro_ita_api_v1 as apiv1
import dotenv
import json
import collections.abc
from typing import *

import importlib.resources as resources
import importlib.abc as resabc


def test_add_record():
    dotenv.load_dotenv()
    api_exastro = apiv1.ApiExastro()

    edit_data_entries = [
        {
            'operation': '登録',
            'body': {
                'ホスト名': 'test-01',
                'IPアドレス': '192.168.0.1',
                'ssh鍵認証情報/ssh秘密鍵ファイル': 'private.key',
                'Ansible利用情報/Ansible Automation Controller利用情報/接続タイプ': 'machine'
            },
            'upload_file': {
                'ssh鍵認証情報/ssh秘密鍵ファイル': 'tests/data_private_keys/private-00.key'
            }
        },
        {
            'operation': '登録',
            'strategy': apiv1.sequence_register(range(10, 20)),
            'body': {
                'ホスト名': 'test-{sequence:0>2d}',
                'IPアドレス': '192.168.0.{sequence:d}',
                'ssh鍵認証情報/ssh秘密鍵ファイル': 'private.key',
                'Ansible利用情報/Ansible Automation Controller利用情報/接続タイプ': 'machine',
            },
            'upload_file': {
                'ssh鍵認証情報/ssh秘密鍵ファイル': 'tests/data_private_keys/private-{sequence:0>2d}.key'
            }
        },
    ]

    api_exastro.edit(apiv1.MenuId.基本コンソール.機器一覧, edit_data_entries)
#
#
#def test_update_record():
#    dotenv.load_dotenv()
#    api_exastro = apiv1.ApiExastro()
#
#    input_data = [
#        {
#            'body': {
#                'ホスト名': 'test-01',
#                'IPアドレス': '192.168.0.1',
#                'ssh鍵認証情報/ssh秘密鍵ファイル': 'private.key',
#                'Ansible利用情報/Ansible Automation Controller利用情報/接続タイプ': 'machine'
#            },
#            'upload_file': {
#                'ssh鍵認証情報/ssh秘密鍵ファイル': 'tests/data_private_keys/private-00.key'
#            }
#        },
#        apiv1.sequenced_template(range(10, 20), {
#            'body': {
#                'ホスト名': 'test-{sequence_number:0>2d}',
#                'IPアドレス': '192.168.0.{sequence_number:d}',
#                'ssh鍵認証情報/ssh秘密鍵ファイル': 'private.key',
#                'Ansible利用情報/Ansible Automation Controller利用情報/接続タイプ': 'machine'
#            },
#            'upload_file': {
#                'ssh鍵認証情報/ssh秘密鍵ファイル': 'tests/data_private_keys/private-{sequence_number:0>2d}.key'
#            }
#        })
#    ]
#
#    api_exastro.add_records(apiv1.MenuId.基本コンソール.機器一覧, input_data)
#
#    edit_data = [
#        {
#            'operation': '登録',
#            'strategy': sequence_register(range(10, 15),
#            'body': {
#                'ホスト名': 'test-{sequence:0>2d}',
#                'IPアドレス': '192.168.0.{sequence:d}',
#                'ssh鍵認証情報/ssh秘密鍵ファイル': 'private.key',
#                'Ansible利用情報/Ansible Automation Controller利用情報/接続タイプ': 'machine'
#            },
#            'upload_file': {
#                'ssh鍵認証情報/ssh秘密鍵ファイル': 'tests/data_private_keys/private-{sequence:0>2d}.key'
#            }
#        },
#        {
#            'operation': '更新',
#            'strategy': regexp_selector({
#                'ホスト名': r'(.+)'
#                'IPアドレス': r'192.168.0.(\d+)'
#            }),
#            'values': {
#                'ホスト名': r'{ホスト名[1]}-{IPアドレス[1]}',
#                'Ansible利用情報/Ansible Automation Controller利用情報/接続タイプ': 'machine'
#                'ssh鍵認証情報/ssh秘密鍵ファイル': 'private.key',
#            },
#            'files': {
#                'ssh鍵認証情報/ssh秘密鍵ファイル': r'tests/data_private_keys/private-{IPアドレス[1]:0>2d}.key'
#            }
#        }
#    ]
#
##    api_exastro.update_records(apiv1.MenuId.基本コンソール.機器一覧, updators)
##