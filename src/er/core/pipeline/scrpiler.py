from er.utils.console import console
from er.utils.instructions import (
    Handler,
    HandlerResult,
    Instruction,
    ParseContext,
    assemble_one_inst,
    fix_offset,
    h,
    parse_data,
    u8,
    u16,
    u32,
)
from er.utils.binary import BinaryReader, CStringNotTerminatedError, String, de, se
from er.utils.fs import PathLike, collect_files, to_path
from er.utils.misc import read_json, write_json


def inverted_str_handler(reader: BinaryReader, ctx: ParseContext) -> HandlerResult:
    """
    读取取反的CP932字符串。
    字符串以NULL结尾，每个字节都经过~（取反）操作存储。
    """
    _ = ctx
    # 读取直到NULL字节
    start_offset = reader.tell()
    data = reader.data
    offset = start_offset

    # 查找NULL终止符
    while offset < len(data) and data[offset] != 0:
        offset += 1

    if offset >= len(data):
        raise CStringNotTerminatedError(
            f"未找到取反字符串结尾: offset={start_offset}, length={len(data)}"
        )

    # 读取取反的字节
    inverted_bytes = data[start_offset:offset]
    # 对每个字节取反还原原始字节
    original_bytes = bytes(~b & 0xFF for b in inverted_bytes)

    # 解码为CP932字符串
    text = original_bytes.decode("cp932")

    # 跳过NULL终止符
    reader.seek(offset + 1)
    return se(String(text))


def inverted_str_with_length_handler(
    reader: BinaryReader, ctx: ParseContext, length: int
) -> HandlerResult:
    """
    读取指定长度的取反CP932字符串。
    字符串没有NULL结尾，长度由参数指定。
    """
    _ = ctx
    # 读取指定长度的取反字节
    inverted_bytes = reader.read_bytes(length)
    # 对每个字节取反还原原始字节
    original_bytes = bytes(~b & 0xFF for b in inverted_bytes)
    # 解码为CP932字符串
    text = original_bytes.decode("cp932")
    return se(String(text))


def inverted_str_var_length_handler(
    reader: BinaryReader, ctx: ParseContext, length_index: int = -1
) -> HandlerResult:
    """
    从上下文中获取长度参数，读取指定长度的取反CP932字符串。

    Args:
        length_index: 从 ctx["args"] 中获取长度参数的索引（默认-1表示最后一个参数）
    """
    # 从上下文中获取长度参数
    args = ctx["args"]
    if not args:
        raise ValueError("inverted_str_var_length 上下文 args 为空")

    if length_index < 0:
        length_index = len(args) + length_index

    if length_index >= len(args):
        raise ValueError(f"长度参数索引 {length_index} 超出范围，args长度: {len(args)}")

    length_value = args[length_index]
    length = de(length_value)
    if not isinstance(length, int) or length <= 0:
        raise ValueError(f"非法的长度参数: {length_value}")

    # 读取指定长度的取反字节
    inverted_bytes = reader.read_bytes(length)
    # 对每个字节取反还原原始字节
    original_bytes = bytes(~b & 0xFF for b in inverted_bytes)
    # 解码为CP932字符串
    text = original_bytes.decode("cp932")
    return se(String(text))


inverted_str = Handler(inverted_str_handler)
inverted_str_with_length = Handler(inverted_str_with_length_handler)
inverted_str_var_length = Handler(inverted_str_var_length_handler)


FIX_INST_MAP = {
    # 需要修复偏移的指令索引
    # "02": [0],  # 跳转指令，第0个参数是偏移
}

