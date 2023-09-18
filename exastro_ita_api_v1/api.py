import base64
import http.client
import json
import os.path
import urllib.parse
import urllib.request
import urllib.response

from typing import *


class HttpMethod:
    GET = 'GET'
    POST = 'POST'


class XCommand:
    CANCEL = 'CANCEL'
    COMPARE = 'COMPARE'
    DOWNLOAD = 'DOWNLOAD'
    DOWNLOAD_SPREADSHEET = 'DOWNLOAD_SPREADSHEET'
    EDIT = 'EDIT'
    EXECUTE = 'EXECUTE'
    FILTER = 'FILTER'
    FILTER_DATAONLY = 'FILTER_DATAONLY'
    INFO = 'INFO'
    LIST_OPTIONS = 'LIST_OPTIONS'
    RELEASE = 'RELEASE'
    SCRAM = 'SCRAM'
    UPLOAD = 'UPLOAD'
    UPLOAD_SPREADSHEET = 'UPLOAD_SPREADSHEET'


class MenuId:
    class Exastro_IT_Automation:
        ログイン画面 = '2100000101'
        システムエラー = '2100000102'
        不正操作によるアクセス警告 = '2100000103'
        不正端末からのアクセス警告 = '2100000104'
        ログインID一覧 = '2100000105'
        パスワード変更 = '2100000106'
        アカウントロックエラー = '2100000107'
    
    class 管理コンソール:
        システム設定 = '2100000202'
        IPアドレスフィルタ管理 = '2100000203'
        メニューグループ管理 = '2100000204'
        メニュー管理 = '2100000205'
        ロール管理 = '2100000207'
        ユーザ管理 = '2100000208'
        ロール_メニュー紐付管理 = '2100000209'
        ロール_ユーザ紐付管理 = '2100000210'
        オペレーション削除管理 = '2100000214'
        ファイル削除管理 = '2100000215'
        シーケンス管理 = '2100000216'
        ADグループ判定 = '2100000221'
        ADユーザ判定 = '2100000222'
        SSO基本情報管理 = '2100000231'
        SSO属性情報管理 = '2100000232'
        バージョン確認 = '2100000299'

    class エクスポート_インポート:
        メニューエクスポート = '2100000211'
        メニューインポート = '2100000212'
        メニューエクスポート_インポート管理 = '2100000213'
        Excel一括エクスポート = '2100000329'
        Excel一括インポート = '2100000330'
        Excel一括エクスポート_インポート管理 = '2100000331'

    class 基本コンソール:
        機器一覧 = '2100000303'
        オペレーション一覧 = '2100000304'
        Movement一覧 = '2100000305'
        ER図表示 = '2100000326'
        ER図メニュー管理 = '2100000327'
        ER図項目管理 = '2100000328'
        紐付対象メニュー = '2100000501'
        紐付対象メニューテーブル管理 = '2100000502'
        紐付対象メニューカラム管理 = '2100000503'

    class Symphony:
        Symphonyクラス編集 = '2100000306'
        Symphonyクラス一覧 = '2100000307'
        Symphony作業実行 = '2100000308'
        Symphony作業確認 = '2100000309'
        Symphony作業一覧 = '2100000310'
        Symphony紐付Movement一覧 = '2100000311'
        Movementインスタンス一覧 = '2100000312'
        Symphonyインターフェース情報 = '2100000313'
        Symphony定期作業実行 = '2100000314'

    class Ansible共通:
        インターフェース情報 = '2100040702'
        ファイル管理 = '2100040703'
        テンプレート管理 = '2100040704'
        グローバル変数管理 = '2100040706'
        共通変数利用リスト = '2100040707'
        Ansible_Automation_Controller_ホスト一覧 = '2100040708'
        収集インターフェース情報 = '2100040709'
        収集項目値管理 = '2100040710'

    class Ansible_Legacy:
        Movement一覧 = '2100020103'
        Playbook素材集 = '2100020104'
        Movement_Playbook紐付 = '2100020105'
        変数名一覧 = '2100020106'
        Movement変数紐付管理 = '2100020107'
        作業対象ホスト = '2100020108'
        代入値管理 = '2100020109'
        作業実行 = '2100020111'
        作業状態確認 = '2100020112'
        作業管理 = '2100020113'
        代入値自動登録設定 = '2100020115'

    class Ansible_LegacyRole:
        ロールパッケージ管理 = '2100020303'
        ロール名管理 = '2100020304'
        ロール変数名管理 = '2100020305'
        Movement一覧 = '2100020306'
        Movement_ロール紐付 = '2100020307'
        変数名一覧 = '2100020308'
        Movement変数紐付管理 = '2100020309'
        作業対象ホスト = '2100020310'
        代入値管理 = '2100020311'
        作業実行 = '2100020312'
        作業状態確認 = '2100020313'
        作業管理 = '2100020314'
        メンバー変数管理 = '2100020315'
        代入値自動登録設定 = '2100020316'
        変数具体値管理 = '2100020317'
        多段変数メンバー管理 = '2100020318'
        変数ネスト管理 = '2100020319'
        多段変数配列組合せ管理 = '2100020320'
        読替変数一覧 = '2100020322'

    class AnsiblePioneer:
        OS種別マスタ = '2100000302'
        Movement一覧 = '2100020203'
        対話種別リスト = '2100020204'
        対話ファイル素材集 = '2100020205'
        Movement_対話種別紐付 = '2100020206'
        変数名一覧 = '2100020207'
        Movement変数紐付管理 = '2100020208'
        作業対象ホスト = '2100020209'
        代入値管理 = '2100020210'
        作業実行 = '2100020211'
        作業状態確認 = '2100020212'
        作業管理 = '2100020213'
        代入値自動登録設定 = '2100020214'

    class Terraform:
        インターフェース情報 = '2100080001'
        Organizations管理 = '2100080002'
        Workspaces管理 = '2100080003'
        Movement一覧 = '2100080004'
        Module素材集 = '2100080005'
        Policies管理 = '2100080006'
        Movement_Module紐付 = '2100080007'
        代入値管理 = '2100080008'
        作業実行 = '2100080009'
        作業状態確認 = '2100080010'
        作業管理 = '2100080011'
        PolicySets管理 = '2100080012'
        PolicySet_Policy紐付管理 = '2100080013'
        PolicySet_Workspace紐付管理 = '2100080014'
        代入値自動登録設定 = '2100080015'
        Module変数紐付管理 = '2100080016'
        連携先Terraform管理 = '2100080017'
        Movement変数紐付管理 = '2100080018'
        メンバー変数管理 = '2100080019'
        変数ネスト管理 = '2100080020'

    class CI_CD_for_IaC:
        リモートリポジトリ = '2100120001'
        リモートリポジトリ資材 = '2100120002'
        資材紐付 = '2100120003'
        インターフェース情報 = '2100120004'
        登録アカウント = '2100120005'

    class メニュー作成:
        メニュー定義一覧 = '2100160001'
        メニュー項目作成情報 = '2100160002'
        メニュー作成実行 = '2100160003'
        メニュー作成履歴 = '2100160004'
        メニュー_テーブル紐付 = '2100160005'
        他メニュー連携 = '2100160007'
        カラムグループ管理 = '2100160008'
        メニュー_縦_作成情報 = '2100160009'
        メニュー縦横変換管理 = '2100160010'
        メニュー定義_作成 = '2100160011'
        参照項目情報 = '2100160012'
        選択1 = '2100160016'
        選択2 = '2100160017'
        一意制約_複数項目_作成情報 = '2100160018'

    class ホストグループ管理:
        ホストグループ一覧 = '2100170001'
        ホストグループ親子紐付 = '2100170002'
        ホスト紐付管理 = '2100170003'
        ホストグループ分割対象 = '2100170004'

    class Conductor:
        Conductorインターフェース情報 = '2100180001'
        Conductorクラス一覧 = '2100180002'
        Conductorクラス編集 = '2100180003'
        Conductor作業実行 = '2100180004'
        Conductor作業確認 = '2100180005'
        Conductor作業一覧 = '2100180006'
        Conductor紐付Node一覧 = '2100180007'
        Node紐付Terminal一覧 = '2100180008'
        Conductorインスタンス一覧 = '2100180009'
        Nodeインスタンス一覧 = '2100180010'
        Conductor定期作業実行 = '2100180011'
        Conductor通知先定義 = '2100180012'

    class 比較:
        比較定義 = '2100190001'
        比較定義詳細 = '2100190002'
        比較実行 = '2100190003'

    class Terraform_CLI:
        インターフェース情報 = '2100200001'
        Workspaces管理 = '2100200002'
        Movement一覧 = '2100200003'
        Module素材集 = '2100200004'
        Movement_Module紐付 = '2100200005'
        変数ネスト管理 = '2100200006'
        代入値自動登録設定 = '2100200007'
        代入値管理 = '2100200008'
        作業実行 = '2100200009'
        作業状態確認 = '2100200010'
        作業管理 = '2100200011'
        Module変数紐付管理 = '2100200012'
        メンバー変数管理 = '2100200013'
        Movement変数紐付管理 = '2100200014'


