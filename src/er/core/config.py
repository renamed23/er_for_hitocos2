from er.utils import misc


CONFIG = {
    # "REDIRECTION_SRC_PATH": "B.FL4",
    # "REDIRECTION_TARGET_PATH": "FLOWERS_CHS.FL4",
    "FONT_FACE": "SimHei",  # (ＭＳ ゴシック, SimHei, SimSun)
    "CHAR_SET": 134,  # CP932=128, GBK=134
    # "FONT_FILTER": [
    #     "ＭＳ ゴシック",
    #     "俵俽 僑僔僢僋",
    #     "MS Gothic",
    #     "",
    #     "俵俽僑僔僢僋",
    #     "ＭＳゴシック",
    # ],
    "FONT_FILTER": ["Microsoft YaHei", "Microsoft YaHei UI"],
    "WINDOW_TITLE": "人妻cosplay咖啡馆2",
    # "CHAR_FILTER": [
    #     0x40
    # ],
    # "ENUM_FONT_PROC_CHAR_SET": 128,
    # "ENUM_FONT_PROC_PITCH": 1,
    # "ENUM_FONT_PROC_OUT_PRECISION": 3,
    "ARG_GAME_TYPE": {
        "value": "hitocos2",
        "type": "&str",
    },
    # "HIJACKED_DLL_PATH": "some_path/your_dll.dll",
    # "RESOURCE_PACK_NAME": "MOZU_chs",
    # "HWBP_REG": "crate::utils::hwbp::HwReg::Dr2",
    # "HWBP_TYPE": "crate::utils::hwbp::HwBreakpointType::Execute",
    # "HWBP_LEN": "crate::utils::hwbp::HwBreakpointLen::Byte1",
    # "HWBP_MODULE": "::core::ptr::null()",
    # "HWBP_RVA": 0x1F4D541,
    # "EMULATE_LOCALE_CODEPAGE": 932,
    # "EMULATE_LOCALE_LOCALE": 1041,
    # "EMULATE_LOCALE_CHARSET": 128,
    # "EMULATE_LOCALE_TIMEZONE": "Tokyo Standard Time",
    # "EMULATE_LOCALE_WAIT_FOR_EXIT": False,
    # "OVERLAY_TARGET_WINDOW_TEXT": "some_window_text",
    # "OVERLAY_TARGET_WINDOW_CLASS_NAME": "some_window_class_name"
}

HOOK_LISTS = {
    "enable": [],
    "disable": [
        "PropertySheetA",
        "ModifyMenuA",
        "MessageBoxA",
        "SetDlgItemTextA",
        "SetWindowTextA",
        "SendMessageA",
    ],
}


# patch,custom_font,debug_output,debug_text_mapping
# default_impl,enum_font_families
# export_default_dll_main,read_file_patch_impl
# debug_file_impl,locale_emulator,override_window_title
# dll_hijacking,export_patch_process_fn,text_patch,text_extracting
# x64dbg_1337_patch,apply_1337_patch_on_attach,create_file_redirect
# text_out_arg_c_is_bytes,iat_hook,resource_pack,resource_pack_embedding
# apply_1337_patch_on_hwbp_hit,hwbp_from_constants,veh
# attach_clean_up,worker_thread,win_event_hook,gl_painter,overlay,overlay_gl
FEATURES = [
    "hitocos2",
    "text_hook",
    "iat_hook",
    "text_patch",
    "override_window_title",
    "locale_emulator",
]

BITMAP_FONT = {
    "font_path": "assets/font/unifont-17.0.03.otf",
    "font_size": 16,
    "padding": 2,
    "texture_max_width": 2048,
    "chars": "",
}


def generate_config_files() -> None:
    """生成配置文件"""
    misc.write_json("workspace/generated/config.json", CONFIG)
    misc.write_json("workspace/generated/hook_lists.json", HOOK_LISTS)


def generate_bitmap_font_config(chars: str) -> None:
    """生成位图字体配置文件"""
    BITMAP_FONT["chars"] = chars
    misc.write_json("workspace/generated/bitmap_font.json", BITMAP_FONT)
