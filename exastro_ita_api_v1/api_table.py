import collections.abc
import pathlib
import uuid

from typing import *

from .api import *
from .common import *


RecordValues: TypeAlias = Union[dict[Union[int, str], str], list[str]]


class Record(collections.abc.MutableMapping[str, str], IndexerMixin):
    def __init__(self, indexer: Indexer, values: RecordValues = None, is_named: bool = False) -> None:
        self.__indexer: Indexer = indexer

        if values is None:
            it = {}.items()
        elif isinstance(values, dict):
            it = values.items()
        elif isinstance(values, list):
            it = enumerate(values)
        else:
            raise ApiException(f'Unknown type {type(values)}. Valid types are dict and list.')

        self.__values: dict[int, str] = {indexer.sanitize(index, is_named): value for index, value in it}


    def __getitem__(self, key: str) -> str:
        return self.__values.__getitem__(self.indexer[key])


    def __setitem__(self, key: str, value: str) -> None:
        self.__values.__setitem__(self.indexer[key], value)


    def __delitem__(self, key: str) -> None:
        return self.__values.__delitem__(self.indexer[key])


    def __iter__(self) -> Iterator[str]:
        for index in self.__values.keys():
            yield self.indexer.to_column_name(index)


    def __len__(self) -> int:
        return self.__values.__len__()


    @property
    def indexer(self) -> Indexer:
        return self.__indexer


    @property
    def values(self) -> dict[int, str]:
        return self.__values


    def _convert_value(self, value: str) -> str:
        return value


    def merge(self, other: 'Record') -> None:
        self.check_acceptable(other)

        self.values |= other.values


    def generate_edit_parameters(self) -> dict:
        return {
            str(index): self._convert_value(self.__values[index]) for index in sorted(self.__values.keys())
        }


class Body(Record):
    def __init__(self, indexer: Indexer, values: RecordValues = None, operation: str = None, is_named: bool = False) -> None:
        super().__init__(indexer, values, is_named)

        if operation is not None:
            self['実行処理種別'] = operation


    @property
    def id(self) -> str:
        return self.values.get(CommonIndex.ID)


    def clone_for_edit(self, operation: str):
        values: dict[int, str] = {
            CommonIndex.ID: self.values[CommonIndex.ID],
            self.indexer['更新用の最終更新日時']: self.values[self.indexer['更新用の最終更新日時']]
        }

        result = Body(self.indexer, values, operation)

        return result


class UploadFile(Record):
    def __init__(self, indexer: Indexer, values: RecordValues = None, is_named: bool = False) -> None:
        super().__init__(indexer, values, is_named)


    def _convert_value(self, value: str):
        result = value

        if value:
            result = base64.b64encode(pathlib.Path(value).read_bytes()).decode()

        return result
    

    def clone_for_edit(self, operation: str):
        return UploadFile(self.indexer)


class Row(IndexerMixin):
    def __init__(self, indexer: Indexer, body_values: RecordValues = None, upload_file_values: RecordValues = None, operation: str = None, is_named: bool = False) -> None:
        self.__indexer: Indexer = indexer

        self.__body = Body(
            indexer = indexer,
            values = body_values,
            operation = operation,
            is_named = is_named
        )
        
        self.__upload_file = UploadFile(
            indexer = indexer,
            values = upload_file_values,
            is_named = is_named
        )


    @property
    def indexer(self) -> Indexer:
        return self.__indexer


    @property
    def body(self) -> Body:
        return self.__body


    @property
    def upload_file(self) -> UploadFile:
        return self.__upload_file


    @property
    def id(self) -> str:
        return self.body.id


    def merge(self, row: 'Row'):
        self.check_acceptable(row)

        self.body.merge(row.body)
        self.upload_file.merge(row.upload_file)


    def clone_for_edit(self, operation: str):
        result = Row(self.indexer)

        result.__body = self.body.clone_for_edit(operation)
        result.__upload_file = self.upload_file.clone_for_edit(operation)

        return result



class Table(IndexerMixin):
    def __init__(self, indexer: Indexer, json_object: dict = None) -> None:
        self.__indexer: Indexer = indexer
        self.__rows: dict[str, Row] = {}

        if json_object is not None:
            contents = json_object['resultdata']['CONTENTS']
            for index, body_values in enumerate(contents['BODY']):
                row = Row(
                    indexer = indexer,
                    body_values = body_values,
                    upload_file_values = contents['UPLOAD_FILE'].get(str(index + 1))
                )
                print(contents['UPLOAD_FILE'].get(str(index + 1)))

                self.__rows[row.id] = row


    @property
    def indexer(self) -> Indexer:
        return self.__indexer


    @property
    def rows(self) -> Collection[Row]:
        return self.__rows.values()


    def create_row(self, body_values: RecordValues = None, upload_file_values: RecordValues = None, operation: str = None, is_named: bool =False) -> Row:
        return Row(self.indexer, body_values, upload_file_values, operation, is_named)


    def add_row(self, row: Row) -> Row:
        self.check_acceptable(row)
        
        if row.id:
            if row.id in self.__rows.keys():
                raise ApiException(f'Row ID "{row.id}" already exists in table.')
            
            id = row.id
        else:
            id = str(uuid.uuid4())
        
        self.__rows[id] = row


    def merge_row(self, row: Row) -> Row:
        base_row = self.__rows.get(row.id)
        if base_row:
            base_row.merge(row)
        else:
            self.add_row(row)


    def generate_edit_parameters(self) -> dict:
        result = {
            str(index): row.body.generate_edit_parameters() for index, row in enumerate(self.__rows.values())
        }

        upload_file = {}
        for index, row in enumerate(self.__rows.values()):
            parameters = row.upload_file.generate_edit_parameters()
            if parameters:
                upload_file[str(index)] = parameters

        if upload_file:
            result['UPLOAD_FILE'] = upload_file

        return result
