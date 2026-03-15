from dataclasses import dataclass
from pathlib import Path, PureWindowsPath
import struct

from er.utils.console import console
from er.utils.fs import PathLike, collect_files, to_path


@dataclass(slots=True)
class AriEntry:
    """SCR.ARI 的单条索引记录。"""

    name: str
    name_len: int
    name_raw: bytes
    flags: int
    size: int


ARC_MAGIC = b"WFL1"


def _resolve_pair_paths(input_path: PathLike) -> tuple[Path, Path]:
    """根据任一输入路径推导 SCR.ARI / SCR.ARC 路径。"""
    source = to_path(input_path)
    suffix = source.suffix.lower()

    if suffix == ".ari":
        ari_path = source
        arc_path = source.with_suffix(".ARC")
    elif suffix == ".arc":
        arc_path = source
        ari_path = source.with_suffix(".ARI")
    else:
        raise ValueError(f"不支持的输入扩展名: {source}")

    if not ari_path.is_file():
        raise FileNotFoundError(f"找不到索引文件: {ari_path}")
    if not arc_path.is_file():
        raise FileNotFoundError(f"找不到封包文件: {arc_path}")
    return ari_path, arc_path


def _decode_obfuscated_name(raw_name: bytes) -> str:
    """解码 ARI 中按位取反的 cp932 文件名。"""
    plain = invert_bytes(raw_name)
    try:
        return plain.decode("cp932")
    except UnicodeDecodeError as exc:
        raise ValueError(f"无法按 cp932 解码文件名: {raw_name.hex()}") from exc


def invert_bytes(b: bytes) -> bytes:
    """将字节按位取反"""
    return bytes((~byte_value) & 0xFF for byte_value in b)


def _encode_obfuscated_name(name: str) -> bytes:
    """将文件名按 cp932 编码并做按位取反混淆。"""
    try:
        encoded = name.encode("cp932")
    except UnicodeEncodeError as exc:
        raise ValueError(f"文件名无法按 cp932 编码: {name}") from exc
    return invert_bytes(encoded)


def _parse_ari_entries(ari_blob: bytes) -> list[AriEntry]:
    """解析 SCR.ARI 记录。"""
    entries: list[AriEntry] = []
    cursor = 0

    while cursor < len(ari_blob):
        if cursor + 4 > len(ari_blob):
            raise ValueError(f"ARI 结构损坏：记录头不足 4 字节 (cursor={cursor})")

        name_len = struct.unpack_from("<I", ari_blob, cursor)[0]
        cursor += 4

        if cursor + name_len + 6 > len(ari_blob):
            raise ValueError(
                "ARI 结构损坏：记录长度超界 "
                f"(cursor={cursor}, name_len={name_len}, total={len(ari_blob)})"
            )

        name_raw = ari_blob[cursor : cursor + name_len]
        cursor += name_len

        flags = struct.unpack_from("<H", ari_blob, cursor)[0]
        cursor += 2

        size = struct.unpack_from("<I", ari_blob, cursor)[0]
        cursor += 4

        entries.append(
            AriEntry(
                name=_decode_obfuscated_name(name_raw),
                name_len=name_len,
                name_raw=name_raw,
                flags=flags,
                size=size,
            )
        )

    return entries


def _build_output_path(out_dir: Path, entry_name: str) -> Path:
    """根据封包内文件名计算输出路径。"""
    win_path = PureWindowsPath(entry_name)
    safe_parts = [part for part in win_path.parts if part not in {"", "."}]
    if any(part == ".." for part in safe_parts):
        raise ValueError(f"检测到非法相对路径: {entry_name}")
    return out_dir.joinpath(*safe_parts)


def _normalize_archive_name(file_path: Path, root: Path) -> str:
    """将实际文件路径转换为封包内文件名（Windows 分隔符）。"""
    rel = file_path.relative_to(root)
    if not rel.parts:
        raise ValueError(f"无法计算相对路径: {file_path}")
    return "\\".join(rel.parts)


def _resolve_output_pair(out_path: PathLike) -> tuple[Path, Path]:
    """根据输出路径推导 SCR.ARI / SCR.ARC 的写入路径。"""
    base = to_path(out_path)
    suffix = base.suffix.lower()
    if suffix == ".ari":
        return base, base.with_suffix(".ARC")
    if suffix == ".arc":
        return base.with_suffix(".ARI"), base
    raise ValueError(f"输出路径扩展名必须是 .ARI 或 .ARC: {base}")


