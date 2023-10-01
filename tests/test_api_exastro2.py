import exastro_ita_api_v1 as apiv1
import dotenv
import json
import collections.abc
from typing import *

import importlib.resources as resources
import importlib.abc as resabc


#def test_load_private_keys():
#    dotenv.load_dotenv()
#
#    for i in [0, *list(range(10, 20))]:
#        x = 'data_private_keys/private-{:0>2d}.key'
#        traversable = resources.files(__package__).joinpath('data_private_keys/private-{:0>2d}.key')
#        print(type(traversable))
#        print(str(traversable).format(i))



def testx_get_indexer():
    dotenv.load_dotenv()
    api_exastro = apiv1.ApiExastro()

    indexer: dict[str, int] = api_exastro.get_indexer(apiv1.MenuId.基本コンソール.機器一覧)

    print(indexer)


def test_add_record():
    dotenv.load_dotenv()
    api_exastro = apiv1.ApiExastro()

    input_data = [
        {
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
        apiv1.sequenced_template(range(10, 20), {
            'body': {
                'ホスト名': 'test-{sequence_number:0>2d}',
                'IPアドレス': '192.168.0.{sequence_number:d}',
                'ssh鍵認証情報/ssh秘密鍵ファイル': 'private.key',
                'Ansible利用情報/Ansible Automation Controller利用情報/接続タイプ': 'machine'
            },
            'upload_file': {
                'ssh鍵認証情報/ssh秘密鍵ファイル': 'tests/data_private_keys/private-{sequence_number:0>2d}.key'
            }
        })
    ]

    api_exastro.add_records(apiv1.MenuId.基本コンソール.機器一覧, input_data)

    api_exastro.get_records(apiv1.MenuId.基本コンソール.機器一覧)


def test_update_record():
    dotenv.load_dotenv()
    api_exastro = apiv1.ApiExastro()

    input_data = [
        {
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
        apiv1.sequenced_template(range(10, 20), {
            'body': {
                'ホスト名': 'test-{sequence_number:0>2d}',
                'IPアドレス': '192.168.0.{sequence_number:d}',
                'ssh鍵認証情報/ssh秘密鍵ファイル': 'private.key',
                'Ansible利用情報/Ansible Automation Controller利用情報/接続タイプ': 'machine'
            },
            'upload_file': {
                'ssh鍵認証情報/ssh秘密鍵ファイル': 'tests/data_private_keys/private-{sequence_number:0>2d}.key'
            }
        })
    ]

    api_exastro.add_records(apiv1.MenuId.基本コンソール.機器一覧, input_data)

    input_data = [
        {
            'unique-selector': {
                'ホスト名': 'aaa'
            },
            'values': {
                'ホスト名': 'test1',
                'IPアドレス': '192.168.0.1',
                'Ansible利用情報/Ansible Automation Controller利用情報/接続タイプ': 'machine'
            },
            'files': {
                'ssh鍵認証情報/ssh秘密鍵ファイル': ''
            }
        },
        {
            'selector': regexp_select({
                'ホスト名': r'(aaa)'
            }),
            'values': regexp_replace({
                'ホスト名': r'\1test2',
                'IPアドレス': '192.168.0.2',
                'Ansible利用情報/Ansible Automation Controller利用情報/接続タイプ': 'machine'
            }),
            'files': {
                'ssh鍵認証情報/ssh秘密鍵ファイル': ''
            }
        }
    ]

#    api_exastro.update_records(apiv1.MenuId.基本コンソール.機器一覧, updators)
#