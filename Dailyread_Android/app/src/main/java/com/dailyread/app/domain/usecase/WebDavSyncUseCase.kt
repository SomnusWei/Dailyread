package com.dailyread.app.domain.usecase

import android.content.Context
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.util.Base64
import com.dailyread.app.data.local.database.entities.Acupoint
import com.dailyread.app.data.local.database.entities.Concept
import com.dailyread.app.data.local.database.entities.Config
import dagger.Lazy
import com.dailyread.app.data.repository.AcupointRepository
import com.dailyread.app.data.repository.CheckInRepository
import com.dailyread.app.data.repository.ConfigRepository
import com.dailyread.app.data.repository.ContentRepository
import com.dailyread.app.data.repository.ConceptRepository
import com.google.gson.Gson
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.io.ByteArrayOutputStream
import java.io.File
import java.security.MessageDigest
import java.time.LocalDateTime
import java.time.format.DateTimeFormatter
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class WebDavSyncUseCase @Inject constructor(
    private val contentRepository: ContentRepository,
    private val checkInRepository: CheckInRepository,
    private val acupointRepositoryLazy: Lazy<AcupointRepository>,
    private val conceptRepositoryLazy: Lazy<ConceptRepository>,
    private val configRepository: ConfigRepository,
    private val webDavClient: WebDavClient,
    @ApplicationContext private val context: Context
) {
    private val gson = Gson()
    private val dateFormatter = DateTimeFormatter.ISO_LOCAL_DATE_TIME

    private val acupointRepository: AcupointRepository
        get() = acupointRepositoryLazy.get()

    private val conceptRepository: ConceptRepository
        get() = conceptRepositoryLazy.get()

    companion object {
        private const val SYNC_INDEX_FILE = "sync_index.json"
        private const val ARTICLES_FILE = "articles.json"
        private const val ACUPOINTS_FILE = "acupoints.json"
        private const val CONCEPTS_FILE = "concepts.json"
        private const val CHECKINS_FILE = "checkins.json"
        private const val CURRENT_VERSION = 5
    }

    data class SyncIndex(
        val version: Int = CURRENT_VERSION,
        val syncTime: String,
        val files: Map<String, FileInfo>
    )

    data class FileInfo(
        val filename: String,
        val syncTime: String,
        val count: Int,
        val hash: String? = null
    )

    private fun encodeImageToBase64(imagePath: String?): String? {
        return imagePath?.let { path ->
            try {
                val file = File(path)
                if (file.exists()) {
                    // 非常严格的文件大小限制
                    val maxFileSize = 500 * 1024 // 500KB
                    if (file.length() > maxFileSize) {
                        // 大文件进行极其激进的压缩
                        val boundsOptions = BitmapFactory.Options().apply {
                            inJustDecodeBounds = true
                            inPreferredConfig = Bitmap.Config.RGB_565
                        }
                        BitmapFactory.decodeFile(path, boundsOptions)
                        
                        // 非常激进的采样率计算
                        val sampleSize = calculateInSampleSize(boundsOptions, 500, 500)
                        
                        val decodeOptions = BitmapFactory.Options().apply {
                            inJustDecodeBounds = false
                            inSampleSize = sampleSize
                            inPreferredConfig = Bitmap.Config.RGB_565
                            inPurgeable = true
                            inInputShareable = true
                        }
                        val bitmap = BitmapFactory.decodeFile(path, decodeOptions)
                        if (bitmap != null) {
                            val stream = ByteArrayOutputStream()
                            try {
                                // 最高压缩率
                                bitmap.compress(Bitmap.CompressFormat.JPEG, 40, stream)
                                val compressedBytes = stream.toByteArray()
                                Base64.encodeToString(compressedBytes, Base64.NO_WRAP)
                            } finally {
                                stream.close()
                                bitmap.recycle()
                            }
                        } else null
                    } else {
                        // 所有图片都进行压缩
                        val boundsOptions = BitmapFactory.Options().apply {
                            inJustDecodeBounds = true
                        }
                        BitmapFactory.decodeFile(path, boundsOptions)
                        
                        // 只要超过中等尺寸就压缩
                        val needsCompression = (boundsOptions.outWidth > 1000 || boundsOptions.outHeight > 1000)
                        
                        if (needsCompression) {
                            val sampleSize = calculateInSampleSize(boundsOptions, 800, 800)
                            val decodeOptions = BitmapFactory.Options().apply {
                                inJustDecodeBounds = false
                                inSampleSize = sampleSize
                                inPreferredConfig = Bitmap.Config.RGB_565
                            }
                            val bitmap = BitmapFactory.decodeFile(path, decodeOptions)
                            if (bitmap != null) {
                                val stream = ByteArrayOutputStream()
                                try {
                                    bitmap.compress(Bitmap.CompressFormat.JPEG, 50, stream)
                                    val compressedBytes = stream.toByteArray()
                                    Base64.encodeToString(compressedBytes, Base64.NO_WRAP)
                                } finally {
                                    stream.close()
                                    bitmap.recycle()
                                }
                            } else null
                        } else {
                            val bytes = file.readBytes()
                            Base64.encodeToString(bytes, Base64.NO_WRAP)
                        }
                    }
                } else null
            } catch (e: OutOfMemoryError) {
                System.gc()
                e.printStackTrace()
                null
            } catch (e: Exception) {
                e.printStackTrace()
                null
            }
        }
    }
    
    private fun calculateInSampleSize(options: BitmapFactory.Options, reqWidth: Int, reqHeight: Int): Int {
        // 原始图片尺寸
        val height = options.outHeight.takeIf { it > 0 } ?: 1024
        val width = options.outWidth.takeIf { it > 0 } ?: 1024
        var inSampleSize = 1
        
        if (height > reqHeight || width > reqWidth) {
            val halfHeight = height / 2
            val halfWidth = width / 2
            
            // 计算合适的采样率，保持宽高比 - 更激进的压缩
            while (halfHeight / inSampleSize >= reqHeight && halfWidth / inSampleSize >= reqWidth) {
                inSampleSize *= 2
            }
        }
        
        return inSampleSize
    }

    private fun decodeBase64ToImage(base64: String?, prefix: String = "image"): String? {
        return base64?.takeIf { it.isNotBlank() }?.let { b64 ->
            try {
                val bytes = Base64.decode(b64, Base64.NO_WRAP)
                // 防止过大的base64数据
                if (bytes.size > 5 * 1024 * 1024) { // 限制5MB
                    return null
                }
                val fileName = "${prefix}_${System.currentTimeMillis()}.jpg"
                val file = File(context.filesDir, fileName)
                file.writeBytes(bytes)
                file.absolutePath
            } catch (e: OutOfMemoryError) {
                e.printStackTrace()
                null
            } catch (e: Exception) {
                e.printStackTrace()
                null
            }
        }
    }

    private fun calculateHash(data: String): String {
        val bytes = data.toByteArray(Charsets.UTF_8)
        val digest = MessageDigest.getInstance("SHA-256")
        val hashBytes = digest.digest(bytes)
        return hashBytes.joinToString("") { "%02x".format(it) }.substring(0, 16)
    }

    private fun buildSyncIndex(
        articlesCount: Int,
        acupointsCount: Int,
        conceptsCount: Int,
        checkinsCount: Int
    ): SyncIndex {
        val now = LocalDateTime.now().format(dateFormatter)
        return SyncIndex(
            version = CURRENT_VERSION,
            syncTime = now,
            files = mapOf(
                "articles" to FileInfo(ARTICLES_FILE, now, articlesCount),
                "acupoints" to FileInfo(ACUPOINTS_FILE, now, acupointsCount),
                "concepts" to FileInfo(CONCEPTS_FILE, now, conceptsCount),
                "checkins" to FileInfo(CHECKINS_FILE, now, checkinsCount)
            )
        )
    }

    private fun getLocalIndexFile(): String? {
        val file = File(context.filesDir, SYNC_INDEX_FILE)
        return if (file.exists()) file.readText() else null
    }

    private fun saveLocalIndex(index: SyncIndex) {
        val file = File(context.filesDir, SYNC_INDEX_FILE)
        file.writeText(gson.toJson(index))
    }

    private suspend fun downloadIndexFile(config: Config): SyncIndex? {
        val result = webDavClient.downloadFile(
            config.webdavServerUrl,
            config.webdavUsername,
            config.webdavPassword,
            "${config.webdavRemotePath}/$SYNC_INDEX_FILE"
        )

        return when (result) {
            is WebDavClient.WebDavResult.Success -> {
                try {
                    gson.fromJson(result.data, SyncIndex::class.java)
                } catch (e: Exception) {
                    null
                }
            }
            is WebDavClient.WebDavResult.Error -> null
        }
    }

    private suspend fun downloadFileIfExists(config: Config, filename: String): String? {
        val result = webDavClient.downloadFile(
            config.webdavServerUrl,
            config.webdavUsername,
            config.webdavPassword,
            "${config.webdavRemotePath}/$filename"
        )

        return when (result) {
            is WebDavClient.WebDavResult.Success -> result.data
            is WebDavClient.WebDavResult.Error -> null
        }
    }

    private suspend fun uploadFileToRemote(config: Config, filename: String, data: String) {
        webDavClient.uploadFile(
            config.webdavServerUrl,
            config.webdavUsername,
            config.webdavPassword,
            "${config.webdavRemotePath}/$filename",
            data
        )
    }

    private suspend fun shouldDownload(fileType: String, remoteIndex: SyncIndex): Boolean {
        val localIndexFile = getLocalIndexFile()
        val remoteFileInfo = remoteIndex.files[fileType] ?: return true

        return if (localIndexFile != null) {
            val localIndex = try {
                gson.fromJson(localIndexFile, SyncIndex::class.java)
            } catch (e: Exception) {
                null
            }

            val localFileInfo = localIndex?.files?.get(fileType)

            if (localFileInfo == null) {
                true
            } else {
                try {
                    val localTime = LocalDateTime.parse(localFileInfo.syncTime)
                    val remoteTime = LocalDateTime.parse(remoteFileInfo.syncTime)
                    remoteTime.isAfter(localTime)
                } catch (e: Exception) {
                    true
                }
            }
        } else {
            true
        }
    }

    data class SyncResult(
        val success: Boolean,
        val uploadedArticles: Int = 0,
        val downloadedArticles: Int = 0,
        val uploadedCheckIns: Int = 0,
        val downloadedCheckIns: Int = 0,
        val uploadedAcupoints: Int = 0,
        val downloadedAcupoints: Int = 0,
        val uploadedConcepts: Int = 0,
        val downloadedConcepts: Int = 0,
        val conflicts: List<SyncConflict> = emptyList(),
        val errorMessage: String? = null
    )

    data class SyncConflict(
        val type: ConflictType,
        val localData: String,
        val remoteData: String,
        val localTimestamp: String,
        val remoteTimestamp: String
    )

    enum class ConflictType {
        ARTICLE_CONTENT,
        CHECKIN_RECORD,
        ACUPOINT_DATA,
        CONCEPT_DATA
    }

    data class SyncData(
        val version: Int = 4,
        val exportTime: String,
        val articles: List<SyncArticle> = emptyList(),
        val checkIns: List<SyncCheckIn> = emptyList(),
        val acupoints: List<SyncAcupoint> = emptyList(),
        val concepts: List<SyncConcept> = emptyList(),
        val config: SyncConfig? = null
    )

    data class SyncArticle(
        val id: Long,
        val title: String,
        val content: String,
        val contentHtml: String?,
        val chineseChars: Int,
        val fontFamily: String,
        val fontSize: Int,
        val fontColor: String,
        val isBold: Boolean,
        val isReading: Boolean,
        val isRequired: Boolean,
        val requiredDays: String,
        val useIndependentCheckRate: Boolean,
        val independentCheckRate: Float,
        val createTime: String,
        val lastModified: String
    )

    data class SyncCheckIn(
        val id: Long,
        val contentId: Long,
        val date: String,
        val lastModified: String
    )

    data class SyncAcupoint(
        val id: Long,
        val acupoint: String,
        val meridian: String,
        val acupointProperty: String = "",
        val location: String = "",
        val function: String = "",
        val indications: String = "",
        val anatomy: String = "",
        val operation: String = "",
        val contraindications: String = "",
        val locationImagePath: String? = null,
        val locationImageBase64: String? = null,
        val note: String = "",
        val createTime: String = "",
        val lastModified: String = ""
    )

    data class SyncConcept(
        val id: Long,
        val subject: String = "",
        val category: String = "",
        val subChapter: String = "",
        val title: String = "",
        val content: String = "",
        val imagePath: String? = null,
        val imageBase64: String? = null,
        val note: String = "",
        val isEnabled: Boolean = true,
        val createTime: String = "",
        val lastModified: String = ""
    )

    data class SyncConfig(
        val dailyMinutes: Int = 20,
        val targetCheckRate: Float = 30.0f,
        val keepScreenOn: Boolean = false,
        val autoSyncWebDav: Boolean = false,
        val yesterdayLongArticleIds: String = ""
    )

    suspend fun testConnection(config: Config): SyncResult = withContext(Dispatchers.IO) {
        when (val result = webDavClient.testConnection(
            config.webdavServerUrl,
            config.webdavUsername,
            config.webdavPassword,
            config.webdavRemotePath
        )) {
            is WebDavClient.WebDavResult.Success -> {
                runCatching {
                    webDavClient.createDirectory(
                        config.webdavServerUrl,
                        config.webdavUsername,
                        config.webdavPassword,
                        config.webdavRemotePath
                    )
                }
                SyncResult(success = true)
            }
            is WebDavClient.WebDavResult.Error -> {
                SyncResult(success = false, errorMessage = result.message)
            }
        }
    }

    suspend fun syncFromRemote(config: Config): SyncResult = withContext(Dispatchers.IO) {
        try {
            val remoteIndex = downloadIndexFile(config)

            if (remoteIndex == null) {
                return@withContext syncFromRemoteFull(config)
            }

            var downloadedArticles = 0
            var downloadedCheckIns = 0
            var downloadedAcupoints = 0
            var downloadedConcepts = 0
            val conflicts = mutableListOf<SyncConflict>()

            // 分步处理，每个处理完释放内存并给GC时间
            if (config.syncArticlesEnabled && shouldDownload("articles", remoteIndex)) {
                System.gc()
                Thread.sleep(100)
                
                val articlesData = downloadFileIfExists(config, ARTICLES_FILE)
                if (articlesData != null) {
                    val articles = try { gson.fromJson(articlesData, Array<SyncArticle>::class.java).toList() } catch (e: Exception) { emptyList() }
                    downloadedArticles = processDownloadedArticles(articles)
                    System.gc()
                    Thread.sleep(100)
                }
            }

            if (config.syncAcupointsEnabled && shouldDownload("acupoints", remoteIndex)) {
                System.gc()
                Thread.sleep(100)
                
                val acupointsData = downloadFileIfExists(config, ACUPOINTS_FILE)
                if (acupointsData != null) {
                    val acupoints = try { gson.fromJson(acupointsData, Array<SyncAcupoint>::class.java).toList() } catch (e: Exception) { emptyList() }
                    downloadedAcupoints = processDownloadedAcupoints(acupoints)
                    System.gc()
                    Thread.sleep(100)
                }
            }

            if (config.syncConceptsEnabled && shouldDownload("concepts", remoteIndex)) {
                System.gc()
                Thread.sleep(100)
                
                val conceptsData = downloadFileIfExists(config, CONCEPTS_FILE)
                if (conceptsData != null) {
                    val concepts = try { gson.fromJson(conceptsData, Array<SyncConcept>::class.java).toList() } catch (e: Exception) { emptyList() }
                    downloadedConcepts = processDownloadedConcepts(concepts)
                    System.gc()
                    Thread.sleep(100)
                }
            }

            if (shouldDownload("checkins", remoteIndex)) {
                System.gc()
                Thread.sleep(50)
                
                val checkinsData = downloadFileIfExists(config, CHECKINS_FILE)
                if (checkinsData != null) {
                    val checkins = try { gson.fromJson(checkinsData, Array<SyncCheckIn>::class.java).toList() } catch (e: Exception) { emptyList() }
                    downloadedCheckIns = processDownloadedCheckins(checkins)
                    System.gc()
                    Thread.sleep(50)
                }
            }

            val now = LocalDateTime.now().format(dateFormatter)
            configRepository.updateConfig(config.copy(lastSyncTime = now))

            SyncResult(
                success = true,
                downloadedArticles = downloadedArticles,
                downloadedCheckIns = downloadedCheckIns,
                downloadedAcupoints = downloadedAcupoints,
                downloadedConcepts = downloadedConcepts,
                conflicts = conflicts
            )
        } catch (e: OutOfMemoryError) {
            System.gc()
            System.gc()
            e.printStackTrace()
            SyncResult(success = false, errorMessage = "内存不足，请尝试：1. 在设置中只同步文章或只同步穴位/概念，2. 分多次同步")
        } catch (e: Exception) {
            e.printStackTrace()
            SyncResult(success = false, errorMessage = "下载失败: ${e.message}")
        }
    }

    private suspend fun syncFromRemoteFull(config: Config): SyncResult = withContext(Dispatchers.IO) {
        val remoteFilePath = "${config.webdavRemotePath}/daily_read_sync.json"

        when (val result = webDavClient.downloadFile(
            config.webdavServerUrl,
            config.webdavUsername,
            config.webdavPassword,
            remoteFilePath
        )) {
            is WebDavClient.WebDavResult.Success -> {
                try {
                    val jsonMap = gson.fromJson(result.data, Map::class.java) as Map<String, Any?>
                    val compatibleJson = buildCompatibleJson(jsonMap)
                    val remoteData = gson.fromJson(compatibleJson, SyncData::class.java)

                    val localContents = contentRepository.getAllContentsOnce()
                    val localCheckIns = checkInRepository.getAllCheckInRecords()
                    val localAcupoints = acupointRepository.getAllAcupointsOnce()
                    val localConcepts = conceptRepository.getAllConceptsOnce()

                    val conflicts = mutableListOf<SyncConflict>()
                    val articlesToUpdate = mutableListOf<SyncArticle>()
                    val checkInsToUpdate = mutableListOf<SyncCheckIn>()
                    val acupointsToUpdate = mutableListOf<SyncAcupoint>()
                    val conceptsToUpdate = mutableListOf<SyncConcept>()

                    if (config.syncArticlesEnabled) {
                        for (remoteArticle in remoteData.articles) {
                            val localArticle = localContents.find { it.id == remoteArticle.id }
                            if (localArticle == null) {
                                articlesToUpdate.add(remoteArticle)
                            } else {
                                try {
                                    val localTime = LocalDateTime.parse(localArticle.createTime)
                                    val remoteTime = LocalDateTime.parse(remoteArticle.lastModified)
                                    if (remoteTime.isAfter(localTime)) {
                                        articlesToUpdate.add(remoteArticle)
                                    }
                                } catch (e: Exception) {
                                    articlesToUpdate.add(remoteArticle)
                                }
                            }
                        }
                    }

                    for (remoteCheckIn in remoteData.checkIns) {
                        val localCheckIn = localCheckIns.find { it.contentId == remoteCheckIn.contentId && it.date == remoteCheckIn.date }
                        if (localCheckIn == null) {
                            checkInsToUpdate.add(remoteCheckIn)
                        }
                    }

                    if (config.syncAcupointsEnabled) {
                        for (remoteAcupoint in remoteData.acupoints) {
                            val localAcupoint = localAcupoints.find { it.id == remoteAcupoint.id }
                            if (localAcupoint == null) {
                                acupointsToUpdate.add(remoteAcupoint)
                            } else {
                                try {
                                    val localTime = LocalDateTime.parse(localAcupoint.createTime)
                                    val remoteTime = LocalDateTime.parse(remoteAcupoint.lastModified)
                                    if (remoteTime.isAfter(localTime)) {
                                        acupointsToUpdate.add(remoteAcupoint)
                                    }
                                } catch (e: Exception) {
                                    acupointsToUpdate.add(remoteAcupoint)
                                }
                            }
                        }
                    }

                    if (config.syncConceptsEnabled) {
                        for (remoteConcept in remoteData.concepts) {
                            val localConcept = localConcepts.find { it.id == remoteConcept.id }
                            if (localConcept == null) {
                                conceptsToUpdate.add(remoteConcept)
                            } else {
                                try {
                                    val localTime = LocalDateTime.parse(localConcept.createTime)
                                    val remoteTime = LocalDateTime.parse(remoteConcept.lastModified)
                                    if (remoteTime.isAfter(localTime)) {
                                        conceptsToUpdate.add(remoteConcept)
                                    }
                                } catch (e: Exception) {
                                    conceptsToUpdate.add(remoteConcept)
                                }
                            }
                        }
                    }

                    for (article in articlesToUpdate) {
                        val entity = com.dailyread.app.data.local.database.entities.Content(
                            id = article.id, title = article.title, content = article.content, contentHtml = article.contentHtml,
                            chineseChars = article.chineseChars, fontFamily = article.fontFamily, fontSize = article.fontSize,
                            fontColor = article.fontColor, isBold = article.isBold, isReading = article.isReading,
                            isRequired = article.isRequired, requiredDays = article.requiredDays,
                            useIndependentCheckRate = article.useIndependentCheckRate,
                            independentCheckRate = article.independentCheckRate, createTime = article.createTime
                        )
                        val existing = contentRepository.getContentById(article.id)
                        if (existing != null) {
                            contentRepository.updateContent(entity)
                        } else {
                            contentRepository.insertContent(entity)
                        }
                    }

                    for (checkIn in checkInsToUpdate) {
                        val entity = com.dailyread.app.data.local.database.entities.ContentCheckIn(
                            id = checkIn.id, contentId = checkIn.contentId, date = checkIn.date
                        )
                        checkInRepository.insertCheckIn(entity)
                    }

                    for (acupoint in acupointsToUpdate) {
                        val imagePath = if (!acupoint.locationImagePath.isNullOrEmpty()) {
                            val file = File(acupoint.locationImagePath)
                            if (file.exists()) acupoint.locationImagePath else decodeBase64ToImage(acupoint.locationImageBase64, "acupoint")
                        } else {
                            decodeBase64ToImage(acupoint.locationImageBase64, "acupoint")
                        }

                        val entity = Acupoint(
                            id = acupoint.id, acupoint = acupoint.acupoint, meridian = acupoint.meridian,
                            acupointProperty = acupoint.acupointProperty, location = acupoint.location,
                            function = acupoint.function, indications = acupoint.indications, anatomy = acupoint.anatomy,
                            operation = acupoint.operation, contraindications = acupoint.contraindications,
                            locationImagePath = imagePath, locationImageBase64 = acupoint.locationImageBase64,
                            note = acupoint.note, createTime = acupoint.createTime
                        )

                        val existing = acupointRepository.getAcupointById(acupoint.id)
                        if (existing != null) {
                            acupointRepository.update(entity)
                        } else {
                            acupointRepository.insert(entity)
                        }
                    }

                    for (concept in conceptsToUpdate) {
                        val imagePath = if (!concept.imagePath.isNullOrEmpty()) {
                            val file = File(concept.imagePath)
                            if (file.exists()) concept.imagePath else decodeBase64ToImage(concept.imageBase64, "concept")
                        } else {
                            decodeBase64ToImage(concept.imageBase64, "concept")
                        }

                        val entity = Concept(
                            id = concept.id, subject = concept.subject, category = concept.category,
                            subChapter = concept.subChapter, title = concept.title, content = concept.content,
                            imagePath = imagePath, imageBase64 = concept.imageBase64, note = concept.note,
                            isEnabled = concept.isEnabled, createTime = concept.createTime,
                            lastModified = concept.lastModified
                        )

                        val existing = conceptRepository.getConceptById(concept.id)
                        if (existing != null) {
                            conceptRepository.updateConcept(entity)
                        } else {
                            conceptRepository.insertConcept(entity)
                        }
                    }

                    val now = LocalDateTime.now().format(dateFormatter)

                    remoteData.config?.let { remoteConfig ->
                        configRepository.updateConfig(
                            config.copy(
                                lastSyncTime = now, dailyMinutes = remoteConfig.dailyMinutes,
                                targetCheckRate = remoteConfig.targetCheckRate, keepScreenOn = remoteConfig.keepScreenOn,
                                autoSyncWebDav = remoteConfig.autoSyncWebDav, yesterdayLongArticleIds = remoteConfig.yesterdayLongArticleIds
                            )
                        )
                    } ?: run {
                        configRepository.updateConfig(config.copy(lastSyncTime = now))
                    }

                    SyncResult(
                        success = true,
                        downloadedArticles = articlesToUpdate.size,
                        downloadedCheckIns = checkInsToUpdate.size,
                        downloadedAcupoints = acupointsToUpdate.size,
                        downloadedConcepts = conceptsToUpdate.size,
                        conflicts = conflicts
                    )
                } catch (e: Exception) {
                    e.printStackTrace()
                    SyncResult(success = false, errorMessage = "解析远程数据失败: ${e.message}")
                }
            }
            is WebDavClient.WebDavResult.Error -> {
                SyncResult(success = false, errorMessage = result.message)
            }
        }
    }

    private fun buildCompatibleJson(jsonMap: Map<String, Any?>): String {
        val mutableMap = jsonMap.toMutableMap()
        if (mutableMap.containsKey("contents") && !mutableMap.containsKey("articles")) {
            mutableMap["articles"] = mutableMap["contents"]
        }
        mutableMap.putIfAbsent("version", 4)
        mutableMap.putIfAbsent("exportTime", LocalDateTime.now().format(dateFormatter))
        mutableMap.putIfAbsent("articles", emptyList<Any>())
        mutableMap.putIfAbsent("checkIns", emptyList<Any>())
        mutableMap.putIfAbsent("acupoints", emptyList<Any>())
        mutableMap.putIfAbsent("concepts", emptyList<Any>())
        return gson.toJson(mutableMap)
    }

    private suspend fun processDownloadedArticles(articles: List<SyncArticle>): Int {
        for (article in articles) {
            val entity = com.dailyread.app.data.local.database.entities.Content(
                id = article.id, title = article.title, content = article.content, contentHtml = article.contentHtml,
                chineseChars = article.chineseChars, fontFamily = article.fontFamily, fontSize = article.fontSize,
                fontColor = article.fontColor, isBold = article.isBold, isReading = article.isReading,
                isRequired = article.isRequired, requiredDays = article.requiredDays,
                useIndependentCheckRate = article.useIndependentCheckRate,
                independentCheckRate = article.independentCheckRate, createTime = article.createTime
            )
            val existing = contentRepository.getContentById(article.id)
            if (existing != null) {
                contentRepository.updateContent(entity)
            } else {
                contentRepository.insertContent(entity)
            }
        }
        return articles.size
    }

    private suspend fun processDownloadedAcupoints(acupoints: List<SyncAcupoint>): Int {
        for (acupoint in acupoints) {
            val imagePath = if (!acupoint.locationImagePath.isNullOrEmpty()) {
                val file = File(acupoint.locationImagePath)
                if (file.exists()) acupoint.locationImagePath else decodeBase64ToImage(acupoint.locationImageBase64, "acupoint")
            } else {
                decodeBase64ToImage(acupoint.locationImageBase64, "acupoint")
            }

            val entity = Acupoint(
                id = acupoint.id, acupoint = acupoint.acupoint, meridian = acupoint.meridian,
                acupointProperty = acupoint.acupointProperty, location = acupoint.location,
                function = acupoint.function, indications = acupoint.indications, anatomy = acupoint.anatomy,
                operation = acupoint.operation, contraindications = acupoint.contraindications,
                locationImagePath = imagePath, locationImageBase64 = acupoint.locationImageBase64,
                note = acupoint.note, createTime = acupoint.createTime
            )

            val existing = acupointRepository.getAcupointById(acupoint.id)
            if (existing != null) {
                acupointRepository.update(entity)
            } else {
                acupointRepository.insert(entity)
            }
        }
        return acupoints.size
    }

    private suspend fun processDownloadedConcepts(concepts: List<SyncConcept>): Int {
        for (concept in concepts) {
            val imagePath = if (!concept.imagePath.isNullOrEmpty()) {
                val file = File(concept.imagePath)
                if (file.exists()) concept.imagePath else decodeBase64ToImage(concept.imageBase64, "concept")
            } else {
                decodeBase64ToImage(concept.imageBase64, "concept")
            }

            val entity = Concept(
                id = concept.id, subject = concept.subject, category = concept.category,
                subChapter = concept.subChapter, title = concept.title, content = concept.content,
                imagePath = imagePath, imageBase64 = concept.imageBase64, note = concept.note,
                isEnabled = concept.isEnabled, createTime = concept.createTime,
                lastModified = concept.lastModified
            )

            val existing = conceptRepository.getConceptById(concept.id)
            if (existing != null) {
                conceptRepository.updateConcept(entity)
            } else {
                conceptRepository.insertConcept(entity)
            }
        }
        return concepts.size
    }

    private suspend fun processDownloadedCheckins(checkins: List<SyncCheckIn>): Int {
        for (checkIn in checkins) {
            val entity = com.dailyread.app.data.local.database.entities.ContentCheckIn(
                id = checkIn.id, contentId = checkIn.contentId, date = checkIn.date
            )
            checkInRepository.insertCheckIn(entity)
        }
        return checkins.size
    }

    suspend fun syncToRemote(config: Config): SyncResult = withContext(Dispatchers.IO) {
        try {
            val localIndexFile = getLocalIndexFile()
            val localIndex = try { localIndexFile?.let { gson.fromJson(it, SyncIndex::class.java) } } catch (e: Exception) { null }

            val localFiles = localIndex?.files ?: emptyMap()
            var uploadedArticles = 0
            var uploadedAcupoints = 0
            var uploadedConcepts = 0
            var uploadedCheckIns = 0
            val filesToSync = mutableMapOf<String, FileInfo>()
            val nowTime = LocalDateTime.now().format(dateFormatter)

            // 分批处理，每个类型处理完立即释放所有相关内存

            // 1. 处理文章（纯文本，先处理）
            if (config.syncArticlesEnabled) {
                System.gc()
                Thread.sleep(50) // 给GC一点时间
                
                val localContents = contentRepository.getAllContentsOnce()
                val articles = localContents.map {
                    SyncArticle(
                        id = it.id, title = it.title ?: "", content = it.content ?: "", contentHtml = null, // 不处理html减少内存
                        chineseChars = it.chineseChars, fontFamily = it.fontFamily ?: "default", fontSize = it.fontSize,
                        fontColor = it.fontColor ?: "#000000", isBold = it.isBold, isReading = it.isReading,
                        isRequired = it.isRequired, requiredDays = it.requiredDays ?: "",
                        useIndependentCheckRate = it.useIndependentCheckRate,
                        independentCheckRate = it.independentCheckRate, createTime = it.createTime,
                        lastModified = nowTime
                    )
                }
                val articlesJson = gson.toJson(articles)
                val articlesHash = calculateHash(articlesJson)
                
                val localArticlesInfo = localFiles["articles"]
                if (localArticlesInfo == null || localArticlesInfo.hash != articlesHash) {
                    uploadFileToRemote(config, ARTICLES_FILE, articlesJson)
                    uploadedArticles = articles.size
                }
                
                filesToSync["articles"] = FileInfo(ARTICLES_FILE, nowTime, articles.size, articlesHash)
                
                // 立即释放内存
                System.gc()
                Thread.sleep(100)
            } else if ("articles" in localFiles) {
                filesToSync["articles"] = localFiles["articles"]!!
            }

            // 2. 处理签到数据
            val localCheckIns = checkInRepository.getAllCheckInRecords()
            val checkIns = localCheckIns.map {
                SyncCheckIn(
                    id = it.id, contentId = it.contentId, date = it.date,
                    lastModified = nowTime
                )
            }
            val checkinsJson = gson.toJson(checkIns)
            val checkinsHash = calculateHash(checkinsJson)
            
            val localCheckinsInfo = localFiles["checkins"]
            if (localCheckinsInfo == null || localCheckinsInfo.hash != checkinsHash) {
                uploadFileToRemote(config, CHECKINS_FILE, checkinsJson)
                uploadedCheckIns = checkIns.size
            }
            
            filesToSync["checkins"] = FileInfo(CHECKINS_FILE, nowTime, checkIns.size, checkinsHash)
            
            // 释放内存
            System.gc()
            Thread.sleep(50)

            // 3. 处理穴位 - 逐个处理图片避免内存溢出
            if (config.syncAcupointsEnabled) {
                System.gc()
                Thread.sleep(100)
                
                val localAcupoints = acupointRepository.getAllAcupointsOnce()
                // 分批处理穴位，每批10个
                val acupoints = mutableListOf<SyncAcupoint>()
                
                for (i in localAcupoints.indices step 10) {
                    val batch = localAcupoints.subList(i, minOf(i + 10, localAcupoints.size))
                    batch.forEach { acupoint ->
                        acupoints.add(
                            SyncAcupoint(
                                id = acupoint.id, acupoint = acupoint.acupoint ?: "", meridian = acupoint.meridian ?: "",
                                acupointProperty = acupoint.acupointProperty ?: "", location = acupoint.location ?: "",
                                function = acupoint.function ?: "", indications = acupoint.indications ?: "", anatomy = acupoint.anatomy ?: "",
                                operation = acupoint.operation ?: "", contraindications = acupoint.contraindications ?: "",
                                locationImagePath = acupoint.locationImagePath, 
                                locationImageBase64 = encodeImageToBase64(acupoint.locationImagePath),
                                note = acupoint.note ?: "", createTime = acupoint.createTime,
                                lastModified = nowTime
                            )
                        )
                    }
                    System.gc() // 每批后释放内存
                    Thread.sleep(20)
                }
                
                val acupointsJson = gson.toJson(acupoints)
                val acupointsHash = calculateHash(acupointsJson)
                
                val localAcupointsInfo = localFiles["acupoints"]
                if (localAcupointsInfo == null || localAcupointsInfo.hash != acupointsHash) {
                    uploadFileToRemote(config, ACUPOINTS_FILE, acupointsJson)
                    uploadedAcupoints = acupoints.size
                }
                
                filesToSync["acupoints"] = FileInfo(ACUPOINTS_FILE, nowTime, acupoints.size, acupointsHash)
                
                System.gc()
                Thread.sleep(100)
            } else if ("acupoints" in localFiles) {
                filesToSync["acupoints"] = localFiles["acupoints"]!!
            }

            // 4. 处理概念 - 同样分批处理
            if (config.syncConceptsEnabled) {
                System.gc()
                Thread.sleep(100)
                
                val localConcepts = conceptRepository.getAllConceptsOnce()
                val concepts = mutableListOf<SyncConcept>()
                
                for (i in localConcepts.indices step 10) {
                    val batch = localConcepts.subList(i, minOf(i + 10, localConcepts.size))
                    batch.forEach { concept ->
                        concepts.add(
                            SyncConcept(
                                id = concept.id, subject = concept.subject ?: "", category = concept.category ?: "",
                                subChapter = concept.subChapter ?: "", title = concept.title ?: "", content = concept.content ?: "",
                                imagePath = concept.imagePath, 
                                imageBase64 = encodeImageToBase64(concept.imagePath),
                                note = concept.note ?: "", isEnabled = concept.isEnabled, createTime = concept.createTime,
                                lastModified = nowTime
                            )
                        )
                    }
                    System.gc()
                    Thread.sleep(20)
                }
                
                val conceptsJson = gson.toJson(concepts)
                val conceptsHash = calculateHash(conceptsJson)
                
                val localConceptsInfo = localFiles["concepts"]
                if (localConceptsInfo == null || localConceptsInfo.hash != conceptsHash) {
                    uploadFileToRemote(config, CONCEPTS_FILE, conceptsJson)
                    uploadedConcepts = concepts.size
                }
                
                filesToSync["concepts"] = FileInfo(CONCEPTS_FILE, nowTime, concepts.size, conceptsHash)
                
                System.gc()
                Thread.sleep(100)
            } else if ("concepts" in localFiles) {
                filesToSync["concepts"] = localFiles["concepts"]!!
            }

            // 5. 上传索引
            val newIndex = SyncIndex(
                version = CURRENT_VERSION,
                syncTime = nowTime,
                files = filesToSync
            )
            uploadFileToRemote(config, SYNC_INDEX_FILE, gson.toJson(newIndex))
            saveLocalIndex(newIndex)

            // 6. 跳过旧版兼容格式以避免内存问题
            // if (localIndex == null) { ... } - 不再处理兼容格式

            configRepository.updateConfig(config.copy(lastSyncTime = nowTime))

            SyncResult(
                success = true,
                uploadedArticles = uploadedArticles,
                uploadedCheckIns = uploadedCheckIns,
                uploadedAcupoints = uploadedAcupoints,
                uploadedConcepts = uploadedConcepts
            )
        } catch (e: OutOfMemoryError) {
            System.gc()
            System.gc() // 双重调用确保回收
            e.printStackTrace()
            SyncResult(success = false, errorMessage = "内存不足，请尝试：1. 在设置中只同步文章或只同步穴位/概念，2. 删除一些大图片")
        } catch (e: Exception) {
            e.printStackTrace()
            SyncResult(success = false, errorMessage = "上传数据失败: ${e.message}")
        }
    }

    suspend fun resolveConflict(config: Config, conflict: SyncConflict, useLocal: Boolean): SyncResult = withContext(Dispatchers.IO) {
        try {
            when (conflict.type) {
                ConflictType.ARTICLE_CONTENT -> {
                    if (useLocal) {
                        val localArticle = gson.fromJson(conflict.localData, com.dailyread.app.data.local.database.entities.Content::class.java)
                        contentRepository.updateContent(localArticle)
                    } else {
                        val remoteArticle = gson.fromJson(conflict.remoteData, SyncArticle::class.java)
                        val entity = com.dailyread.app.data.local.database.entities.Content(
                            id = remoteArticle.id, title = remoteArticle.title, content = remoteArticle.content,
                            contentHtml = remoteArticle.contentHtml, chineseChars = remoteArticle.chineseChars,
                            fontFamily = remoteArticle.fontFamily, fontSize = remoteArticle.fontSize,
                            fontColor = remoteArticle.fontColor, isBold = remoteArticle.isBold,
                            isReading = remoteArticle.isReading, isRequired = remoteArticle.isRequired,
                            requiredDays = remoteArticle.requiredDays,
                            useIndependentCheckRate = remoteArticle.useIndependentCheckRate,
                            independentCheckRate = remoteArticle.independentCheckRate,
                            createTime = remoteArticle.createTime
                        )
                        contentRepository.updateContent(entity)
                    }
                }
                ConflictType.ACUPOINT_DATA -> {
                    if (useLocal) {
                        val localAcupoint = gson.fromJson(conflict.localData, Acupoint::class.java)
                        acupointRepository.update(localAcupoint)
                    } else {
                        val remoteAcupoint = gson.fromJson(conflict.remoteData, SyncAcupoint::class.java)
                        val imagePath = if (!remoteAcupoint.locationImagePath.isNullOrEmpty()) {
                            val file = File(remoteAcupoint.locationImagePath)
                            if (file.exists()) remoteAcupoint.locationImagePath else decodeBase64ToImage(remoteAcupoint.locationImageBase64, "acupoint")
                        } else {
                            decodeBase64ToImage(remoteAcupoint.locationImageBase64, "acupoint")
                        }
                        val entity = Acupoint(
                            id = remoteAcupoint.id, acupoint = remoteAcupoint.acupoint, meridian = remoteAcupoint.meridian,
                            acupointProperty = remoteAcupoint.acupointProperty, location = remoteAcupoint.location,
                            function = remoteAcupoint.function, indications = remoteAcupoint.indications,
                            anatomy = remoteAcupoint.anatomy, operation = remoteAcupoint.operation,
                            contraindications = remoteAcupoint.contraindications, locationImagePath = imagePath,
                            locationImageBase64 = remoteAcupoint.locationImageBase64, note = remoteAcupoint.note,
                            createTime = remoteAcupoint.createTime
                        )
                        acupointRepository.update(entity)
                    }
                }
                ConflictType.CONCEPT_DATA -> {
                    if (useLocal) {
                        val localConcept = gson.fromJson(conflict.localData, Concept::class.java)
                        conceptRepository.updateConcept(localConcept)
                    } else {
                        val remoteConcept = gson.fromJson(conflict.remoteData, SyncConcept::class.java)
                        val imagePath = if (!remoteConcept.imagePath.isNullOrEmpty()) {
                            val file = File(remoteConcept.imagePath)
                            if (file.exists()) remoteConcept.imagePath else decodeBase64ToImage(remoteConcept.imageBase64, "concept")
                        } else {
                            decodeBase64ToImage(remoteConcept.imageBase64, "concept")
                        }
                        val entity = Concept(
                            id = remoteConcept.id, subject = remoteConcept.subject, category = remoteConcept.category,
                            subChapter = remoteConcept.subChapter, title = remoteConcept.title, content = remoteConcept.content,
                            imagePath = imagePath, imageBase64 = remoteConcept.imageBase64, note = remoteConcept.note,
                            isEnabled = remoteConcept.isEnabled, createTime = remoteConcept.createTime,
                            lastModified = remoteConcept.lastModified
                        )
                        conceptRepository.updateConcept(entity)
                    }
                }
                else -> {}
            }
            SyncResult(success = true)
        } catch (e: Exception) {
            e.printStackTrace()
            SyncResult(success = false, errorMessage = "解决冲突失败: ${e.message}")
        }
    }
}