def unpack(input_path: PathLike, out_dir: PathLike) -> None:
    """
    解包。

    Args:
        input_path: 输入包路径。
        out_dir: 解包输出目录。

    Returns:
        None
    """
    source = to_path(input_path)
    output_dir = to_path(out_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    ari_path, arc_path = _resolve_pair_paths(source)
    ari_blob = ari_path.read_bytes()
    arc_blob = arc_path.read_bytes()

    if len(arc_blob) < 4:
        raise ValueError(f"ARC 文件过短: {arc_path}")
    if arc_blob[:4] != ARC_MAGIC:
        raise ValueError(f"ARC 魔数异常: {arc_path} (magic={arc_blob[:4]!r})")

    entries = _parse_ari_entries(ari_blob)

    cursor = 4
    for index, entry in enumerate(entries):
        header_size = 4 + entry.name_len + 2 + 4
        if cursor + header_size > len(arc_blob):
            raise ValueError(
                "ARC 结构损坏：条目头超界 "
                f"(index={index}, cursor={cursor}, need={header_size}, total={len(arc_blob)})"
            )

        arc_name_len = struct.unpack_from("<I", arc_blob, cursor)[0]
        if arc_name_len != entry.name_len:
            raise ValueError(
                "ARI/ARC 不一致：name_len 不匹配 "
                f"(index={index}, ari={entry.name_len}, arc={arc_name_len})"
            )
        cursor += 4

        arc_name_raw = arc_blob[cursor : cursor + arc_name_len]
        if arc_name_raw != entry.name_raw:
            raise ValueError(
                f"ARI/ARC 不一致：name_raw 不匹配 (index={index}, name={entry.name})"
            )
        cursor += arc_name_len

        arc_flags = struct.unpack_from("<H", arc_blob, cursor)[0]
        if arc_flags != entry.flags:
            raise ValueError(
                f"ARI/ARC 不一致：flags 不匹配 (index={index}, ari={entry.flags}, arc={arc_flags})"
            )
        cursor += 2

        arc_size = struct.unpack_from("<I", arc_blob, cursor)[0]
        if arc_size != entry.size:
            raise ValueError(
                f"ARI/ARC 不一致：size 不匹配 (index={index}, ari={entry.size}, arc={arc_size})"
            )
        cursor += 4

        if entry.flags & 0x1:
            raise ValueError(
                "检测到压缩条目，但当前流程明确不支持压缩："
                f"index={index}, name={entry.name}, flags={entry.flags}"
            )

        if cursor + entry.size > len(arc_blob):
            raise ValueError(
                "ARC 结构损坏：数据段超界 "
                f"(index={index}, cursor={cursor}, size={entry.size}, total={len(arc_blob)})"
            )

        data = arc_blob[cursor : cursor + entry.size]
        cursor += entry.size

        out_file = _build_output_path(output_dir, entry.name)
        out_file.parent.mkdir(parents=True, exist_ok=True)
        out_file.write_bytes(data)

    if cursor != len(arc_blob):
        raise ValueError(
            "ARC 末尾存在未消费数据："
            f"remain={len(arc_blob) - cursor}, total={len(arc_blob)}"
        )

    console.print(
        f"[OK] unpack 完成: {source} -> {output_dir} (entries={len(entries)})",
        style="info",
    )


def pack(input_dir: PathLike, out_path: PathLike) -> None:
    """
    将目录内容重新打包。

    Args:
        input_dir: 输入目录路径。
        out_path: 输出包路径。

    Returns:
        None

    Raises:
        ValueError: 输入非法、命名冲突或字段超限。
    """
    input_root = to_path(input_dir)
    if not input_root.is_dir():
        raise ValueError(f"输入目录不存在: {input_root}")

    ari_path, arc_path = _resolve_output_pair(out_path)
    files = collect_files(input_root)
    if not files:
        raise ValueError(f"输入目录没有可打包文件: {input_root}")

    ari_chunks: list[bytes] = []
    arc_chunks: list[bytes] = [ARC_MAGIC]

    for file_path in files:
        name = _normalize_archive_name(file_path, input_root)
        name_raw = _encode_obfuscated_name(name)
        name_len = len(name_raw)
        flags = 0
        data = file_path.read_bytes()
        size = len(data)

        header = (
            struct.pack("<I", name_len)
            + name_raw
            + struct.pack("<H", flags)
            + struct.pack("<I", size)
        )
        ari_chunks.append(header)
        arc_chunks.append(header)
        arc_chunks.append(data)

    ari_path.parent.mkdir(parents=True, exist_ok=True)
    arc_path.parent.mkdir(parents=True, exist_ok=True)
    ari_path.write_bytes(b"".join(ari_chunks))
    arc_path.write_bytes(b"".join(arc_chunks))

    console.print(
        f"[OK] pack 完成: {input_root} -> {ari_path}, {arc_path} (entries={len(files)})",
        style="info",
    )
