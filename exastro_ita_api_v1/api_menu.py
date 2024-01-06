import collections.abc
import pathlib
import uuid

from typing import Sequence

from .api import *
from .constants import *


class Record(collections.abc.MutableMapping[str, str], IndexerMixin):
    def __init__(self, indexer: Indexer, values: dict[str, str]) -> None:
        self.__indexer = indexer
        self.__values = values


    def __getitem__(self, key: str) -> str:
        return self.__values.__getitem__(self.indexer[key])


    def __setitem__(self, key: str, value: str) -> None:
        self.__values.__setitem__(self.indexer[key], value)


    def __delitem__(self, key: str) -> None:
        self.__values.__delitem__(self.indexer[key])


    def __iter__(self) -> Iterator[str]:
        for index in self.__values.keys():
            yield self.indexer.to_column_name(index)


    def __len__(self) -> int:
        return self.__values.__len__()


    @property
    def indexer(self) -> Indexer:
        return self.__indexer


    @property
    def values(self) -> dict[str, str]:
        return self.__values


    def clone_values(self, kept_indexes: list[str] | None = None) -> dict[str, str]:
        if kept_indexes is None:
            return dict(self.__values)
        else:
            return {index: self.__values[index] for index in kept_indexes} if kept_indexes else {}


    def at(self, index: int | str) -> str | None:
        i = int(index)

        # out of range
        if i < 0 and len(self.indexer) <= i:
            raise ApiException(f'Passed index is out of range. max index: {len(self.indexer) - 1}, passed index: {i}')

        return self.__values.get(str(i))


    def merge(self, other: 'Record') -> None:
        self.check_acceptable(other)

        self.__values |= other.values


    def to_editable(self, kept_indexes: list[str] = []):
        kept_values = {index: self.values[index] for index in kept_indexes} if kept_indexes else {}
        self.values.clear()
        self.values.update(kept_values)


    def to_edit_parameters(self) -> dict:
        def convert_value(value: str) -> str:
            result = value
    
            if isinstance(value, pathlib.Path):
                result = base64.b64encode(value.read_bytes()).decode()
    
            return result
    
        return {
            str(index): convert_value(self.values[index]) for index in sorted(self.values.keys())
        }


class Row(IndexerMixin):
    def __init__(self,
        indexer: Indexer,
        body_values: StrBlurDict = None,
        file_values: StrBlurDict = None,
        operation: str | None = None
    ) -> None:
        self.__indexer: Indexer = indexer

        self.__body = Record(
            indexer=indexer,
            values=to_dict(body_values) | ({CommonIndex.実行処理種別: operation} if operation else {})
        )

        self.__file = Record(
            indexer=indexer,
            values=to_dict(file_values)
        )


    @property
    def indexer(self) -> Indexer:
        return self.__indexer


    @property
    def body(self) -> Record:
        return self.__body


    @property
    def file(self) -> Record:
        return self.__file


    @property
    def id(self) -> str:
        return self.body.values[CommonIndex.ID]


    def merge(self, row: 'Row'):
        self.check_acceptable(row)

        self.body.merge(row.body)
        self.file.merge(row.file)


    def to_editable(self, operation: str | None = None) -> None:
        self.body.to_editable([
            CommonIndex.ID,
            self.indexer['更新用の最終更新日時']
        ])

        if operation:
            self.body.values[CommonIndex.実行処理種別] = operation

        self.__file.to_editable()
    

    def clone_for_edit(self, operation: str):
        return Row(
            self.indexer,
            body_values=self.body.clone_values([CommonIndex.ID, self.indexer['更新用の最終更新日時']]),
            file_values=self.file.clone_values(),
            operation=operation
        )


# FILTERのみ受け入れ可能。FILTER_DATAONLYは受入不可
class Menu(IndexerMixin):
    def __init__(self, indexer: Indexer, json_object: dict | None = None) -> None:
        self.__indexer: Indexer = indexer
        self.__rows: dict[str, Row] = {}

        if json_object is not None:
            body_entries = to_dict(json_object['resultdata']['CONTENTS']['BODY'])
            file_entries = to_dict(json_object['resultdata']['CONTENTS']['UPLOAD_FILE'])

            for index in body_entries.keys():
                if int(index) == 0:
                    continue

                row = Row(
                    indexer=indexer,
                    body_values=body_entries.get(index),
                    file_values=file_entries.get(index)
                )

                self.__rows[row.id] = row


    @property
    def indexer(self) -> Indexer:
        return self.__indexer


    @property
    def rows(self) -> Sequence[Row]:
        return list(self.__rows.values())


    def create_row(
        self,
        body_values: StrBlurDict = None,
        file_values: StrBlurDict = None,
        operation: str | None = None
    ) -> Row:
        return Row(
            indexer=self.indexer,
            body_values=body_values,
            file_values=file_values,
            operation=operation
        )


    def add_row(self, row: Row) -> None:
        self.check_acceptable(row)
        
        try:
            id = row.id
            if id in self.__rows.keys():
                raise ApiException(f'Row ID "{id}" already exists in table.')
        except KeyError:
            id = str(uuid.uuid4())

        self.__rows[id] = row


    def merge_row(self, row: Row) -> None:
        base_row = self.__rows.get(row.id)
        if base_row:
            base_row.merge(row)
        else:
            self.add_row(row)


    def to_edit_parameters(self) -> dict:
        result = {
            str(index): row.body.to_edit_parameters() for index, row in enumerate(self.__rows.values())
        }

        upload_file = {}
        for index, row in enumerate(self.__rows.values()):
            parameters = row.file.to_edit_parameters()
            if parameters:
                upload_file[str(index)] = parameters

        if upload_file:
            result['UPLOAD_FILE'] = upload_file

        return result
