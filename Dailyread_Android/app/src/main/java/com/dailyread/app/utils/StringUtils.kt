package com.dailyread.app.utils

/**
 * 字符串工具类
 */
object StringUtils {

    /**
     * 计算纯中文字符数量（不包括标点符号、阿拉伯数字、英文字母等）
     */
    fun countChineseChars(text: String): Int {
        var count = 0
        for (char in text) {
            // 检查是否是中文字符
            // Unicode范围：基本汉字区 U+4E00 至 U+9FFF
            if (char in '\u4E00'..'\u9FFF') {
                count++
            }
        }
        return count
    }
}