INST_MAP = {
    # 基本变量操作
    h("00"): [u8, u16, u32],  # 设置变量 var[idx] = value
    h("01"): [u8, u16, u32],  # 变量加法 var[idx] += value
    h("02"): [u8, u32],  # 无条件跳转 (需要修复偏移)
    # 条件跳转 (参数结构不完全确定)
    # h("03"): [u8, u32, u32, u32],  # 等于跳转 if (a == b) goto offset
    # h("04"): [u8, u32, u32, u32],  # 不等于跳转 if (a != b) goto offset
    # h("05"): [u8, u32, u32, u32],  # 大于跳转 if (a > b) goto offset
    # h("06"): [u8, u32, u32, u32],  # 小于跳转 if (a < b) goto offset
    # h("07"): [u8, u32, u32, u32],  # 大于等于跳转 if (a >= b) goto offset
    # h("08"): [u8, u32, u32, u32],  # 小于等于跳转 if (a <= b) goto offset
    # 脚本控制
    h("09"): [],  # 等待/暂停
    # 文本显示 (字符串参数需要取反)
    h("0C"): [u8, inverted_str_var_length.args(0)],  # 加载脚本文件
    h("12"): [u8, inverted_str_var_length.args(0)],  # 显示消息
    # 音频播放
    h("0F"): [u8, inverted_str_var_length.args(0)],  # 播放 WAV 音效
    h("10"): [u8, inverted_str_var_length.args(0)],  # 播放 MIDI 音乐
    # 选项显示
    h("15"): [u8, u8, inverted_str_var_length.args(1)],  # 显示选项
    # 延时等待
    h("18"): [u8, u8, u8, u32],  # 延时，参数：延时值 (单位: 毫秒/100)
    # 游戏控制
    h("25"): [u8],  # 退出游戏
    # 变量操作
    h("2C"): [u8, u8, inverted_str_var_length.args(0)],  # 设置角色名
    h("2F"): [
        u8,
        u16,
        u16,
        u16,
        inverted_str_var_length.args(2),
    ],
}


def decompile(input_path: PathLike, output_path: PathLike) -> None:
    """反编译：将二进制文件转换为JSON"""
    input_root = to_path(input_path)
    output_root = to_path(output_path)
    files = collect_files(input_root)

    for file in files:
        reader = BinaryReader(file.read_bytes())

        result = {}

        if not reader.startswith(h("01 0C 0D 0A 0C 3B")):
            console.print(f"忽略非脚本文件：{file}", style="warn")

        result["header"] = se(reader.read_bytes(6))

        insts = parse_data(
            {
                "file_name": str(file),
                "offset": 0,
            },
            reader,
            INST_MAP,
        )

        assert reader.is_eof()

        # 保存为JSON
        rel_path = file.relative_to(input_root)
        out_file = output_root / f"{rel_path.as_posix()}.json"
        out_file.parent.mkdir(parents=True, exist_ok=True)

        write_json(out_file, insts)

    console.print(f"[OK] decompile 完成: {input_path} -> {output_path}", style="info")


def compile(input_path: PathLike, output_path: PathLike) -> None:
    """编译：将JSON转换回二进制文件"""
    input_root = to_path(input_path)
    output_root = to_path(output_path)
    files = collect_files(input_root, "json")

    for file in files:
        insts: list[Instruction] = read_json(file)

        # ========= 第一步：assemble instruction，计算新 offset =========
        old2new = {}  # old_offset -> new_offset
        cursor = 0

        for inst in insts:
            old_offset = inst["offset"]
            b = assemble_one_inst(inst)

            old2new[old_offset] = cursor
            cursor += len(b)

        # ========= 第二步：修复指令的偏移 =========
        insts = fix_offset(str(file), insts, old2new, FIX_INST_MAP)

        # ========= 第三步：assemble 修复过偏移的指令 =========
        new_blob = b"".join([assemble_one_inst(inst) for inst in insts])

        # 保存二进制文件
        rel_path = file.relative_to(input_root)
        out_file = output_root / rel_path.with_suffix("")
        out_file.parent.mkdir(parents=True, exist_ok=True)

        out_file.write_bytes(new_blob)

    console.print(f"[OK] compile 完成: {input_path} -> {output_path}", style="info")
