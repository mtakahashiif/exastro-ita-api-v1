import collections.abc
import json

body = [
    [
        "実行処理種別",
        "廃止",
        "項番",
        "オペレーション",
        "Movement",
        "ホスト",
        "アクセス許可ロール",
        "備考",
        "最終更新日時",
        "更新用の最終更新日時",
        "最終更新者"
    ],
    [
        [
            "登録",
            "更新",
            "廃止",
            "復活"
        ],
        [],
        [],
        [],
        {
            "1": "1:a"
        },
        {
            "1": "1:test1",
            "2": "2:test2",
            "5": "5:aaa",
            "6": "6:bbb"
        },
        [],
        [],
        [],
        [],
        []
    ]
]


options_table: dict[str, dict[str, str]] = {}
column_names: list[str] = body[0]
for column_index, options in enumerate(body[1]):
    if isinstance(options, collections.abc.Sequence):
        options = {str(index): option for index, option in enumerate(options)}
    elif isinstance(options, collections.abc.Mapping):
        options = dict(options)
    else:
        print('error')
    
    if not options:
        options = None

    options_table[column_names[column_index]] = options
    
print(json.dumps(options_table, ensure_ascii=False, indent=4))
