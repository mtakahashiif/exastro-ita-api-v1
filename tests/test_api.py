import exastro_ita_api_v1 as apiv1
import dotenv
import json
import os


def test_api():
    dotenv.load_dotenv()

    api_context = apiv1.ApiContext(os.environ)
    api_request = api_context.create_api_request(apiv1.MenuId.基本コンソール.機器一覧)

    with api_request.send_post(apiv1.XCommand.FILTER) as api_response:
        json_object = api_response.json_object

    print(json.dumps(json_object, ensure_ascii=False, indent=4))


def test_edit():
    dotenv.load_dotenv()

    api_context = apiv1.ApiContext(os.environ)
    api_request = api_context.create_api_request(apiv1.MenuId.基本コンソール.機器一覧)
    indexer: apiv1.Indexer = api_request.indexer

    parameters = {
        "0": {
            indexer['実行処理種別']: apiv1.実行処理種別.登録,
            indexer['ホスト名']: 'test-hostname-01',
            indexer['IPアドレス']: '192.168.0.1',
            indexer['Ansible利用情報/Ansible Automation Controller利用情報/接続タイプ']: 'machine'
        },
        "1": {
            indexer['実行処理種別']: apiv1.実行処理種別.登録,
            indexer['ホスト名']: 'test-hostname-02',
            indexer['IPアドレス']: '192.168.0.2',
            indexer['Ansible利用情報/Ansible Automation Controller利用情報/接続タイプ']: 'machine'
        }
    }

    with api_request.send_post(apiv1.XCommand.EDIT, parameters) as api_response:
        json_object = api_response.json_object
        print('EDIT ●●●●●●●●●●●●')
        print(json.dumps(json_object, ensure_ascii=False, indent=4))    

    parameters = {
        indexer['廃止']: { 
            'NORMAL': '0'   # 廃止含まず
        }
    }

    with api_request.send_post(apiv1.XCommand.FILTER, parameters) as api_response:
        json_object = api_response.json_object
        print('FILTER ●●●●●●●●●●●●')
        print(json.dumps(json_object, ensure_ascii=False, indent=4))

    with api_request.send_post(apiv1.XCommand.FILTER_DATAONLY, parameters) as api_response:
        json_object = api_response.json_object
        print('FILTER_DATAONLY ●●●●●●●●●●●●')
        print(json.dumps(json_object, ensure_ascii=False, indent=4))


def test_edit_with_table():
    dotenv.load_dotenv()

    api_context = apiv1.ApiContext(os.environ)
    api_request = api_context.create_api_request(apiv1.MenuId.基本コンソール.機器一覧)
    indexer: apiv1.Indexer = api_request.indexer

    menu = apiv1.Menu(indexer)

    row = menu.create_row(operation=apiv1.実行処理種別.登録)
    row.body['ホスト名'] = 'test-hostname-10'
    row.body['IPアドレス'] = '192.168.0.10'
    row.body['Ansible利用情報/Ansible Automation Controller利用情報/接続タイプ'] = 'machine'
    row.body['ssh鍵認証情報/ssh秘密鍵ファイル'] = 'private.key'
    row.file['ssh鍵認証情報/ssh秘密鍵ファイル'] = 'tests/data_private_keys/private-10.key'
    menu.add_row(row)

    row = menu.create_row(operation=apiv1.実行処理種別.登録)
    row.body['ホスト名'] = 'test-hostname-11'
    row.body['IPアドレス'] = '192.168.0.11'
    row.body['Ansible利用情報/Ansible Automation Controller利用情報/接続タイプ'] = 'machine'
    row.body['ssh鍵認証情報/ssh秘密鍵ファイル'] = 'private.key'
    row.file['ssh鍵認証情報/ssh秘密鍵ファイル'] = 'tests/data_private_keys/private-11.key'
    menu.add_row(row)
    
    print('parameters ●●●●●●●●●●●●')
    print(json.dumps(menu.to_edit_parameters(), ensure_ascii=False, indent=4))

    with api_request.send_post(apiv1.XCommand.EDIT, menu.to_edit_parameters()) as api_response:
        json_object = api_response.json_object
        print('EDIT ●●●●●●●●●●●●')
        print(json.dumps(json_object, ensure_ascii=False, indent=4))

    parameters = {
        indexer['廃止']: { 
            'NORMAL': '0'   # 廃止含まず
        }
    }

    with api_request.send_post(apiv1.XCommand.FILTER_DATAONLY, parameters) as api_response:
        json_object = api_response.json_object
        print('FILTER_DATAONLY ●●●●●●●●●●●●')
        print(json.dumps(json_object, ensure_ascii=False, indent=4))

    menu = apiv1.Menu(indexer, json_object)

    print('parameters ●●●●●●●●●●●●')
    print(json.dumps(menu.to_edit_parameters(), ensure_ascii=False, indent=4))
