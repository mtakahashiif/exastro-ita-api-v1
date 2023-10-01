import pathlib
import base64

from .common import *


class EditRecordBase:
    def __init__(self, indexer: dict[str, int]):
        self._indexer = indexer
        self._values: dict[int, str] = {}


    def __setitem__(self, key: str, value: str) -> None:
        self.set(key, value)


    def __len__(self) -> int:
        return self._values.__len__()


    def get(self, key: str) -> str:
        return self._values[self._indexer[key]]


    def set(self, key: str, new_value: str) -> None:
        index = self._indexer[key]
        if index == CommonIndex.ID:
            raise ApiException(f'Can not modify record ID "{self._values[CommonIndex.ID]}" to "{new_value}".')

        self._values[self._indexer[key]] = new_value


    def _convert_value(self, value: str) -> str:
        return value


    def generate(self) -> dict:
        return {
            str(index): self._convert_value(self._values[index]) for index in sorted(self._values.keys())
        }


class EditRecord(EditRecordBase):
    def __init__(self, indexer: dict[str, int], operation: str, original_values: list[str] = None) -> None:
        super().__init__(indexer)

        self._values[self._indexer['実行処理種別']] = operation
        
        if original_values is not None:
            self._values[CommonIndex.ID] = original_values[CommonIndex.ID]     # ID (メニューによって名前が違うがインデックスは同じ)
            self._values[self._indexer['更新用の最終更新日時']] = original_values[self._indexer['更新用の最終更新日時']]

        self.file_record: EditFileRecord = EditFileRecord(self._indexer)


    @property
    def id(self) -> str:
        return self._values.get(CommonIndex.ID)


class EditFileRecord(EditRecordBase):
    def __init__(self, indexer: dict[str, int]):
        super().__init__(indexer)

    def _convert_value(self, file_path: str):
        path = pathlib.Path(file_path)
        contents = path.read_bytes()
        text = base64.b64encode(contents).decode()

        return text


class EditParameterBuilder:
    def __init__(self, indexer: dict[str, int]) -> None:
        self.__indexer = indexer
        self.__records: list[EditRecord] = []


    def create_edit_record(self, operation: str, original_values: list[str] = None):
        return EditRecord(self.__indexer, operation, original_values)


    def add(self, record: EditRecord):
        self.__records.append(record)


    def generate(self):
        result = {
            str(index): record.generate() for index, record in enumerate(self.__records)
        }

        upload_file = {
            str(index): record.file_record.generate() for index, record in enumerate(self.__records) if record.file_record
        }

        if upload_file:
            result['UPLOAD_FILE'] = upload_file

        return result
