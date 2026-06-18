package com.dailyread.app.ui.screens.acupoint

import android.content.Context
import android.util.Base64
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.dailyread.app.data.local.database.entities.Acupoint
import com.dailyread.app.data.repository.AcupointRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import java.io.File
import java.time.LocalDateTime
import java.time.format.DateTimeFormatter
import javax.inject.Inject

data class AcupointUiState(
    val randomAcupoint: Acupoint? = null,
    val isLoading: Boolean = false
)

data class AcupointManageUiState(
    val acupoints: List<Acupoint> = emptyList(),
    val selectedAcupoints: Set<Long> = emptySet(),
    val meridians: List<String> = emptyList(),
    val searchQuery: String = "",
    val selectedMeridian: String? = null,
    val isLoading: Boolean = false
)

data class AcupointEditUiState(
    val acupoint: Acupoint? = null,
    val isLoading: Boolean = false,
    val navigateBack: Boolean = false
)

@HiltViewModel
class AcupointViewModel @Inject constructor(
    private val acupointRepository: AcupointRepository,
    @ApplicationContext private val context: Context
) : ViewModel() {
    
    private fun encodeImageToBase64(imagePath: String?): String? {
        return imagePath?.let { path ->
            try {
                val file = File(path)
                if (file.exists()) {
                    val bytes = file.readBytes()
                    Base64.encodeToString(bytes, Base64.NO_WRAP)
                } else null
            } catch (e: Exception) {
                e.printStackTrace()
                null
            }
        }
    }
    private val _uiState = MutableStateFlow(AcupointUiState())
    val uiState: StateFlow<AcupointUiState> = _uiState.asStateFlow()
    
    private val _manageUiState = MutableStateFlow(AcupointManageUiState())
    val manageUiState: StateFlow<AcupointManageUiState> = _manageUiState.asStateFlow()
    
    private val _editUiState = MutableStateFlow(AcupointEditUiState())
    val editUiState: StateFlow<AcupointEditUiState> = _editUiState.asStateFlow()

    fun loadRandomAcupoint() {
        viewModelScope.launch {
            try {
                _uiState.value = _uiState.value.copy(isLoading = true)
                val acupoint = acupointRepository.getRandomAcupoint()
                _uiState.value = _uiState.value.copy(randomAcupoint = acupoint, isLoading = false)
            } catch (e: Exception) {
                e.printStackTrace()
                _uiState.value = _uiState.value.copy(isLoading = false)
            }
        }
    }
    
    fun loadAllAcupoints() {
        viewModelScope.launch {
            try {
                _manageUiState.value = _manageUiState.value.copy(isLoading = true)
                acupointRepository.getAllAcupoints().collect { acupoints ->
                    val meridians = try {
                        acupointRepository.getDistinctMeridians()
                    } catch (e: Exception) {
                        e.printStackTrace()
                        emptyList()
                    }
                    _manageUiState.value = _manageUiState.value.copy(
                        acupoints = acupoints,
                        meridians = meridians,
                        isLoading = false
                    )
                }
            } catch (e: Exception) {
                e.printStackTrace()
                _manageUiState.value = _manageUiState.value.copy(isLoading = false)
            }
        }
    }
    
    fun toggleSelectAcupoint(id: Long) {
        val currentSelected = _manageUiState.value.selectedAcupoints
        val newSelected = if (currentSelected.contains(id)) {
            currentSelected - id
        } else {
            currentSelected + id
        }
        _manageUiState.value = _manageUiState.value.copy(selectedAcupoints = newSelected)
    }
    
    fun selectAll() {
        val allIds = _manageUiState.value.acupoints.map { it.id }.toSet()
        _manageUiState.value = _manageUiState.value.copy(selectedAcupoints = allIds)
    }
    
    fun clearSelection() {
        _manageUiState.value = _manageUiState.value.copy(selectedAcupoints = emptySet())
    }
    
    fun deleteSelected() {
        viewModelScope.launch {
            val selectedIds = _manageUiState.value.selectedAcupoints
            val selectedAcupoints = _manageUiState.value.acupoints.filter { it.id in selectedIds }
            acupointRepository.deleteAcupoints(selectedAcupoints)
            clearSelection()
        }
    }
    
    fun searchAcupoints(query: String) {
        viewModelScope.launch {
            _manageUiState.value = _manageUiState.value.copy(searchQuery = query, isLoading = true)
            if (query.isBlank()) {
                acupointRepository.getAllAcupoints().collect { acupoints ->
                    _manageUiState.value = _manageUiState.value.copy(acupoints = acupoints, isLoading = false)
                }
            } else {
                val results = acupointRepository.searchByAcupoint(query)
                _manageUiState.value = _manageUiState.value.copy(acupoints = results, isLoading = false)
            }
        }
    }
    
    fun filterByMeridian(meridian: String?) {
        viewModelScope.launch {
            _manageUiState.value = _manageUiState.value.copy(selectedMeridian = meridian, isLoading = true)
            if (meridian.isNullOrBlank()) {
                acupointRepository.getAllAcupoints().collect { acupoints ->
                    _manageUiState.value = _manageUiState.value.copy(acupoints = acupoints, isLoading = false)
                }
            } else {
                val results = acupointRepository.filterByMeridian(meridian)
                _manageUiState.value = _manageUiState.value.copy(acupoints = results, isLoading = false)
            }
        }
    }
    
    fun loadAcupointById(id: Long) {
        viewModelScope.launch {
            _editUiState.value = _editUiState.value.copy(isLoading = true)
            val acupoint = acupointRepository.getAcupointById(id)
            _editUiState.value = _editUiState.value.copy(
                acupoint = acupoint,
                isLoading = false
            )
        }
    }
    
    fun saveAcupoint(
        acupoint: String,
        meridian: String,
        acupointProperty: String,
        location: String,
        function: String,
        indications: String,
        anatomy: String,
        operation: String,
        contraindications: String,
        locationImagePath: String?,
        note: String,
        id: Long? = null
    ) {
        viewModelScope.launch {
            _editUiState.value = _editUiState.value.copy(isLoading = true)
            val now = LocalDateTime.now().format(DateTimeFormatter.ISO_LOCAL_DATE_TIME)
            val locationImageBase64 = encodeImageToBase64(locationImagePath)
            val acupointEntity = if (id != null) {
                val existing = acupointRepository.getAcupointById(id)
                existing?.copy(
                    acupoint = acupoint,
                    meridian = meridian,
                    acupointProperty = acupointProperty,
                    location = location,
                    function = function,
                    indications = indications,
                    anatomy = anatomy,
                    operation = operation,
                    contraindications = contraindications,
                    locationImagePath = locationImagePath,
                    locationImageBase64 = locationImageBase64,
                    note = note
                ) ?: Acupoint(
                    id = id,
                    acupoint = acupoint,
                    meridian = meridian,
                    acupointProperty = acupointProperty,
                    location = location,
                    function = function,
                    indications = indications,
                    anatomy = anatomy,
                    operation = operation,
                    contraindications = contraindications,
                    locationImagePath = locationImagePath,
                    locationImageBase64 = locationImageBase64,
                    note = note,
                    createTime = now
                )
            } else {
                Acupoint(
                    acupoint = acupoint,
                    meridian = meridian,
                    acupointProperty = acupointProperty,
                    location = location,
                    function = function,
                    indications = indications,
                    anatomy = anatomy,
                    operation = operation,
                    contraindications = contraindications,
                    locationImagePath = locationImagePath,
                    locationImageBase64 = locationImageBase64,
                    note = note,
                    createTime = now
                )
            }
            
            if (id != null) {
                acupointRepository.update(acupointEntity)
            } else {
                acupointRepository.insert(acupointEntity)
            }
            
            _editUiState.value = _editUiState.value.copy(
                isLoading = false,
                navigateBack = true
            )
        }
    }
    
    fun clearEditState() {
        _editUiState.value = AcupointEditUiState()
    }
}