import abc
import json
import re

from typing import *
from .api import *
from .api_table import *


class Strategy(metaclass = abc.ABCMeta):
    @abc.abstractmethod
    def check_operation_acceptable(self, operation: str) -> None:
        raise NotImplementedError()


    @abc.abstractmethod
    def select_rows(self, context: dict, original_table: Table) -> Iterator[Row]:
        raise NotImplementedError()


    @abc.abstractmethod
    def create_edited_row(self, context: dict, indexer: Indexer, edit_data_entry: dict, selected_row: Row) -> Row:
        raise NotImplementedError()
    

    def create_row(self, indexer: Indexer, body_values: RecordValues, upload_file_values: RecordValues, operation: str) -> Row:
        pass


class RegisterStrategy(Strategy):
    def check_operation_acceptable(self, operation: str) -> None:
        if operation not in [実行処理種別.登録]:
            raise ApiException()


class SelectorStrategy(Strategy):
    def check_operation_acceptable(self, operation: str) -> None:
        if operation not in [実行処理種別.更新, 実行処理種別.廃止, 実行処理種別.復活]:
            raise ApiException()


class SingleConstantRegisterStrategy(RegisterStrategy):
    def select_rows(self, context: dict, original_table: Table) -> Iterator[Row]:
        yield None


    def create_edited_row(self, context: dict, indexer: Indexer, edit_data_entry: dict, selected_row: Row) -> Row:
        return Row(
            indexer = indexer,
            body_values = edit_data_entry.get('body'),
            upload_file_values = edit_data_entry.get('upload_file'),
            operation = edit_data_entry.get('operation'),
            is_named = True
        )


def single_constant_register():
    return SingleConstantRegisterStrategy()


class SequenceRegisterStrategy(RegisterStrategy):
    def __init__(self, iterable: Iterable[Any]) -> None:
        self.__iterable = iterable


    def select_rows(self, context: dict, original_table: Table) -> Iterator[Row]:
        try:
            for sequence in self.__iterable:
                context['sequence'] = sequence
                yield None
        finally:
            del context['sequence']


    def __replace_with_sequence(self, context: dict, values: dict[str, str]) -> dict[str, str]:
        result: dict[str, str] = {}

        if values:
            for key, template in values.items():
                result[key] = eval(f'f"{template}"', {}, {'sequence': context['sequence']})

        return result


    def create_edited_row(self, context: dict, indexer: Indexer, edit_data_entry: dict, selected_row: Row) -> Row:
        return Row(
            indexer = indexer,
            body_values = self.__replace_with_sequence(context, edit_data_entry.get('body')),
            upload_file_values = self.__replace_with_sequence(context, edit_data_entry.get('upload_file')),
            operation = edit_data_entry.get('operation'),
            is_named = True
        )


def sequence_register(iterable: Iterable[Any]):
    return SequenceRegisterStrategy(iterable)


class ExactMatchSelectorStrategy(SelectorStrategy):
    def __init__(self, selector: dict[str, str]) -> None:
        self.__selector = selector


    def select_rows(self, context: dict, original_table: Table) -> Iterator[Row]:
        for original_row in original_table.rows:
            found = True
            for key, value in self.__selector.items():
                if key not in original_row.body.keys() or value != original_row.body[key]:
                    found = False
                    break
            
            if found:
                yield original_row


    def __merge_values(self, context: dict, edited_record: Record, new_values: dict[str, str]) -> None:
        result: dict[str, str] = {}

        if new_values:
            for key, new_value in new_values.items():
                edited_record[key] = new_value

        return result


    def create_edited_row(self, context: dict, indexer: Indexer, edit_data_entry: dict, selected_row: Row) -> Row:
        edited_row = selected_row.clone_for_edit(edit_data_entry.get('operation'))

        self.__merge_values(context, edited_row.body, edit_data_entry.get('body'))
        self.__merge_values(context, edited_row.upload_file, edit_data_entry.get('upload_file'))

        return edited_row


def exact_match_selector(selector: dict[str, str]):
    return ExactMatchSelectorStrategy(selector)


