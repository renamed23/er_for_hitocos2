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


# bind_asset_virtualizer, bind_font_manager, bind_lifecycle_guard
# bind_path_redirector, bind_text_mapping, bind_user_interface_patcher
# bind_window_title_overrider, disable_forced_font, enable_debug_output
# assume_text_out_arg_c_is_byte_len, enable_window_title_override
# enable_text_mapping_debug, enable_x64dbg_1337_patch
# auto_apply_1337_patch_on_attach, auto_apply_1337_patch_on_hwbp_hit
# enable_attach_cleanup, enable_overlay_gl, enable_overlay
# enable_gl_painter, enable_win_event_hook, enable_worker_thread
# enable_hwbp_from_constants, enable_veh, enable_resource_pack
# embed_resource_pack, enable_iat_hook, enable_text_patch
# extract_text, enable_patch, extract_patch, enable_custom_font
# export_default_dll_main, enable_locale_emulator, enable_delayed_attach
# enable_dll_hijacking, export_hook_symbols, default_impl
FEATURES = [
    "hitocos2",
    "bind_text_mapping",
    "bind_font_manager",
    "enable_iat_hook",
    "enable_text_patch",
    "bind_window_title_overrider",
    "enable_window_title_override",
    "enable_locale_emulator",
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
