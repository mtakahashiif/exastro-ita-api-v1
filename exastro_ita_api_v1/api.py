import abc
import base64
import http.client
import http.cookiejar
import json
import os.path
import urllib.error
import urllib.parse
import urllib.request
import urllib.response
import time

from collections.abc import Iterator, Mapping
from typing import *

from .constants import *


_T = TypeVar('_T')


class ApiException(Exception):
    pass


BlurDict: TypeAlias = dict[str, _T] | dict[int, _T] | list[_T] | None
StrBlurDict: TypeAlias = BlurDict[str]


def get_config_from_env():
    return {key: value for key, value in os.environ.items() if key.startswith('EXASTRO_')}


def to_dict(collection: BlurDict[_T]) -> dict[str, _T]:
    if collection is None:
        it = {}.items()
    elif isinstance(collection, dict):
        it = collection.items()
    elif isinstance(collection, list):
        it = enumerate(collection)
    else:
        raise ApiException(f'Unknown type {type(collection)}. Valid types are dict and list.')

    return {str(key): value for key, value in it}


class Indexer(Mapping[str, str]):
    def __init__(self, menu_id: str, column_names: StrBlurDict) -> None:
        self.__menu_id = menu_id
        self.__forward_mapping = {column_name: index for index, column_name in to_dict(column_names).items()}
        self.__reverse_mapping = {index: column_name for column_name, index in self.__forward_mapping.items()}


    @property
    def menu_id(self) -> str:
        return self.__menu_id


    def __getitem__(self, key: str) -> str:
        try:
            return self.__forward_mapping.__getitem__(key)
        except KeyError as e:
            raise KeyError(f'Invalid key "{key}" for the menu "{self.menu_id}". Valid keys are {list(self.__forward_mapping.keys())}') from e


    def __iter__(self) -> Iterator[str]:
        return self.__forward_mapping.__iter__()


    def __len__(self) -> int:
        return self.__forward_mapping.__len__()


    def to_column_name(self, index: str) -> str:
        try:
            return self.__reverse_mapping[index]
        except KeyError as e:
            raise KeyError(f'Invalid index "{index}" for the menu "{self.menu_id}". Valid index are 0 to {len(self.__reverse_mapping)}') from e


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


class EventHook:
    def on_request(
        self,
        api_request: 'ApiRequest',
        http_method: str,
        xcommand: str,
        headers: dict[str, str],
        params: dict[str, str],
        wait_func: Callable,
        wait_func_args: dict
    ) -> None: ...


    def on_response(
        self,
        api_request: 'ApiRequest',
        api_response: 'ApiResponse'
    ) -> None: ...


    def before_wait_func(
        self,
        api_request: 'ApiRequest',
        wait_func: Callable,
        wait_func_args: dict
    ) -> None: ...


    def after_wait_func(
        self,
        api_request: 'ApiRequest',
        wait_func: Callable,
        wait_func_args: dict,
        wait_duration: float
    ) -> None: ...


class ApiResponse(IndexerMixin):
    def __init__(
        self,
        api_request: 'ApiRequest',
        http_method: str,
        xcommand: str,
        params: dict,
        response: http.client.HTTPResponse,
        exception: Exception
    ) -> None:
        self.__api_request = api_request
        self.__http_method = http_method
        self.__xcommand = xcommand
        self.__params = params
        self.__response: http.client.HTTPResponse = response
        self.__exception = exception
        self.__body = None
        self.__json_object = None


    def __enter__(self):
        return self


    def __exit__(self, exc_type, exc_value, traceback):
        if not self.__response.isclosed():
            self.__response.close()
            self.__body = None
            self.__json_object = None


    @property
    def api_request(self) -> 'ApiRequest':
        return self.__api_request
    

    @property
    def api_context(self) -> 'ApiContext':
        return self.__api_request.api_context
    

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
    def params(self) -> dict:
        return self.__params
    
    
    @property
    def exception(self) -> Exception:
        return self.__exception


    @property
    def status(self) -> int:
        return self.__response.status


    @property
    def body(self) -> bytes:
        if self.__body is None:
            self.__body = self.__response.read()

        return self.__body


    @property
    def json_object(self) -> dict:
        if self.__json_object is None:
            try:
                self.__json_object = json.loads(self.body)
            except json.decoder.JSONDecodeError:
                raise ApiException(f'Response body is not JSON: {self.body.decode()}')

        return self.__json_object