class ApiException(Exception):
    pass


class ApiResponse:
    def __init__(self, menu_id: str, http_method: str, xcommand: str, response: http.client.HTTPResponse):
        self.__menu_id: str = menu_id
        self.__http_method: str = http_method
        self.__xcommand: str = xcommand
        self.__response: http.client.HTTPResponse = response
        self.__body = None
        self.__body_as_json_object = None


    def __enter__(self):
        return self


    def __exit__(self, exc_type, exc_value, traceback):
        if not self.__response.isclosed():
            self.__response.close()


    @property
    def menu_id(self) -> str:
        return self.__menu_id


    @property
    def http_method(self) -> str:
        return self.__http_method


    @property
    def xcommand(self) -> str:
        return self.__xcommand
    

    @property
    def status(self) -> int:
        return self.__response.status


    @property
    def body(self) -> bytes:
        if self.__body is None:
            self.__body = self.__response.read()

        return self.__body


    @property
    def body_as_json_object(self) -> dict:
        if self.__body_as_json_object is None:
            self.__body_as_json_object = json.loads(self.body)

        return self.__body_as_json_object


    @property
    def column_indexer(self) -> dict:
        if self.xcommand is XCommand.FILTER:
            column_names = self.body_as_json_object['resultdata']['CONTENTS']['BODY'][0]
        elif self.xcommand is XCommand.INFO:
            column_names = self.body_as_json_object['resultdata']['CONTENTS']['INFO']
        else:
            raise ApiException(f'Response with X-Command "{self.xcommand}" does not have column names.')

        return {column_name: index for index, column_name in enumerate(column_names)}


