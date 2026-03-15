from pathlib import Path
from typing import Any

from er.core.gal_json import GalJson
from er.utils.binary import de
from er.utils.console import console
from er.utils.fs import PathLike, collect_files, to_path
from er.utils.misc import read_json


def _extract_from_script(
    script_path: Path,
    gal_json: GalJson,
) -> None:
    """
    从单个脚本中提取可翻译条目。

    Args:
        script_path: 输入脚本路径。
        gal_json: 原文容器。

    Returns:
        None
    """
    items: list[Any] = read_json(script_path)["items"]

    last_name: str | None = None

    for item in items:
        arg = de(item["unknown_arg"])
        s: str = item["buf"]["str"]

        match arg:
            case 2:
                assert last_name is None
                last_name = s

            case 0:
                if last_name is None:
                    item = {"message": s}
                else:
                    item = {"name": last_name, "message": s}
                    last_name = None
                gal_json.add_item(item)  # type: ignore

            case 3:
                assert last_name is None
                gal_json.add_item({"message": s, "is_select": True})
            case _:
                raise ValueError(f"未知的arg：{arg}")

    assert last_name is None


def extract(input_dir: PathLike, gal_json: GalJson) -> None:
    """
    提取目录下脚本文本到容器中。

    Args:
        input_dir: 反汇编后的脚本目录（json）。
        gal_json: 原文容器。

    Returns:
        None
    """
    source_root = to_path(input_dir)
    files = collect_files(source_root, "json")

    for file in files:
        _extract_from_script(file, gal_json)

    console.print(
        f"[OK] 文本提取完成: {source_root} ({len(files)} files, {gal_json.total_count()} items)",
        style="info",
    )