class ApiRequest(IndexerMixin):
    def __init__(
        self,
        api_context: 'ApiContext',
        url: str,
        menu_id,
        default_wait_func: Callable = None
    ) -> None:
        self.__api_context: ApiContext = api_context
        self.__url: str = url
        self.__credential: str = base64.b64encode((api_context.username + ':' + api_context.password).encode()).decode()
        self.__menu_id: str = menu_id
        self.__indexer: Indexer = None
        self.__options_table: dict[str, dict[str, str]] = None
        self.__default_wait_func = default_wait_func if default_wait_func else lambda _, seconds=3: time.sleep(seconds)


    @property
    def api_context(self) -> 'ApiContext':
        return self.__api_context


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
            with self.send_post(xcommand=XCommand.INFO) as api_response:
                self.__indexer = Indexer(
                    menu_id=self.menu_id,
                    column_names=api_response.json_object['resultdata']['CONTENTS']['INFO']
                )

        return self.__indexer


    @property
    def options_table(self) -> dict:
        if self.__options_table is None:
            with self.send_post(xcommand=XCommand.LIST_OPTIONS) as api_response:
                body = api_response.json_object['resultdata']['CONTENTS']['BODY']

            options_table: dict[str, dict[str, str]] = {}
            column_names = to_dict(body[0])
            for column_index, options in to_dict(body[1]):
                options = to_dict(options)
                if options:
                    options_table[column_names[column_index]] = options

            self.__options_table = options_table

        return self.__options_table


    def send_get(
        self,
        *,
        wait_func: Callable = None,
        wait_func_args: dict = {}
    ) -> ApiResponse:
        return self.__invoke(
            http_method=HttpMethod.GET,
            xcommand=None,
            headers={
                'Content-Type': 'application/json',
                'Authorization': self.credential
            },
            wait_func=wait_func,
            wait_func_args=wait_func_args
        )


    def send_post(
        self,
        xcommand: str,
        params: dict = None,
        *,
        wait_func: Callable = None,
        wait_func_args: dict = {}
    ) -> ApiResponse:
        return self.__invoke(
            http_method=HttpMethod.POST,
            xcommand=xcommand,
            headers={
                'Content-Type': 'application/json',
                'Authorization': self.credential,
                'X-Command': xcommand
            },
            params=params,
            wait_func=wait_func,
            wait_func_args=wait_func_args
        )


    def __invoke(
        self,
        http_method: str,
        xcommand: str,
        headers: dict[str, str],
        params: dict = None,
        *,
        wait_func: Callable,
        wait_func_args: dict
    ) -> ApiResponse:
        
        self.api_context.event_handler.on_request(
            api_request=self,
            http_method=http_method,
            xcommand=xcommand,
            headers=headers,
            params=params,
            wait_func=wait_func,
            wait_func_args=wait_func_args
        )

        request = urllib.request.Request(
            url=self.url,
            method=http_method,
            headers=headers,
            data=json.dumps(params, ensure_ascii=False).encode() if params is not None else None
        )

        response = exception = None
        try:
            response = urllib.request.urlopen(request)
        except urllib.error.HTTPError as e:
            response = e
        except Exception as e:
            exception = e

        api_response = ApiResponse(
            api_request=self,
            http_method=http_method,
            xcommand=xcommand,
            params=params,
            response=response,
            exception=exception
        )

        self.api_context.event_handler.on_response(
            api_request=self,
            api_response=api_response
        )

        # 更新系の処理であれば待ち合わせ関数を呼び出す
        if xcommand in [XCommand.EDIT, XCommand.EXECUTE, XCommand.UPLOAD, XCommand.UPLOAD_SPREADSHEET]:
            # TODO エラーが発生している場合は待ち合わせしない
            wait_func = wait_func if wait_func else self.__default_wait_func

            self.api_context.event_handler.before_wait_func(
                api_request=self,
                wait_func=wait_func,
                wait_func_args=wait_func_args
            )

            begin_time = time.time()
            wait_func(api_response, **wait_func_args)
            end_time = time.time()

            self.api_context.event_handler.after_wait_func(
                api_request=self,
                wait_func=wait_func,
                wait_func_args=wait_func_args,
                wait_duration=end_time - begin_time
            )

        return api_response


class WebResponse:
    def __init__(
        self,
        response: http.client.HTTPResponse | urllib.error.HTTPError
    ) -> None:
        # Response instance returned from urllib "opener" must not be held because it will be closed.
        self.__response_type = type(response)
        self.__headers = list(response.getheaders())
        self.__body = response.read().decode('utf-8')
        self.__code = response.getcode()


    @property
    def response_type(self) -> type:
        return self.__response_type


    @property
    def headers(self) -> list[tuple[str, str]]:
        return self.__headers


    @property
    def body(self) -> str:
        return self.__body


    @property
    def code(self) -> Any:
        return self.__code


