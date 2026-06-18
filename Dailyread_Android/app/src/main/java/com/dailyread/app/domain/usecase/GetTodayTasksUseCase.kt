package com.dailyread.app.domain.usecase

import com.dailyread.app.data.repository.CheckInRepository
import com.dailyread.app.data.repository.ConfigRepository
import com.dailyread.app.data.repository.ContentRepository
import com.dailyread.app.data.local.database.entities.toDomainModel
import com.dailyread.app.domain.model.Article
import com.google.gson.Gson
import com.google.gson.reflect.TypeToken
import kotlinx.coroutines.flow.firstOrNull
import java.time.LocalDate
import java.time.YearMonth
import java.time.LocalDateTime
import javax.inject.Inject
import javax.inject.Singleton
import kotlin.math.max
import kotlin.random.Random

@Singleton
class GetTodayTasksUseCase @Inject constructor(
    private val contentRepository: ContentRepository,
    private val checkInRepository: CheckInRepository,
    private val configRepository: ConfigRepository
) {
    private val gson = Gson()
    
    suspend operator fun invoke(): List<Article> {
        return try {
            val today = LocalDate.now()
            val config = configRepository.getConfigOnce()
            val todayStr = today.toString()
            val dayOfWeek = today.dayOfWeek.value
            
            // 检查是否需要自动重置（00:01逻辑）
            checkAndAutoResetIfNeeded(config, todayStr)
            
            // 检查缓存
            if (config.tasksLocked && config.tasksLockedDate == todayStr && config.todayTasks != null) {
                try {
                    val type = object : TypeToken<List<Article>>() {}.type
                    val cachedTasks: List<Article> = gson.fromJson(config.todayTasks, type)
                    return cachedTasks
                } catch (e: Exception) {
                    // JSON解析失败，继续重新生成
                }
            }
            
            // 获取配置参数
            val dailyMinutes = config.dailyMinutes.coerceIn(5, 120)
            val targetWords = 250 * dailyMinutes
            val maxWords = (targetWords * 1.05).toInt()
            val minWords = (targetWords * 0.9).toInt()
            val longArticleThreshold = (targetWords * 0.3).toInt()
            val longArticleMaxSum = (targetWords * 0.75).toInt()
            
            // 获取所有文章
            val allContents = try {
                contentRepository.getAllContentsOnce()
            } catch (e: Exception) {
                return emptyList()
            }
            
            // 第一步：筛选必读文章
            val requiredArticles = getRequiredArticles(allContents, dayOfWeek)
            
            // 第二步：筛选任务池
            val taskPool = buildTaskPool(allContents, today, config.targetCheckRate)
            
            // 第三步：划分长短类型
            val (longArticles, shortArticles) = categorizeArticles(taskPool, longArticleThreshold)
            
            // 解析昨日长文ID
            val yesterdayIds = parseYesterdayIds(config.yesterdayLongArticleIds ?: "")
            
            // 第四步：选择长文
            val selectedLongArticles = selectLongArticles(
                longArticles,
                longArticleMaxSum,
                yesterdayIds,
                Random(System.currentTimeMillis())
            )
            
            // 第五步：补充短文
            val selectedShortArticles = selectShortArticles(
                shortArticles,
                selectedLongArticles,
                targetWords,
                Random(System.currentTimeMillis())
            )
            
            // 组合最终结果
            val result = requiredArticles + selectedLongArticles + selectedShortArticles
            val totalWords = result.sumOf { it.chineseChars }
            
            // 记录今天的任务并锁定
            if (totalWords >= minWords && result.isNotEmpty()) {
                try {
                    val tasksJson = gson.toJson(result)
                    val longArticleIds = selectedLongArticles.mapNotNull { it.id }
                    configRepository.updateConfig(
                        config.copy(
                            todayTasks = tasksJson,
                            tasksLocked = true,
                            tasksLockedDate = todayStr,
                            yesterdayLongArticleIds = gson.toJson(longArticleIds)
                        )
                    )
                } catch (e: Exception) {
                    // 忽略保存错误
                }
            }
            
            result
        } catch (e: Exception) {
            e.printStackTrace()
            emptyList()
        }
    }
    
    private suspend fun checkAndAutoResetIfNeeded(config: com.dailyread.app.data.local.database.entities.Config, todayStr: String) {
        try {
            val now = LocalDateTime.now()
            val hour = now.hour
            val minute = now.minute
            
            // 在00:01分自动重置
            if (hour == 0 && minute == 1) {
                if (config.tasksLocked && config.tasksLockedDate != todayStr) {
                    configRepository.updateConfig(
                        config.copy(
                            tasksLocked = false,
                            tasksLockedDate = null,
                            todayTasks = null
                        )
                    )
                }
            }
        } catch (e: Exception) {
            // 忽略错误
        }
    }
    
    private fun parseYesterdayIds(json: String?): List<Long> {
        return try {
            if (json.isNullOrBlank()) {
                emptyList()
            } else {
                val type = object : TypeToken<List<Long>>() {}.type
                gson.fromJson(json, type)
            }
        } catch (e: Exception) {
            emptyList()
        }
    }
    
    /**
     * 第一步：筛选必读文章
     * 条件：必读 + 当日属于必读星期 + 字数不为0
     */
    private fun getRequiredArticles(
        allContents: List<com.dailyread.app.data.local.database.entities.Content>,
        dayOfWeek: Int
    ): List<Article> {
        return try {
            allContents
                .filter { content ->
                    content.isRequired && 
                    content.requiredDays.contains(dayOfWeek.toString()) && 
                    content.chineseChars > 0
                }
                .mapNotNull { 
                    try {
                        it.toDomainModel()
                    } catch (e: Exception) {
                        null
                    }
                }
        } catch (e: Exception) {
            emptyList()
        }
    }
    
    /**
     * 第二步：筛选任务池
     * 条件：非必读、字数不为0、阅读开关开启、完成率未达标
     */
    private suspend fun buildTaskPool(
        allContents: List<com.dailyread.app.data.local.database.entities.Content>,
        today: LocalDate,
        systemTargetRate: Float
    ): List<Article> {
        val taskPool = mutableListOf<Article>()
        
        for (content in allContents) {
            try {
                // 排除必读和字数为0的文章
                if (content.isRequired || content.chineseChars <= 0) continue
                
                // 第一层：阅读开关必须开启
                if (!content.isReading) continue
                
                // 第二层：完成率校验
                val combinedRate = getCombinedRate(content.id, today)
                val targetRate = if (content.useIndependentCheckRate) {
                    content.independentCheckRate
                } else {
                    systemTargetRate
                }
                
                val threshold = if (today.dayOfMonth <= 5) {
                    max(0.0f, targetRate - 5.0f)
                } else {
                    targetRate
                }
                
                // 未达成目标才进入任务池
                if (combinedRate <= threshold) {
                    try {
                        taskPool.add(content.toDomainModel())
                    } catch (e: Exception) {
                        // 忽略转换错误
                    }
                }
            } catch (e: Exception) {
                // 忽略单个文章的筛选错误
            }
        }
        
        return taskPool
    }
    
    /**
     * 第三步：划分长短类型
     * 长文：字数 ≥ 目标字数 × 30%
     * 短文：字数 < 目标字数 × 30%
     */
    private fun categorizeArticles(pool: List<Article>, threshold: Int): Pair<List<Article>, List<Article>> {
        val longArticles = pool.filter { it.chineseChars >= threshold }
        val shortArticles = pool.filter { it.chineseChars < threshold }
        return Pair(longArticles, shortArticles)
    }
    
    /**
     * 第四步：选择长文
     * 优先规避昨日已选长文
     */
    private fun selectLongArticles(
        longArticles: List<Article>,
        maxSum: Int,
        yesterdayIds: List<Long>,
        random: Random
    ): List<Article> {
        if (longArticles.isEmpty()) return emptyList()
        
        // 长文组仅有1篇
        if (longArticles.size == 1) {
            val article = longArticles.first()
            return if (article.chineseChars <= maxSum) {
                listOf(article)
            } else {
                emptyList()
            }
        }
        
        // 长文组大于1篇
        // 先剔除昨日已选
        var candidates = longArticles.filter { it.id !in yesterdayIds }
        
        // 若剔除后为空，则恢复使用原始长文组
        if (candidates.isEmpty()) {
            candidates = longArticles
        }
        
        // 在备选池中随机挑选1~3篇
        val count = when {
            candidates.size >= 3 -> random.nextInt(1, 4) // 1, 2, or 3
            candidates.size == 2 -> random.nextInt(1, 3) // 1 or 2
            else -> 1
        }
        
        // 尝试不同组合，找满足字数限制的
        val selected = findBestLongArticleCombination(candidates, count, maxSum, random)
        
        return selected
    }
    
    private fun findBestLongArticleCombination(
        candidates: List<Article>,
        targetCount: Int,
        maxSum: Int,
        random: Random
    ): List<Article> {
        // 按目标数量尝试
        val shuffled = candidates.shuffled(random)
        
        // 尝试所有可能的组合
        val combinations = mutableListOf<List<Article>>()
        
        for (i in shuffled.indices) {
            val combination = mutableListOf<Article>()
            var sum = 0
            
            for (j in i until minOf(i + targetCount, shuffled.size)) {
                val article = shuffled[j]
                if (sum + article.chineseChars <= maxSum) {
                    combination.add(article)
                    sum += article.chineseChars
                }
            }
            
            if (combination.isNotEmpty()) {
                combinations.add(combination)
            }
        }
        
        // 选择字数最多的组合
        return combinations.maxByOrNull { it.sumOf { a -> a.chineseChars } } ?: emptyList()
    }
    
    /**
     * 第五步：补充短文
     */
    private fun selectShortArticles(
        shortArticles: List<Article>,
        selectedLongArticles: List<Article>,
        targetWords: Int,
        random: Random
    ): List<Article> {
        val longSum = selectedLongArticles.sumOf { it.chineseChars }
        val remaining = targetWords - longSum
        
        if (remaining <= 0 || shortArticles.isEmpty()) {
            return emptyList()
        }
        
        val result = mutableListOf<Article>()
        var currentSum = 0
        val selectedIds = selectedLongArticles.mapNotNull { it.id }.toMutableSet()
        
        val shuffled = shortArticles.shuffled(random)
        
        for (article in shuffled) {
            if (article.id in selectedIds) continue
            
            if (currentSum + article.chineseChars <= targetWords) {
                result.add(article)
                currentSum += article.chineseChars
                selectedIds.add(article.id)
            }
            
            // 达到目标就停止
            if (currentSum >= remaining) break
        }
        
        return result
    }
    
    private suspend fun getCombinedRate(contentId: Long, today: LocalDate): Float {
        return try {
            val currentMonthRate = getArticleCheckRate(contentId, today.year, today.monthValue, today)

            if (today.dayOfMonth <= 5) {
                val lastMonth = today.minusMonths(1)
                val lastMonthRate = getArticleCheckRate(contentId, lastMonth.year, lastMonth.monthValue, today)
                (currentMonthRate + lastMonthRate) / 2
            } else {
                currentMonthRate
            }
        } catch (e: Exception) {
            0f
        }
    }

    private suspend fun getArticleCheckRate(
        contentId: Long,
        year: Int,
        month: Int,
        today: LocalDate
    ): Float {
        return try {
            val yearPrefix = year.toString()
            val checkIns = checkInRepository.getCheckInDataByYear(yearPrefix)
                .filter { 
                    it.contentId == contentId && it.date.startsWith("$year-${String.format("%02d", month)}")
                }
            
            val daysInMonth = YearMonth.of(year, month).lengthOfMonth()
            val totalDays = if (year == today.year && month == today.monthValue) {
                today.dayOfMonth
            } else {
                daysInMonth
            }

            if (totalDays > 0) checkIns.size.toFloat() / totalDays.toFloat() * 100f else 0f
        } catch (e: Exception) {
            0f
        }
    }
}