class ApiRequest:
    def __init__(self, url: str, username: str, password: str, menu_id) -> None:
        self.__url: str = url
        self.__credential: str = base64.b64encode((username + ':' + password).encode()).decode()
        self.__menu_id: str = menu_id


    @property
    def url(self) -> str:
        return self.__url


    @property
    def credential(self) -> str:
        return self.__credential


    @property
    def menu_id(self) -> str:
        return self.__menu_id

    def send_get(self) -> ApiResponse:
        return self.__invoke(
            http_method = HttpMethod.GET,
            xcommand = None,
            headers = {'Content-Type': 'application/json', 'Authorization': self.credential},
            parameters = None
        )


    def send_post(self, xcommand: str, parameters: Union[str, dict] = None) -> ApiResponse:
        return self.__invoke(
            http_method = HttpMethod.POST,
            xcommand = xcommand,
            headers = {'Content-Type': 'application/json', 'Authorization': self.credential, 'X-Command': xcommand},
            parameters = parameters
        )


    def __invoke(self, http_method: str, xcommand: str, headers: dict[str, str], parameters: Union[str, dict]) -> ApiResponse:
        if isinstance(parameters, str):
            data = parameters.encode()
        elif isinstance(parameters, Dict):
            data = json.dumps(parameters, ensure_ascii=False).encode()
        else:
            data = None

        request = urllib.request.Request(
            url = self.url,
            method = http_method,
            headers = headers,
            data = data
        )

        return ApiResponse(
            menu_id = self.menu_id,
            http_method = http_method,
            xcommand = xcommand,
            response = urllib.request.urlopen(request)
        )


class ApiContext:
    def __init__(self, config: dict = {}) -> None:
        def get_value(config: dict, key: str, default_value: str = None) -> str:
            return config.get(key, os.getenv(key, default_value))

        self.__protocol: str = get_value(config, 'EXASTRO_PROTOCOL', 'http')
        self.__host: str = get_value(config, 'EXASTRO_HOST', 'localhost')
        self.__port: str = get_value(config, 'EXASTRO_PORT', '8080')
        self.__username: str = get_value(config, 'EXASTRO_USERNAME')
        self.__password: str = get_value(config, 'EXASTRO_PASSWORD')


    @property
    def protocol(self) -> str:
        return self.__protocol


    @property
    def host(self) -> str:
        return self.__host


    @property
    def port(self) -> str:
        return self.__port


    @property
    def username(self) -> str:
        return self.__username


    @property
    def password(self) -> str:
        return self.__password


    def create_api_request(self, menu_id: str) -> ApiRequest:
        return ApiRequest(
            url = urllib.parse.urlunparse((
                self.protocol,
                self.host + ':' + self.port,
                '/default/menu/07_rest_api_ver1.php',
                '',
                urllib.parse.urlencode({'no': menu_id}),
                ''
            )),
            username = self.username,
            password = self.password,
            menu_id = menu_id
        )
