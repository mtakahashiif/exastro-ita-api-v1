import exastro_ita_api_v1 as apiv1
import dotenv
import json


def test_api():
    dotenv.load_dotenv()

    api_context = apiv1.ApiContext()
    api_request = api_context.create_api_request(apiv1.MenuId.基本コンソール.機器一覧)

    with api_request.send_post(apiv1.XCommand.FILTER) as api_response:
        json_object = api_response.body_as_json_object

    print(json.dumps(json_object, ensure_ascii=False, indent=4))


#KIKI = {
#    'BEFORE': {
#        'HOST': 'ccc',
#        'IP': '192.168.1.1',
#    },
#    'AFTER': {
#        'HOST': 'ddd',
#        'IP': '192.168.1.2',
#    }
#}
#
#def test_edit():
#    dotenv.load_dotenv()
#
#    api_context = apiv1.ApiContext()
#    api_request = api_context.create_api_request(apiv1.MenuId.基本コンソール.機器一覧)
#    indexer = api_request.indexer
#
#    edit_parameter_builder = api_request.create_edit_parameter_builder()
#
#    edit_record = edit_parameter_builder.create_edit_record(apiv1.実行処理種別.登録)
#    edit_record['ホスト名'] = KIKI['BEFORE']['HOST']
#    edit_record['IPアドレス'] = KIKI['BEFORE']['IP']
#    edit_record['Ansible利用情報/Ansible Automation Controller利用情報/接続タイプ'] = 'machine'
#    edit_parameter_builder.add(edit_record)
#
##    print(json.dumps(edit_parameter_builder.generate(), ensure_ascii=False, indent=4))
#
#    with api_request.send_post(apiv1.XCommand.EDIT, edit_parameter_builder.generate()) as api_response:
#        print('40 edit 登録 ●●●●●●●●●●●●')
#        print(json.dumps(api_response.body_as_json_object, ensure_ascii=False, indent=4))
#
#    filter_parameter = {
#        indexer['廃止']: { 
#            'NORMAL': '0'   # 廃止含まず
#        },
#        indexer['ホスト名']: {
#            'NORMAL': KIKI['BEFORE']['HOST']
#        }
#    }
#
#    with api_request.send_post(apiv1.XCommand.FILTER_DATAONLY, filter_parameter) as api_response:
#        json_object = api_response.body_as_json_object
#        print('50 dataonly ●●●●●●●●●●●●')
#        print(json.dumps(json_object, ensure_ascii=False, indent=4))
#
#    edit_parameter_builder = api_request.create_edit_parameter_builder()
#
#    edit_record = edit_parameter_builder.create_edit_record(apiv1.実行処理種別.更新, json_object['resultdata']['CONTENTS']['BODY'][0])
#    edit_record['ホスト名'] = KIKI['AFTER']['HOST']
#    edit_parameter_builder.add(edit_record)
#
#    with api_request.send_post(apiv1.XCommand.EDIT, edit_parameter_builder.generate()) as api_response:
#        print('60 EDIT 更新 ●●●●●●●●●●●●')
#        print(json.dumps(api_response.body_as_json_object, ensure_ascii=False, indent=4))
#
#    filter_parameter = {
#        indexer['廃止']: { 
#            'NORMAL': '0'   # 廃止含まず
#        }
#    }
#
#    with api_request.send_post(apiv1.XCommand.FILTER, filter_parameter) as api_response:
#        print(json.dumps(api_response.body_as_json_object, ensure_ascii=False, indent=4))
#