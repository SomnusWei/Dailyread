package com.dailyread.app.domain.usecase

import android.content.Context
import android.net.Uri
import android.os.Environment
import androidx.documentfile.provider.DocumentFile
import com.dailyread.app.data.repository.CheckInRepository
import com.dailyread.app.data.repository.ContentRepository
import com.dailyread.app.data.repository.AcupointRepository
import com.dailyread.app.data.local.database.entities.Acupoint
import com.google.gson.Gson
import com.google.gson.annotations.SerializedName
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.io.File
import java.io.FileWriter
import java.time.LocalDateTime
import javax.inject.Inject
import javax.inject.Singleton

enum class ExportType {
    ALL,
    ARTICLES_ONLY,
    ACUPOINTS_ONLY,
    CONCEPTS_ONLY
}

@Singleton
class ExportDataUseCase @Inject constructor(
    private val contentRepository: ContentRepository,
    private val checkInRepository: CheckInRepository,
    private val acupointRepository: AcupointRepository,
    private val conceptRepository: com.dailyread.app.data.repository.ConceptRepository,
    private val configRepository: com.dailyread.app.data.repository.ConfigRepository,
    @ApplicationContext private val context: Context
) {
    sealed class Result {
        data class Success(val filePath: String, val exportType: ExportType) : Result()
        object Error : Result()
    }

    suspend operator fun invoke(exportType: ExportType = ExportType.ALL, savePath: String? = null): Result = withContext(Dispatchers.IO) {
        try {
            val contents = if (exportType == ExportType.ALL || exportType == ExportType.ARTICLES_ONLY) {
                contentRepository.getAllContentsOnce()
            } else {
                emptyList()
            }
            
            val checkIns = if (exportType == ExportType.ALL || exportType == ExportType.ARTICLES_ONLY) {
                checkInRepository.getAllCheckInRecords()
            } else {
                emptyList()
            }
            
            val acupoints = if (exportType == ExportType.ALL || exportType == ExportType.ACUPOINTS_ONLY) {
                acupointRepository.getAllAcupointsOnce()
            } else {
                emptyList()
            }
            
            val concepts = if (exportType == ExportType.ALL || exportType == ExportType.CONCEPTS_ONLY) {
                conceptRepository.getAllConceptsOnce()
            } else {
                emptyList()
            }
            
            val config = configRepository.getConfigOnce()

            val exportData = createExportData(exportType, config, contents, checkIns, acupoints, concepts)
            val jsonString = Gson().toJson(exportData)
            val fileName = createFileName(exportType)

            if (savePath != null) {
                writeToPath(savePath, fileName, jsonString)
            } else {
                writeToInternalStorage(fileName, jsonString)
            }
        } catch (e: Exception) {
            e.printStackTrace()
            Result.Error
        }
    }

    suspend fun exportToUri(exportType: ExportType, uri: Uri): Result = withContext(Dispatchers.IO) {
        try {
            val contents = if (exportType == ExportType.ALL || exportType == ExportType.ARTICLES_ONLY) {
                contentRepository.getAllContentsOnce()
            } else {
                emptyList()
            }
            
            val checkIns = if (exportType == ExportType.ALL || exportType == ExportType.ARTICLES_ONLY) {
                checkInRepository.getAllCheckInRecords()
            } else {
                emptyList()
            }
            
            val acupoints = if (exportType == ExportType.ALL || exportType == ExportType.ACUPOINTS_ONLY) {
                acupointRepository.getAllAcupointsOnce()
            } else {
                emptyList()
            }
            
            val concepts = if (exportType == ExportType.ALL || exportType == ExportType.CONCEPTS_ONLY) {
                conceptRepository.getAllConceptsOnce()
            } else {
                emptyList()
            }
            
            val config = configRepository.getConfigOnce()

            val exportData = createExportData(exportType, config, contents, checkIns, acupoints, concepts)
            val jsonString = Gson().toJson(exportData)
            val fileName = createFileName(exportType)

            writeToUriInternal(uri, fileName, jsonString)
        } catch (e: Exception) {
            e.printStackTrace()
            Result.Error
        }
    }

    private fun createExportData(
        exportType: ExportType,
        config: com.dailyread.app.data.local.database.entities.Config,
        contents: List<com.dailyread.app.data.local.database.entities.Content>,
        checkIns: List<com.dailyread.app.data.local.database.entities.ContentCheckIn>,
        acupoints: List<Acupoint>,
        concepts: List<com.dailyread.app.data.local.database.entities.Concept>
    ): ExportData {
        val exportContents = contents.map { ExportContent.fromEntity(it) }
        return ExportData(
            version = 4, // 更新版本号
            exportTime = LocalDateTime.now().toString(),
            dataType = when (exportType) {
                ExportType.ALL -> "all"
                ExportType.ARTICLES_ONLY -> "articles"
                ExportType.ACUPOINTS_ONLY -> "acupoints"
                ExportType.CONCEPTS_ONLY -> "concepts"
            },
            config = ExportConfig(
                dailyMinutes = config.dailyMinutes,
                targetCheckRate = config.targetCheckRate,
                keepScreenOn = config.keepScreenOn,
                autoSyncWebDav = config.autoSyncWebDav,
                yesterdayLongArticleIds = config.yesterdayLongArticleIds
            ),
            contents = exportContents,
            articles = exportContents, // 同时填充两个字段，保持兼容性
            checkIns = checkIns.map { ExportCheckIn.fromEntity(it) },
            acupoints = acupoints.map { ExportAcupoint.fromEntity(it) },
            concepts = concepts.map { ExportConcept.fromEntity(it) }
        )
    }

    private fun createFileName(exportType: ExportType): String {
        return when (exportType) {
            ExportType.ALL -> "daily_read_backup_${System.currentTimeMillis()}.json"
            ExportType.ARTICLES_ONLY -> "daily_read_articles_${System.currentTimeMillis()}.json"
            ExportType.ACUPOINTS_ONLY -> "daily_read_acupoints_${System.currentTimeMillis()}.json"
            ExportType.CONCEPTS_ONLY -> "daily_read_concepts_${System.currentTimeMillis()}.json"
        }
    }

    private fun writeToPath(savePath: String, fileName: String, jsonString: String): Result {
        val targetFile = File(savePath, fileName)
        if (targetFile.parentFile?.exists() == false) {
            targetFile.parentFile?.mkdirs()
        }

        return try {
            FileWriter(targetFile).use { writer ->
                writer.write(jsonString)
            }
            Result.Success(targetFile.absolutePath, ExportType.ALL)
        } catch (e: Exception) {
            val fallbackDir = File(context.getExternalFilesDir(null), "backups")
            if (!fallbackDir.exists()) {
                fallbackDir.mkdirs()
            }
            val fallbackFile = File(fallbackDir, fileName)
            FileWriter(fallbackFile).use { writer ->
                writer.write(jsonString)
            }
            Result.Success(fallbackFile.absolutePath, ExportType.ALL)
        }
    }

    private fun writeToInternalStorage(fileName: String, jsonString: String): Result {
        val filesDir = context.filesDir
        val backupDir = File(filesDir, "backups")
        if (!backupDir.exists()) {
            backupDir.mkdirs()
        }
        val file = File(backupDir, fileName)

        FileWriter(file).use { writer ->
            writer.write(jsonString)
        }
        return Result.Success(file.absolutePath, ExportType.ALL)
    }

    private fun writeToUriInternal(uri: Uri, fileName: String, jsonString: String): Result {
        val docFile = DocumentFile.fromTreeUri(context, uri)
        if (docFile != null) {
            val existingFile = docFile.findFile(fileName)
            if (existingFile != null) {
                existingFile.delete()
            }
            val newFile = docFile.createFile("application/json", fileName)
            if (newFile != null) {
                val outputStream = context.contentResolver.openOutputStream(newFile.uri)
                if (outputStream != null) {
                    outputStream.write(jsonString.toByteArray())
                    outputStream.close()
                    return Result.Success("${uri.path}/$fileName", ExportType.ALL)
                }
            }
        }
        
        return writeToInternalStorage(fileName, jsonString)
    }

    data class ExportData(
        val version: Int,
        val exportTime: String,
        val dataType: String,
        val config: ExportConfig?,
        val contents: List<ExportContent>,
        val articles: List<ExportContent> = emptyList(), // 新增字段，保持兼容性
        val checkIns: List<ExportCheckIn>,
        val acupoints: List<ExportAcupoint>,
        val concepts: List<ExportConcept> = emptyList()
    )

    data class ExportConfig(
        val dailyMinutes: Int,
        val targetCheckRate: Float,
        val keepScreenOn: Boolean,
        val autoSyncWebDav: Boolean?,
        val yesterdayLongArticleIds: String?
    )

    data class ExportContent(
        @SerializedName("id") val id: Long,
        @SerializedName("title") val title: String,
        @SerializedName("content") val content: String,
        @SerializedName("contentHtml") val contentHtml: String?,
        @SerializedName("chineseChars") val chineseChars: Int,
        @SerializedName("fontFamily") val fontFamily: String,
        @SerializedName("fontSize") val fontSize: Int,
        @SerializedName("fontColor") val fontColor: String,
        @SerializedName("isBold") val isBold: Boolean,
        @SerializedName("isReading") val isReading: Boolean,
        @SerializedName("isRequired") val isRequired: Boolean,
        @SerializedName("requiredDays") val requiredDays: String,
        @SerializedName("useIndependentCheckRate") val useIndependentCheckRate: Boolean,
        @SerializedName("independentCheckRate") val independentCheckRate: Float,
        @SerializedName("createTime") val createTime: String
    ) {
        companion object {
            fun fromEntity(entity: com.dailyread.app.data.local.database.entities.Content): ExportContent {
                return ExportContent(
                    id = entity.id,
                    title = entity.title,
                    content = entity.content,
                    contentHtml = entity.contentHtml,
                    chineseChars = entity.chineseChars,
                    fontFamily = entity.fontFamily,
                    fontSize = entity.fontSize,
                    fontColor = entity.fontColor,
                    isBold = entity.isBold,
                    isReading = entity.isReading,
                    isRequired = entity.isRequired,
                    requiredDays = entity.requiredDays,
                    useIndependentCheckRate = entity.useIndependentCheckRate,
                    independentCheckRate = entity.independentCheckRate,
                    createTime = entity.createTime
                )
            }

            fun toEntity(exportContent: ExportContent): com.dailyread.app.data.local.database.entities.Content {
                return com.dailyread.app.data.local.database.entities.Content(
                    id = 0,
                    title = exportContent.title,
                    content = exportContent.content,
                    contentHtml = exportContent.contentHtml,
                    chineseChars = exportContent.chineseChars,
                    fontFamily = exportContent.fontFamily,
                    fontSize = exportContent.fontSize,
                    fontColor = exportContent.fontColor,
                    isBold = exportContent.isBold,
                    isReading = exportContent.isReading,
                    isRequired = exportContent.isRequired,
                    requiredDays = exportContent.requiredDays,
                    useIndependentCheckRate = exportContent.useIndependentCheckRate,
                    independentCheckRate = exportContent.independentCheckRate,
                    createTime = exportContent.createTime
                )
            }
        }
    }

    data class ExportCheckIn(
        @SerializedName("contentId") val contentId: Long,
        @SerializedName("date") val date: String
    ) {
        companion object {
            fun fromEntity(entity: com.dailyread.app.data.local.database.entities.ContentCheckIn): ExportCheckIn {
                return ExportCheckIn(
                    contentId = entity.contentId,
                    date = entity.date
                )
            }

            fun toEntity(exportCheckIn: ExportCheckIn, newContentId: Long): com.dailyread.app.data.local.database.entities.ContentCheckIn {
                return com.dailyread.app.data.local.database.entities.ContentCheckIn(
                    contentId = newContentId,
                    date = exportCheckIn.date
                )
            }
        }
    }

    data class ExportAcupoint(
        @SerializedName("id") val id: Long,
        @SerializedName("acupoint") val acupoint: String,
        @SerializedName("meridian") val meridian: String,
        @SerializedName("acupointProperty") val acupointProperty: String,
        @SerializedName("location") val location: String,
        @SerializedName("function") val function: String,
        @SerializedName("indications") val indications: String,
        @SerializedName("anatomy") val anatomy: String,
        @SerializedName("operation") val operation: String,
        @SerializedName("contraindications") val contraindications: String,
        @SerializedName("locationImagePath") val locationImagePath: String?,
        @SerializedName("locationImageBase64") val locationImageBase64: String?,
        @SerializedName("note") val note: String,
        @SerializedName("createTime") val createTime: String
    ) {
        companion object {
            fun fromEntity(entity: Acupoint): ExportAcupoint {
                return ExportAcupoint(
                    id = entity.id,
                    acupoint = entity.acupoint,
                    meridian = entity.meridian,
                    acupointProperty = entity.acupointProperty,
                    location = entity.location,
                    function = entity.function,
                    indications = entity.indications,
                    anatomy = entity.anatomy,
                    operation = entity.operation,
                    contraindications = entity.contraindications,
                    locationImagePath = entity.locationImagePath,
                    locationImageBase64 = entity.locationImageBase64,
                    note = entity.note,
                    createTime = entity.createTime
                )
            }

            fun toEntity(exportAcupoint: ExportAcupoint): Acupoint {
                return Acupoint(
                    id = 0,
                    acupoint = exportAcupoint.acupoint,
                    meridian = exportAcupoint.meridian,
                    acupointProperty = exportAcupoint.acupointProperty,
                    location = exportAcupoint.location,
                    function = exportAcupoint.function,
                    indications = exportAcupoint.indications,
                    anatomy = exportAcupoint.anatomy,
                    operation = exportAcupoint.operation,
                    contraindications = exportAcupoint.contraindications,
                    locationImagePath = exportAcupoint.locationImagePath,
                    locationImageBase64 = exportAcupoint.locationImageBase64,
                    note = exportAcupoint.note,
                    createTime = exportAcupoint.createTime
                )
            }
        }
    }

    data class ExportConcept(
        @SerializedName("id") val id: Long,
        @SerializedName("subject") val subject: String,
        @SerializedName("category") val category: String,
        @SerializedName("subChapter") val subChapter: String,
        @SerializedName("title") val title: String,
        @SerializedName("content") val content: String,
        @SerializedName("imagePath") val imagePath: String?,
        @SerializedName("imageBase64") val imageBase64: String?,
        @SerializedName("note") val note: String,
        @SerializedName("isEnabled") val isEnabled: Boolean,
        @SerializedName("createTime") val createTime: String,
        @SerializedName("lastModified") val lastModified: String
    ) {
        companion object {
            fun fromEntity(entity: com.dailyread.app.data.local.database.entities.Concept): ExportConcept {
                return ExportConcept(
                    id = entity.id,
                    subject = entity.subject,
                    category = entity.category,
                    subChapter = entity.subChapter,
                    title = entity.title,
                    content = entity.content,
                    imagePath = entity.imagePath,
                    imageBase64 = entity.imageBase64,
                    note = entity.note,
                    isEnabled = entity.isEnabled,
                    createTime = entity.createTime,
                    lastModified = entity.lastModified
                )
            }

            fun toEntity(exportConcept: ExportConcept): com.dailyread.app.data.local.database.entities.Concept {
                return com.dailyread.app.data.local.database.entities.Concept(
                    id = 0,
                    subject = exportConcept.subject,
                    category = exportConcept.category,
                    subChapter = exportConcept.subChapter,
                    title = exportConcept.title,
                    content = exportConcept.content,
                    imagePath = exportConcept.imagePath,
                    imageBase64 = exportConcept.imageBase64,
                    note = exportConcept.note,
                    isEnabled = exportConcept.isEnabled,
                    createTime = exportConcept.createTime,
                    lastModified = exportConcept.lastModified
                )
            }
        }
    }
}
