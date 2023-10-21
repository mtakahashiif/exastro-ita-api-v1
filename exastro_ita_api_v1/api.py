import abc
import base64
import collections.abc
import http.client
import json
import os.path
import urllib.parse
import urllib.request
import urllib.response

from collections.abc import Iterator, Mapping
from typing import *

from .common import *


class Indexer(Mapping[str, int]):
    def __init__(self, menu_id: str, column_names: list[str]) -> None:
        self.__menu_id = menu_id
        self.__mapping = {column_name: index for index, column_name in enumerate(column_names)}
        self.__reverse_mapping = {index: column_name for column_name, index in self.__mapping.items()}


    @property
    def menu_id(self) -> str:
        return self.__menu_id


    def __getitem__(self, key: str) -> int:
        try:
            return self.__mapping.__getitem__(key)
        except KeyError as e:
            raise KeyError(f'Invalid key "{key}" for the menu "{self.menu_id}". Valid keys are {list(self.__mapping.keys())}') from e


    def __iter__(self) -> Iterator[str]:
        return self.__mapping.__iter__()


    def __len__(self) -> int:
        return self.__mapping.__len__()


    def to_column_name(self, index: int):
        try:
            return self.__reverse_mapping[index]
        except KeyError as e:
            raise KeyError(f'Invalid index "{index}" for the menu "{self.menu_id}". Valid index are 0 to {len(self.__reverse_mapping)}') from e


    def sanitize(self, index: Union[int, str], is_named: bool = False) -> int:
        if is_named:
            index = self[index]

        index = int(index)
        if index < 0 or len(self) <= index:
            raise ApiException(f'Invalid index "{index}" for the menu "{self.menu_id}". Valid index range is 0 <= index < {len(self)}')
        
        return index


class IndexerMixin(metaclass = abc.ABCMeta):
    @property
    @abc.abstractmethod
    def indexer(self) -> Indexer:
        raise NotImplementedError()


    @property
    def menu_id(self) -> str:
        return self.indexer.menu_id
    

    def check_acceptable(self, other: 'IndexerMixin') -> None:
        if other.menu_id != self.menu_id:
            raise ApiException(f'menu id "{other.menu_id}", but expected menu id is "{self.menu_id}".')


class ApiResponse(IndexerMixin):
    def __init__(self, api_request: 'ApiRequest', http_method: str, xcommand: str, response: http.client.HTTPResponse):
        self.__api_request: ApiRequest = api_request
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
    def api_request(self) -> 'ApiRequest':
        return self.__api_request
    

    @property
    def indexer(self) -> Indexer:
        return self.api_request.indexer


    @property
    def menu_id(self) -> str:
        return self.api_request.menu_id


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


class ApiRequest(IndexerMixin):
    def __init__(self, url: str, username: str, password: str, menu_id) -> None:
        self.__url: str = url
        self.__credential: str = base64.b64encode((username + ':' + password).encode()).decode()
        self.__menu_id: str = menu_id
        self.__indexer: Indexer = None
        self.__options_table: dict[str, dict[str, str]] = None


    @property
    def url(self) -> str:
        return self.__url


    @property
    def credential(self) -> str:
        return self.__credential


    @property
    def menu_id(self) -> str:
        return self.__menu_id

    @property
    def indexer(self) -> Indexer:
        if self.__indexer is None:
            with self.send_post(XCommand.INFO) as api_response:
                self.__indexer = Indexer(
                    menu_id=self.menu_id,
                    column_names=api_response.body_as_json_object['resultdata']['CONTENTS']['INFO']
                )

        return self.__indexer


    @property
    def options_table(self) -> dict:
        if self.__options_table is None:
            with self.send_post(XCommand.LIST_OPTIONS) as api_response:
                body = api_response.body_as_json_object['resultdata']['CONTENTS']['BODY']

            options_table: dict[str, dict[str, str]] = {}
            column_names: list[str] = body[0]
            for column_index, options in enumerate(body[1]):
                if isinstance(options, collections.abc.Sequence):
                    options = {str(index): option for index, option in enumerate(options)}
                elif isinstance(options, collections.abc.Mapping):
                    options = dict(options)
                else:
                    raise ApiException(f'Unknown type "{type(options)}".')

                if options:
                    options_table[column_names[column_index]] = options

            self.__options_table = options_table

        return self.__options_table


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
            api_request = self,
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
