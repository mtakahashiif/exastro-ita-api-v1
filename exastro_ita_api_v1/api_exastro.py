import abc
import json
import exastro_ita_api_v1 as apiv1

from typing import *


class InputDataContext:
    def __init__(self, menu_id: str, indexer: dict[str, int]):
        self.menu_id = menu_id
        self.indexer = indexer


class InputDataEntryGenerator(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def __call__(self, context: InputDataContext) -> list[dict]:
        raise NotImplementedError()


class DefaultGenerator(InputDataEntryGenerator):
    def __init__(self, input_data_entry):
        self.__input_data_entry = input_data_entry


    def __call__(self, context: InputDataContext) -> list[dict]:
        return [self.__input_data_entry]


class SequencedTemplateGenerator(InputDataEntryGenerator):
    def __init__(self, sequence_numbers: Iterable[Any], input_data_entry: dict) -> None:
        self.__sequence_numbers = sequence_numbers
        self.__input_data_entry = input_data_entry


    def __copy(self, context: InputDataContext, input_data_element: dict, sequence_number: int) -> dict:
        result = {}
        
        for key, value in input_data_element.items():
            if isinstance(value, str):
                try:
                    value = value.format_map({'sequence_number': sequence_number})
                except KeyError as e:
                    print(str(e))   # todo logging
            elif isinstance(value, dict):
                value = self.__copy(context, value, sequence_number)
            
            result[key] = value

        return result


    def __call__(self, context: InputDataContext) -> list[dict]:
        result = []

        for sequence_number in self.__sequence_numbers:
            result.append(self.__copy(context, self.__input_data_entry, sequence_number))

        return result


def default_generator(input_data_entry: dict):
    return DefaultGenerator(input_data_entry)


def sequenced_template(sequence_numbers: Iterable[Any], input_data_entry: dict):
    return SequencedTemplateGenerator(sequence_numbers, input_data_entry)


class DefaultRecordHandlerFactory:
    def __call__(self, data: dict) -> None:
        pass


class DefaultValuesHandlerFactory:
    pass


class DefaultFilesHandlerFactory:
    pass


class ApiExastro:
    def __init__(self, config: dict = {}) -> None:
        self.__api_context = apiv1.ApiContext(config)


    @property
    def api_context(self):
        return self.__api_context


    def get_indexer(self, menu_id: str) -> dict[str, int]:
        api_request = self.api_context.create_api_request(menu_id)
        
        return api_request.indexer


    def __call_input_data_entry_generator(self, input_data_context: InputDataContext, input_data_entry: Any) -> list[dict]:
        if isinstance(input_data_entry, Mapping):
            input_data_entry_generator = default_generator(input_data_entry)
        elif callable(input_data_entry):
            input_data_entry_generator = input_data_entry
        else:
            raise apiv1.ApiException(f'Input data entry must be dict or callable. {type(input_data_entry)}')
        
        return input_data_entry_generator(input_data_context)


    def __process_body_in_input_data_entry(self, context: InputDataContext, input_data_entry: dict, edit_record: apiv1.EditRecord) -> None:
        body = input_data_entry.get('body')

        if body:
            for key, value in body.items():
                if not key in context.indexer.keys():
                    raise apiv1.ApiException(f'Invalid key "{key}" for the menu "{context.menu_id}". Valid keys are {list(context.indexer.keys())}')
        
                edit_record[key] = value


    def __process_upload_file_in_input_data_entry(self, context: InputDataContext, input_data_entry: dict, edit_record: apiv1.EditRecord) -> None:
        fileupload = input_data_entry.get('upload_file')

        if fileupload:
            for key, value in fileupload.items():
                if not key in context.indexer.keys():
                    raise apiv1.ApiException(f'Invalid key "{key}" for the menu "{context.menu_id}". Valid keys are {list(context.indexer.keys())}')
        
                edit_record.file_record[key] = value


    def add_records(self, menu_id: str, input_data_entries: Union[dict[str, str], list[dict[str, str]]]) -> None:
        # 引数の型の調整
        if not isinstance(input_data_entries, Sequence):
            input_data_entries = [input_data_entries]

        # APIリクエストの生成
        api_request = self.api_context.create_api_request(menu_id)

        # パラメータのビルダの生成
        edit_parameter_builder = api_request.create_edit_parameter_builder()

        # コンテキストの生成
        input_data_context: InputDataContext = InputDataContext(
            menu_id = menu_id,
            indexer = api_request.indexer
        )

        # input data entry毎に処理
        for input_data_entry in input_data_entries:
            # ハンドラを実行し、加工後のinput data entryを取得
            entries = self.__call_input_data_entry_generator(input_data_context, input_data_entry)

            # 加工後のinput data entry毎に処理
            for entry in entries:
                edit_record = edit_parameter_builder.create_edit_record(apiv1.実行処理種別.登録)

                self.__process_body_in_input_data_entry(input_data_context, entry, edit_record)
                self.__process_upload_file_in_input_data_entry(input_data_context, entry, edit_record)

                edit_parameter_builder.add(edit_record)

        # API呼び出しにより、Exastro IT Automationにパラメータを登録
        with api_request.send_post(apiv1.XCommand.EDIT, edit_parameter_builder.generate()) as api_response:
            json_object = api_response.body_as_json_object
            print(json.dumps(json_object, ensure_ascii=False, indent=4))
