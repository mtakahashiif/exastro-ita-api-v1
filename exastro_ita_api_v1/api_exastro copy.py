import functools

from typing import *




class DefaultValuesHandlerFactory:
    pass


class ApiExastro:
    def __init__(self, config: dict = {}) -> None:
        self.__api_context = ApiContext(config)


    @property
    def api_context(self):
        return self.__api_context


    def get_indexer(self, menu_id: str) -> dict[str, int]:
        api_request = self.api_context.create_api_request(menu_id)
        
        return api_request.indexer


    def __get_entry_handler(self, data: dict, key, default_handler_factory):
        value = data.get(key)

        if isinstance(value, Mapping):
            handler = default_handler_factory(value)
        elif callable(value):
            handler = value
        else:
            raise ApiException(f'The value of the key "{key}" must be dict or callable. {type(value)}')
        
        return handler


    def add_records(self, menu_id: str, records: Union[dict[str, str], list[dict[str, str]]]) -> None:
        if not isinstance(records, Sequence):
            records = [records]

        api_request = self.api_context.create_api_request(menu_id)
        indexer = api_request.indexer

        edit_parameter_builder = api_request.create_edit_parameter_builder()

        for record in records:
            edit_record = edit_parameter_builder.create_edit_record(実行処理種別.登録)

            values = 

            for key, value in record.items():
                if not key in indexer.keys():
                    raise apiv1.ApiException(f'Invalid key "{key}" for the menu "{menu_id}". Valid keys are {list(indexer.keys())}')
                
                edit_record[key] = value

            edit_parameter_builder.add(edit_record)

        with api_request.send_post(apiv1.XCommand.EDIT, edit_parameter_builder.generate()) as api_response:
            json_object = api_response.body_as_json_object
            print(json.dumps(json_object, ensure_ascii=False, indent=4))
    

    def __get_selector(self, updator):
        selector = updator['selector']

        if isinstance(selector, Mapping):
            selector = SimpleSelector(selector)

        if not callable(selector):
            raise ApiException(f'Selector must be dict or callable. {type(selector)}')
        
        return selector


    def __get_replacer(self, updator):
        replacer = updator['replacer']

        if isinstance(replacer, Mapping):
            replacer = SimpleReplacer(replacer)

        if not callable(replacer):
            raise ApiException(f'Replacer must be dict or callable. {type(replacer)}')
        
        return replacer


    def update_records(self, menu_id: str, updators: Union[dict, list[dict]], filter: dict = {'1': {'NORMAL': '0'}}) -> None:
        if not isinstance(updators, Sequence):
            updators = [updators]

        api_request = self.api_context.create_api_request(menu_id)
        indexer = api_request.indexer

        with api_request.send_post(apiv1.XCommand.FILTER_DATAONLY, filter) as api_response:
            json_object = api_response.body_as_json_object

        original_records = json_object['resultdata']['CONTENTS']['BODY']
        
        updated_records: dict[str, EditRecord] = {}
        for updator in updators:
            selector = self.__get_selector(updator)

            selected_records = selector(
                indexer=indexer,
                original_records=original_records,
                multiple_selection=updator.get('multiple-selection', False)
            )

            replacer = self.__get_replacer(updator)

            replacer(indexer, selected_records, updated_records)

        edit_parameter_builder = EditParameterBuilder(indexer)
        for id in sorted(updated_records.keys()):
            edit_parameter_builder.add(updated_records[id])

        with api_request.send_post(apiv1.XCommand.EDIT, edit_parameter_builder.generate()) as api_response:
            json_object = api_response.body_as_json_object
            print(json.dumps(json_object, ensure_ascii=False, indent=4))



class SimpleSelector:
    def __init__(self, column_values: dict[str, str]):
        self.__column_values = column_values


    def __call__(self, indexer: dict[str, int], original_records: list[list[str]], multiple_selection: bool = False) -> list[list[str]]:
        selected_records: dict[str, list[str]] = {}
        for original_record in original_records:
            selected: bool = True
            for column_name, column_value in self.__column_values.items():
                column_index = indexer[column_name]

                if original_record[column_index] != column_value:
                    selected = False
                    break

            if selected:
                selected_records[original_record[CommonIndex.ID]] = original_record

        if not multiple_selection and len(selected_records) > 1:
            raise ApiException(f'Multiple records are selected. {list(selected_records.values)}')
    
        return sorted(selected_records.values(), key=lambda record: record[CommonIndex.ID])


class ReplacerBase:
    def __init__(self):
        pass

    
    def _get_updated_record(self, indexer: dict[str, int], updated_records: dict[str, EditRecord], selected_record: list[str]):
        updated_record = updated_records.get(selected_record[CommonIndex.ID])
        if updated_record is None:
            updated_record = EditRecord(indexer, 実行処理種別.更新, selected_record)
            updated_records[updated_record.id] = updated_record
        
        return updated_record


class SimpleReplacer(ReplacerBase):
    def __init__(self, column_values: dict[str, str]):
        self.__column_values = column_values


    def __call__(self, indexer: dict[str, int], selected_records: list[str], updated_records: dict[str, EditRecord]) -> None:
        for selected_record in selected_records:
            updated_record = self._get_updated_record(indexer, updated_records, selected_record)

            for column_name, column_value in self.__column_values.items():
                updated_record[column_name] = column_value