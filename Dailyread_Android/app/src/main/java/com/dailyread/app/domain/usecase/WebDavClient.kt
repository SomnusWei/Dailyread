package com.dailyread.app.domain.usecase

import android.content.Context
import android.util.Base64
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import okhttp3.*
import okhttp3.Credentials
import okhttp3.MediaType.Companion.toMediaTypeOrNull
import okhttp3.RequestBody.Companion.toRequestBody
import java.io.IOException
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class WebDavClient @Inject constructor(
    @ApplicationContext private val context: Context
) {
    private val client = OkHttpClient.Builder()
        .connectTimeout(30, java.util.concurrent.TimeUnit.SECONDS)
        .readTimeout(30, java.util.concurrent.TimeUnit.SECONDS)
        .writeTimeout(30, java.util.concurrent.TimeUnit.SECONDS)
        .followRedirects(true)
        .followSslRedirects(true)
        .build()

    sealed class WebDavResult<out T> {
        data class Success<T>(val data: T) : WebDavResult<T>()
        data class Error(val message: String, val code: Int? = null) : WebDavResult<Nothing>()
    }

    suspend fun testConnection(
        serverUrl: String,
        username: String,
        password: String,
        remotePath: String
    ): WebDavResult<Boolean> = withContext(Dispatchers.IO) {
        try {
            val baseUrl = serverUrl.trimEnd('/')
            val cleanPath = if (remotePath.startsWith('/')) remotePath else "/$remotePath"
            val fullUrl = "$baseUrl$cleanPath"
            
            val propfindBody = """<?xml version="1.0" encoding="utf-8"?>
                <propfind xmlns="DAV:">
                    <prop>
                        <resourcetype/>
                    </prop>
                </propfind>""".trimIndent()
            
            val mediaType = "application/xml".toMediaTypeOrNull()
            val requestBody = propfindBody.toRequestBody(mediaType)
            val credential = Credentials.basic(username, password)
            
            val request = Request.Builder()
                .url(fullUrl)
                .header("Authorization", credential)
                .header("Depth", "0")
                .method("PROPFIND", requestBody)
                .build()

            val response = client.newCall(request).execute()

            if (response.isSuccessful || response.code == 207) {
                WebDavResult.Success(true)
            } else if (response.code == 404) {
                tryCreateDirectory(baseUrl, remotePath, username, password)
            } else {
                WebDavResult.Error("连接失败: ${response.message}", response.code)
            }
        } catch (e: Exception) {
            WebDavResult.Error("连接错误: ${e.message}")
        }
    }

    private suspend fun tryCreateDirectory(
        baseUrl: String,
        remotePath: String,
        username: String,
        password: String
    ): WebDavResult<Boolean> = withContext(Dispatchers.IO) {
        try {
            val cleanPath = if (remotePath.startsWith('/')) remotePath else "/$remotePath"
            val fullUrl = "$baseUrl$cleanPath"
            val credential = Credentials.basic(username, password)
            
            val request = Request.Builder()
                .url(fullUrl)
                .header("Authorization", credential)
                .method("MKCOL", null)
                .build()

            val response = client.newCall(request).execute()

            if (response.isSuccessful || response.code == 201 || response.code == 405) {
                WebDavResult.Success(true)
            } else {
                WebDavResult.Error("创建目录失败: ${response.message}", response.code)
            }
        } catch (e: Exception) {
            WebDavResult.Error("创建目录错误: ${e.message}")
        }
    }

    suspend fun createDirectory(
        serverUrl: String,
        username: String,
        password: String,
        remotePath: String
    ): WebDavResult<Boolean> = withContext(Dispatchers.IO) {
        try {
            val baseUrl = serverUrl.trimEnd('/')
            val cleanPath = if (remotePath.startsWith('/')) remotePath else "/$remotePath"
            val fullUrl = "$baseUrl$cleanPath"
            val credential = Credentials.basic(username, password)
            
            val request = Request.Builder()
                .url(fullUrl)
                .header("Authorization", credential)
                .method("MKCOL", null)
                .build()

            val response = client.newCall(request).execute()

            if (response.isSuccessful || response.code == 201 || response.code == 405) {
                WebDavResult.Success(true)
            } else {
                WebDavResult.Error("创建目录失败: ${response.message}", response.code)
            }
        } catch (e: Exception) {
            WebDavResult.Error("创建目录错误: ${e.message}")
        }
    }

    suspend fun uploadFile(
        serverUrl: String,
        username: String,
        password: String,
        remotePath: String,
        content: String
    ): WebDavResult<Boolean> = withContext(Dispatchers.IO) {
        try {
            val baseUrl = serverUrl.trimEnd('/')
            val cleanPath = if (remotePath.startsWith('/')) remotePath else "/$remotePath"
            val fullUrl = "$baseUrl$cleanPath"
            val mediaType = "application/json".toMediaTypeOrNull()
            val requestBody = content.toRequestBody(mediaType)
            val credential = Credentials.basic(username, password)
            
            val request = Request.Builder()
                .url(fullUrl)
                .header("Authorization", credential)
                .method("PUT", requestBody)
                .build()

            val response = client.newCall(request).execute()

            if (response.isSuccessful || response.code == 201 || response.code == 204) {
                WebDavResult.Success(true)
            } else {
                WebDavResult.Error("上传失败: ${response.message}", response.code)
            }
        } catch (e: Exception) {
            WebDavResult.Error("上传错误: ${e.message}")
        }
    }

    suspend fun downloadFile(
        serverUrl: String,
        username: String,
        password: String,
        remotePath: String
    ): WebDavResult<String> = withContext(Dispatchers.IO) {
        try {
            val baseUrl = serverUrl.trimEnd('/')
            val cleanPath = if (remotePath.startsWith('/')) remotePath else "/$remotePath"
            val fullUrl = "$baseUrl$cleanPath"
            val credential = Credentials.basic(username, password)
            
            val request = Request.Builder()
                .url(fullUrl)
                .header("Authorization", credential)
                .method("GET", null)
                .build()

            val response = client.newCall(request).execute()

            if (response.isSuccessful) {
                val body = response.body?.string() ?: ""
                WebDavResult.Success(body)
            } else if (response.code == 404) {
                WebDavResult.Success("")
            } else {
                WebDavResult.Error("下载失败: ${response.message}", response.code)
            }
        } catch (e: Exception) {
            WebDavResult.Error("下载错误: ${e.message}")
        }
    }

    suspend fun getFileLastModified(
        serverUrl: String,
        username: String,
        password: String,
        remotePath: String
    ): WebDavResult<String?> = withContext(Dispatchers.IO) {
        try {
            val baseUrl = serverUrl.trimEnd('/')
            val cleanPath = if (remotePath.startsWith('/')) remotePath else "/$remotePath"
            val fullUrl = "$baseUrl$cleanPath"
            val propfindBody = """<?xml version="1.0" encoding="utf-8"?>
                <propfind xmlns="DAV:">
                    <prop>
                        <getlastmodified/>
                    </prop>
                </propfind>""".trimIndent()

            val mediaType = "application/xml".toMediaTypeOrNull()
            val requestBody = propfindBody.toRequestBody(mediaType)
            val credential = Credentials.basic(username, password)
            
            val request = Request.Builder()
                .url(fullUrl)
                .header("Authorization", credential)
                .header("Depth", "0")
                .method("PROPFIND", requestBody)
                .build()

            val response = client.newCall(request).execute()

            if (response.isSuccessful || response.code == 207) {
                val body = response.body?.string() ?: ""
                val lastModified = parseLastModified(body)
                WebDavResult.Success(lastModified)
            } else if (response.code == 404) {
                WebDavResult.Success(null)
            } else {
                WebDavResult.Error("获取文件信息失败: ${response.message}", response.code)
            }
        } catch (e: Exception) {
            WebDavResult.Error("获取文件信息错误: ${e.message}")
        }
    }

    private fun parseLastModified(xml: String): String? {
        val regex = Regex("<D:getlastmodified>([^<]+)</D:getlastmodified>", RegexOption.IGNORE_CASE)
        val match = regex.find(xml)
        return match?.groupValues?.getOrNull(1)
    }
}
