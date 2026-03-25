import os

from er.core import text_hook
from er.core import config
from er.core.config import FEATURES
from er.core.gal_json import GalJson
from er.core.pipeline import tblstr_scrpiler, textract
from er.processor.mapping import ReplacementPoolBuilder
from er.utils import fs
from er.utils.compatibility import load_uif_json_substitution
from er.utils.console import console


def extract() -> None:
    """提取(extract)相关逻辑"""
    console.print("执行提取...", style="info")

    tblstr_scrpiler.decompile("workspace/TBLSTR.ARC", "workspace/raw/tblstr.json")

    gal_json = GalJson()
    textract.extract("workspace/raw", gal_json)
    gal_json.save_to_path("workspace/raw_text.json")

    (
        gal_json.apply_remove_fullwidth_spaces()
        .apply_transform(lambda s: s.replace("\n", ""))
        .apply_current_to_raw_fields()
        .apply_add_tags()
        .save_to_path("workspace/raw.json")
    )

    console.print("提取完成", style="info")


def replace(check: bool = True) -> None:
    """替换(replace)相关逻辑"""
    console.print("执行替换...", style="info")

    gal_json = GalJson.load_from_path("workspace/translated.json")
    gal_json.apply_remove_tags()

    if check:
        (
            gal_json.check_korean_characters()
            .check_japanese_characters()
            .check_duplicate_quotes()
            .check_length_discrepancy()
            .check_quote_consistency()
            .check_invisible_characters()
            .check_forbidden_words()
            .check_unpaired_quotes()
            .check_max_text_len(106)
            .ok_or_print_error_and_exit()
        )

    (
        gal_json.apply_restore_whitespace()
        .apply_replace_rare_characters()
        .apply_replace_nested_brackets()
        .apply_replace_quotation_marks()
        .apply_fullwidth()
    )

    pool = ReplacementPoolBuilder().exclude_from_gal_text(gal_json).build()
    gal_json.apply_mapping(pool)
    pool.save_mapping_to_path("workspace/generated/mapping.json")

    fs.copy_entry("assets/raw_text", "workspace/generated/raw_text", overwrite=True)
    fs.copy_entry(
        "assets/translated_text",
        "workspace/generated/translated_text",
        overwrite=True,
    )
    fs.copy_entry(
        "workspace/raw_text.json",
        "workspace/generated/raw_text/text.json",
        overwrite=True,
    )
    gal_json.save_to_path("workspace/generated/translated_text/text.json")

    fs.merge_dir("assets/dist_extra", "workspace/generated/dist", overwrite=True)
    config.generate_config_files()

    text_hook.TextHookBuilder(os.environ["TEXT_HOOK_PROJECT_PATH"]).build(
        FEATURES, panic="immediate-abort"
    )


def fix_translated() -> None:
    """修复翻译JSON(fix_translated)的逻辑"""
    substitution = load_uif_json_substitution("workspace/uif_config.json")
    translation_table = str.maketrans(substitution)

    gal_json = GalJson.load_from_path("workspace/translated.json")
    (
        gal_json.apply_transform(
            lambda value: value.translate(translation_table),
            item_fields=("name", "message"),
            include_names=True,
        ).save_to_path("workspace/translated.json")
    )
