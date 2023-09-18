import exastro_ita_api_v1 as apiv1
import dotenv


def test_api():
    dotenv.load_dotenv()

    api_context = apiv1.ApiContext()
    api_request = api_context.create_api_request(apiv1.MenuId.管理コンソール.システム設定)

    with api_request.send_post(apiv1.XCommand.INFO) as api_response:
        column_indexer = api_response.column_indexer

    parameters = {
        column_indexer['識別ID']: {'NORMAL': 'PWL'}
    }

    with api_request.send_post(apiv1.XCommand.FILTER, parameters) as api_response:
        json_object = api_response.body_as_json_object

    print()
    for row in json_object['resultdata']['CONTENTS']['BODY']:
        print(row[column_indexer['識別ID']])