class WebRequest:
    def __init__(
        self,
        api_context: 'ApiContext',
        menu_id: str,
        *,
        default_wait_func: Callable = None
    ) -> None:
        self.__api_context = api_context
        self.__menu_id = menu_id
        self.__default_wait_func = default_wait_func
        self.__cookie_jar = http.cookiejar.CookieJar()
        self.__opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.__cookie_jar))
        self.__referer = None


    @property
    def api_context(self) -> 'ApiContext':
        return self.__api_context


    def __send(
        self,
        method: str,
        path: str,
        queries: dict[str, str],
        parameters: dict[str, str] = None,
        *,
        wait_func: Callable = None,
        wait_func_args: dict = {},
        override_queries: bool = False
    ) -> WebResponse:
        url = urllib.parse.urlunparse((
            self.api_context.protocol,
            self.api_context.host + ':' + self.api_context.port,
            path if path else '/default/menu/01_browse.php',
            '',
            urllib.parse.urlencode(({'no': self.__menu_id} if not override_queries else {}) | (queries if queries else {})),
            ''
        ))

        data = urllib.parse.urlencode(parameters).encode() if parameters else None

        request_header = {
            **({'Referer': self.__referer} if self.__referer else {}),
            **({'Content-Type': 'application/x-www-form-urlencoded'} if data else {})
        }

        request = urllib.request.Request(
            url=url,
            data=data,
            headers=request_header,
            method=method
        )

        def send_request() -> http.client.HTTPResponse | urllib.error.HTTPError:
            try:
                response = self.__opener.open(request)
                self.__referer = url
            except urllib.error.HTTPError as e:
                response = e
                self.__referer = url
            except Exception as e:
                raise e
            
            return response
        
        with send_request() as response:
            web_response = WebResponse(response)

        wait_func = wait_func if wait_func else self.__default_wait_func
        if wait_func:
            wait_func(web_response, **(wait_func_args if wait_func_args else {}))
        
        return web_response


    def send_get(
        self,
        path: str = None,
        queries: dict[str, str] = None,
        *,
        override_queries: bool = False
    ) -> WebResponse:
        return self.__send(
            method='GET',
            path=path,
            queries=queries,
            override_queries=override_queries
        )


    def send_post(
        self,
        path: str = None,
        queries: dict[str, str] = None,
        parameters: dict[str, str] = None,
        *,
        override_queries: bool = False
    ) -> WebResponse:
        return self.__send(
            method='POST',
            path=path,
            queries=queries,
            parameters=parameters,
            override_queries=override_queries
        )


class ApiContext:
    def __init__(
        self,
        config: dict = {},
        *,
        default_wait_func: Callable = None,
        event_hook: EventHook = EventHook()
    ) -> None:
        self.__protocol: str = config.get('EXASTRO_PROTOCOL', 'http')
        self.__host: str = config.get('EXASTRO_HOST', 'localhost')
        self.__port: str = config.get('EXASTRO_PORT', '8080')
        self.__username: str = config.get('EXASTRO_USERNAME')
        self.__password: str = config.get('EXASTRO_PASSWORD')
        self.__default_wait_func = default_wait_func
        self.__event_handler = event_hook


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


    @property
    def default_wait_func(self) -> Callable:
        return self.__default_wait_func


    @property
    def event_handler(self) -> EventHook:
        return self.__event_handler


    def create_api_request(
        self,
        menu_id: str,
        *,
        default_wait_func: Callable = None
    ) -> ApiRequest:
        return ApiRequest(
            self,
            url=urllib.parse.urlunparse((
                self.protocol,
                self.host + ':' + self.port,
                '/default/menu/07_rest_api_ver1.php',
                '',
                urllib.parse.urlencode({'no': menu_id}),
                ''
            )),
            menu_id=menu_id,
            default_wait_func=default_wait_func if default_wait_func else self.default_wait_func
        )


    def create_web_request(self, menu_id: str) -> tuple[WebRequest, WebResponse]:
        from lxml import html

        web_request = WebRequest(
            api_context=self,
            menu_id=menu_id
        )

        web_response = web_request.send_get()
        
        if int(web_response.code) == 401:
            web_response = web_request.send_post(
                path='/common/common_auth.php',
                queries={
                    'login': ''
                },
                parameters={
                    'status': '0'
                }
            )
        
            html_doc = html.fromstring(web_response.body)
            csrf_token = html_doc.xpath('string(//input[@name="csrf_token"]/@value)')
            
            web_response = web_request.send_post(
                path='/common/common_auth.php',
                queries={
                    'login': ''
                },
                parameters={
                    'username': self.username,
                    'password': self.password,
                    'csrf_token': csrf_token,
                    'login': r'%E3%83%AD%E3%82%B0%E3%82%A4%E3%83%B3'
                }
            )

        return web_request, web_response


class ApiParametersCreator(Protocol):
    def __call__(self, indexer: Indexer) -> dict: ...