class RegexpSelectorStrategy(SelectorStrategy):
    def __init__(self, selector: dict[str, str]) -> None:
        self.__pattern: dict[str, Pattern[str]] = {key: re.compile(value) for key, value in selector.items()}


    def select_rows(self, context: dict, original_table: Table) -> Iterator[Row]:
        for original_row in original_table.rows:
            regexp_groups: dict[str, list[str]] = {}

            found = True
            for key, pattern in self.__pattern.items():
                if key not in original_row.body.keys():
                    found = False
                    break

                match: Match[str] = pattern.match(original_row.body[key])
                if not match:
                    found = False
                    break

                # Match.lastindex は結果がグループにマッチしなかった場合はNoneだが、Match.group(0)は有効。
                lastindex = match.lastindex if match.lastindex is not None else 0
                regexp_groups[key] = [match[index] for index in range(lastindex + 1)]

            if found:
                try:
                    context['regexp_groups'] = regexp_groups
                    yield original_row
                finally:
                    if 'regexp_groups' in context.keys():
                        del context['regexp_groups']


    def __merge_values(self, context: dict, edited_record: Record, new_values: dict[str, str]) -> None:
        result: dict[str, str] = {}

        if new_values:
            for key, new_value_template in new_values.items():
                edited_record[key] = eval(f"f'{new_value_template}'", {}, {'regexp_groups': context['regexp_groups']})

        return result


    def create_edited_row(self, context: dict, indexer: Indexer, edit_data_entry: dict, selected_row: Row) -> Row:
        edited_row = selected_row.clone_for_edit(edit_data_entry.get('operation'))

        self.__merge_values(context, edited_row.body, edit_data_entry.get('body'))
        self.__merge_values(context, edited_row.upload_file, edit_data_entry.get('upload_file'))

        return edited_row

def regexp_selector(selector: dict[str, str]):
    return RegexpSelectorStrategy(selector)


class ApiExastro:
    def __init__(self, config: dict = {}) -> None:
        self.__api_context = ApiContext(config)


    @property
    def api_context(self):
        return self.__api_context


    def __get_strategy(self, edit_data_entry: dict, operation: str) -> Strategy:
        # edit data entryから'strategy'の値を取得
        value = edit_data_entry.get('strategy')

        # ストラテジを作成
        if value is None:
            strategy = single_constant_register()
        elif isinstance(value, Mapping):
            strategy = exact_match_selector(value)
        elif isinstance(value, Strategy):
            strategy = value
        else:
            raise ApiException(f'The value of "strategy" must be instance of dict or Strategy. type = {type(value)}')
        
        # ストラテジとオペレーションの組み合わせの妥当性を検査
        strategy.check_operation_acceptable(operation)

        return strategy


    def edit(self, menu_id: str, edit_data_entries: Union[dict[str, str], list[dict[str, str]]], filter: dict = {'1': {'NORMAL': '0'}}) -> None:
        # 引数の型の調整
        if not isinstance(edit_data_entries, Sequence):
            edit_data_entries = [edit_data_entries]

        # APIリクエストの生成
        api_request = self.api_context.create_api_request(menu_id)

        # データの取得
        json_object = None
        if filter is not None:
            with api_request.send_post(XCommand.FILTER_DATAONLY, filter) as api_response:
                json_object = api_response.body_as_json_object

        # オリジナルのテーブルの作成
        original_table: Table = Table(api_request.indexer, json_object)

        # 更新用のテーブルを作成
        edited_table: Table = Table(api_request.indexer)

        # edit data entry毎に処理
        for edit_data_entry in edit_data_entries:
            # 実行処理種別を取得
            operation = edit_data_entry.get('operation')

            # ストラテジを取得
            strategy: Strategy = self.__get_strategy(edit_data_entry, operation)

            # コンテキストを作成
            context: dict = {}

            # 選択された行毎に加工処理を実施
            for selected_row in strategy.select_rows(context, original_table):
                # 更新用のRowを作成
                row: Row = strategy.create_edited_row(
                    context = context,
                    indexer = api_request.indexer,
                    edit_data_entry = edit_data_entry,
                    selected_row = selected_row
                )

                # 更新用のRowを更新用のTableにマージ
                edited_table.merge_row(row)

        # API呼び出しにより、Exastro IT Automationにパラメータを登録
        with api_request.send_post(XCommand.EDIT, edited_table.generate_edit_parameters()) as api_response:
            json_object = api_response.body_as_json_object
            print(json.dumps(json_object, ensure_ascii=False, indent=4))
