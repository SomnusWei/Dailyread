package com.dailyread.app.domain.usecase
import com.dailyread.app.data.repository.CheckInRepository
import com.dailyread.app.data.repository.ContentRepository
import com.dailyread.app.data.repository.AcupointRepository
import com.dailyread.app.data.local.database.entities.Acupoint
import com.google.gson.Gson
import com.google.gson.annotations.SerializedName
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.io.FileReader
import javax.inject.Inject
import javax.inject.Singleton

enum class ImportDataType {
    UNKNOWN,
    ARTICLES,
    ACUPOINTS,
    CONCEPTS,
    ALL
}

@Singleton
class ImportDataUseCase @Inject constructor(
    private val contentRepository: ContentRepository,
    private val checkInRepository: CheckInRepository,
    private val acupointRepository: AcupointRepository,
    private val conceptRepository: com.dailyread.app.data.repository.ConceptRepository,
    private val configRepository: com.dailyread.app.data.repository.ConfigRepository
) {
    data class ImportResult(
        val success: Boolean,
        val dataType: ImportDataType = ImportDataType.UNKNOWN,
        val newArticles: Int = 0,
        val updatedArticles: Int = 0,
        val skippedArticles: Int = 0,
        val newCheckIns: Int = 0,
        val skippedCheckIns: Int = 0,
        val newAcupoints: Int = 0,
        val skippedAcupoints: Int = 0,
        val newConcepts: Int = 0,
        val skippedConcepts: Int = 0,
        val errorMessage: String? = null
    )

    suspend operator fun invoke(filePath: String): ImportResult = withContext(Dispatchers.IO) {
        try {
            val gson = Gson()
            val jsonContent = FileReader(filePath).use { it.readText() }
            val jsonObject = gson.fromJson(jsonContent, java.util.Map::class.java)
            
            val dataType = jsonObject["dataType"] as? String ?: "all"
            val hasArticles = jsonObject["contents"] != null || jsonObject["articles"] != null
            val hasAcupoints = jsonObject["acupoints"] != null
            val hasConcepts = jsonObject["concepts"] != null

            return@withContext when {
                dataType == "articles" || (dataType == "all" && hasArticles && !hasAcupoints && !hasConcepts) -> {
                    importArticles(jsonContent)
                }
                dataType == "acupoints" || (dataType == "all" && !hasArticles && hasAcupoints && !hasConcepts) -> {
                    importAcupoints(jsonContent)
                }
                dataType == "concepts" || (dataType == "all" && !hasArticles && !hasAcupoints && hasConcepts) -> {
                    importConcepts(jsonContent)
                }
                dataType == "all" || (hasArticles || hasAcupoints || hasConcepts) -> {
                    val articleResult = if (hasArticles) importArticles(jsonContent) else ImportResult(success = true)
                    val acupointResult = if (hasAcupoints) importAcupoints(jsonContent) else ImportResult(success = true)
                    val conceptResult = if (hasConcepts) importConcepts(jsonContent) else ImportResult(success = true)
                    
                    ImportResult(
                        success = true,
                        dataType = ImportDataType.ALL,
                        newArticles = articleResult.newArticles,
                        updatedArticles = articleResult.updatedArticles,
                        skippedArticles = articleResult.skippedArticles,
                        newCheckIns = articleResult.newCheckIns,
                        skippedCheckIns = articleResult.skippedCheckIns,
                        newAcupoints = acupointResult.newAcupoints,
                        skippedAcupoints = acupointResult.skippedAcupoints,
                        newConcepts = conceptResult.newConcepts,
                        skippedConcepts = conceptResult.skippedConcepts
                    )
                }
                else -> {
                    ImportResult(
                        success = false,
                        errorMessage = "无法识别的文件格式"
                    )
                }
            }
        } catch (e: Exception) {
            e.printStackTrace()
            ImportResult(
                success = false,
                errorMessage = e.message ?: "导入失败"
            )
        }
    }

    private suspend fun importArticles(jsonContent: String): ImportResult {
        val gson = Gson()
        val exportData = gson.fromJson(jsonContent, ExportDataUseCase.ExportData::class.java)
        
        // 兼容两种数据格式
        val contentsToImport = if (exportData.articles.isNotEmpty()) {
            exportData.articles
        } else {
            exportData.contents
        }

        val existingContents = contentRepository.getAllContentsOnce()
        val existingCheckIns = checkInRepository.getAllCheckInRecords()

        val existingArticleKeys = existingContents.map { "${it.title}|${it.content}" }.toSet()
        val titleToExistingId = existingContents.associateBy { "${it.title}|${it.content}" }
        val existingCheckInKeys = existingCheckIns.map { "${it.contentId}|${it.date}" }.toSet()

        var newArticles = 0
        var updatedArticles = 0
        var skippedArticles = 0
        val oldIdToNewIdMap = mutableMapOf<Long, Long>()

        for (exportContent in contentsToImport) {
            val key = "${exportContent.title}|${exportContent.content}"
            val existingArticle = titleToExistingId[key]

            if (existingArticle != null) {
                val existingRequiredUpdated = existingArticle.isRequired != exportContent.isRequired ||
                        existingArticle.requiredDays != exportContent.requiredDays
                val existingIndependentRateUpdated = existingArticle.useIndependentCheckRate != exportContent.useIndependentCheckRate ||
                        existingArticle.independentCheckRate != exportContent.independentCheckRate
                if (existingRequiredUpdated || existingIndependentRateUpdated) {
                    val updatedEntity = ExportDataUseCase.ExportContent.toEntity(exportContent).copy(
                        id = existingArticle.id,
                        title = existingArticle.title,
                        content = existingArticle.content
                    )
                    contentRepository.updateContent(updatedEntity)
                    updatedArticles++
                } else {
                    skippedArticles++
                }
                oldIdToNewIdMap[exportContent.id] = existingArticle.id
            } else {
                val newEntity = ExportDataUseCase.ExportContent.toEntity(exportContent)
                val newId = contentRepository.insertContent(newEntity)
                oldIdToNewIdMap[exportContent.id] = newId
                newArticles++
            }
        }

        exportData.config?.let { exportConfig ->
            val currentConfig = configRepository.getConfigOnce()
            val updatedConfig = currentConfig.copy(
                dailyMinutes = exportConfig.dailyMinutes,
                targetCheckRate = exportConfig.targetCheckRate,
                keepScreenOn = exportConfig.keepScreenOn,
                autoSyncWebDav = exportConfig.autoSyncWebDav ?: currentConfig.autoSyncWebDav,
                yesterdayLongArticleIds = exportConfig.yesterdayLongArticleIds ?: currentConfig.yesterdayLongArticleIds
            )
            configRepository.updateConfig(updatedConfig)
        }

        var newCheckIns = 0
        var skippedCheckIns = 0

        for (exportCheckIn in exportData.checkIns) {
            val newContentId = oldIdToNewIdMap[exportCheckIn.contentId]
            if (newContentId != null) {
                val checkInKey = "${newContentId}|${exportCheckIn.date}"
                if (!existingCheckInKeys.contains(checkInKey)) {
                    val entity = ExportDataUseCase.ExportCheckIn.toEntity(exportCheckIn, newContentId)
                    checkInRepository.insertCheckIn(entity)
                    newCheckIns++
                } else {
                    skippedCheckIns++
                }
            }
        }

        return ImportResult(
            success = true,
            dataType = ImportDataType.ARTICLES,
            newArticles = newArticles,
            updatedArticles = updatedArticles,
            skippedArticles = skippedArticles,
            newCheckIns = newCheckIns,
            skippedCheckIns = skippedCheckIns
        )
    }

    private suspend fun importAcupoints(jsonContent: String): ImportResult {
        val gson = Gson()
        val exportData = gson.fromJson(jsonContent, ExportDataUseCase.ExportData::class.java)

        val existingAcupoints = acupointRepository.getAllAcupointsOnce()
        val existingAcupointNames = existingAcupoints.map { "${it.acupoint}|${it.meridian}" }.toSet()
        val nameToExistingId = existingAcupoints.associateBy { "${it.acupoint}|${it.meridian}" }

        var newAcupoints = 0
        var skippedAcupoints = 0

        for (exportAcupoint in exportData.acupoints) {
            val key = "${exportAcupoint.acupoint}|${exportAcupoint.meridian}"
            val existingAcupoint = nameToExistingId[key]

            if (existingAcupoint != null) {
                skippedAcupoints++
            } else {
                val newEntity = ExportDataUseCase.ExportAcupoint.toEntity(exportAcupoint)
                acupointRepository.insert(newEntity)
                newAcupoints++
            }
        }

        return ImportResult(
            success = true,
            dataType = ImportDataType.ACUPOINTS,
            newAcupoints = newAcupoints,
            skippedAcupoints = skippedAcupoints
        )
    }

    private suspend fun importConcepts(jsonContent: String): ImportResult {
        val gson = Gson()
        val exportData = gson.fromJson(jsonContent, ExportDataUseCase.ExportData::class.java)

        val existingConcepts = conceptRepository.getAllConceptsOnce()
        val existingConceptKeys = existingConcepts.map { 
            "${it.title}|${it.category}|${it.subject}|${it.subChapter}" 
        }.toSet()
        val keyToExistingConcept = existingConcepts.associateBy { 
            "${it.title}|${it.category}|${it.subject}|${it.subChapter}" 
        }

        var newConcepts = 0
        var skippedConcepts = 0

        for (exportConcept in exportData.concepts) {
            val key = "${exportConcept.title}|${exportConcept.category}|${exportConcept.subject}|${exportConcept.subChapter}"
            val existingConcept = keyToExistingConcept[key]

            if (existingConcept != null) {
                skippedConcepts++
            } else {
                var newEntity = ExportDataUseCase.ExportConcept.toEntity(exportConcept)
                // 处理图片数据，将 base64 编码的图片保存到本地文件
                newEntity = conceptRepository.saveImageFromBase64IfNeeded(newEntity)
                conceptRepository.insertConcept(newEntity)
                newConcepts++
            }
        }

        return ImportResult(
            success = true,
            dataType = ImportDataType.CONCEPTS,
            newConcepts = newConcepts,
            skippedConcepts = skippedConcepts
        )
    }
}
