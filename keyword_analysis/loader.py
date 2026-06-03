import pandas as pd
import re


def load_excel(path: str) -> pd.DataFrame:
    """
    加载 Ozon 关键词分析 Excel 文件，自动清洗数值列。

    Ozon 导出的数据中，数值列通常包含空格（千位分隔）、
    逗号（小数分隔符）、百分号、卢布符号等，需要转为数值类型。

    参数:
        path: Excel 文件路径

    返回:
        清洗后的 DataFrame，数值列已转为 float/int
    """
    df = pd.read_excel(path)

    # 清洗列名：去掉换行符、首尾空格
    df.columns = [col.replace("\n", " ").strip() for col in df.columns]

    # 需要清洗为数值的列（根据 Ozon 导出格式自动检测）
    for col in df.columns:
        # 跳过已经是数值的列
        if pd.api.types.is_numeric_dtype(df[col]):
            continue

        # 尝试将该列转为数值
        sample = df[col].dropna()
        if len(sample) == 0:
            continue

        # 如果大部分是字符串类型，尝试清洗
        if sample.dtype == object:
            cleaned = sample.apply(_clean_numeric_value)
            # 如果超过一半能转成数值，就应用清洗到整列
            numeric_count = cleaned.dropna().count()
            if numeric_count > len(sample) * 0.3:
                df[col] = df[col].apply(_clean_numeric_value)

    return df


def _clean_numeric_value(value) -> float | None:
    """
    清洗单个 Ozon 数值值。
    处理格式：
    - "340 172" -> 340172.0
    - "17,67%" -> 17.67
    - "66 878 170 ₽" -> 66878170.0
    - "751 ₽" -> 751.0
    - "—" / "-" / "" -> None
    """
    if pd.isna(value):
        return None

    s = str(value).strip()

    # 处理占位符
    if s in ("—", "-", "", "--", "N/A", "n/a"):
        return None

    # 去掉卢布符号和多余空格
    s = s.replace("₽", "").replace("руб", "").strip()

    # 如果是百分数，去掉百分号，之后按数值处理
    is_percentage = "%" in s
    s = s.replace("%", "").strip()

    # 替换俄语逗号小数点为英文点
    s = s.replace(",", ".")

    # 去掉所有空格（俄语千位分隔符是空格）
    s = s.replace(" ", "")

    try:
        val = float(s)
        # 如果是百分比，转为百分数值（如 17,67% -> 17.67）
        if is_percentage:
            return val
        return val
    except (ValueError, TypeError):
        return None