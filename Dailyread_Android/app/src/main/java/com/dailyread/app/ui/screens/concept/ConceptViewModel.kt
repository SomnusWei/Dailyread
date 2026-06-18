package com.dailyread.app.ui.screens.concept

import android.content.Context
import android.util.Base64
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.dailyread.app.data.local.database.entities.Concept
import com.dailyread.app.data.repository.ConceptRepository
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

data class ConceptUiState(
    val randomConcept: Concept? = null,
    val isLoading: Boolean = false
)

data class ConceptManageUiState(
    val allConcepts: List<Concept> = emptyList(),
    val concepts: List<Concept> = emptyList(),
    val selectedConcepts: Set<Long> = emptySet(),
    val subjects: List<String> = emptyList(),
    val categories: List<String> = emptyList(),
    val subChapters: List<String> = emptyList(),
    val searchQuery: String = "",
    val selectedCategory: String? = null,
    val selectedSubject: String? = null,
    val selectedSubChapter: String? = null,
    val isLoading: Boolean = false
)

data class ConceptEditUiState(
    val concept: Concept? = null,
    val isLoading: Boolean = false,
    val navigateBack: Boolean = false
)

@HiltViewModel
class ConceptViewModel @Inject constructor(
    private val conceptRepository: ConceptRepository,
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

    private val _uiState = MutableStateFlow(ConceptUiState())
    val uiState: StateFlow<ConceptUiState> = _uiState.asStateFlow()

    private val _manageUiState = MutableStateFlow(ConceptManageUiState())
    val manageUiState: StateFlow<ConceptManageUiState> = _manageUiState.asStateFlow()

    private val _editUiState = MutableStateFlow(ConceptEditUiState())
    val editUiState: StateFlow<ConceptEditUiState> = _editUiState.asStateFlow()

    fun loadRandomConcept() {
        viewModelScope.launch {
            try {
                _uiState.value = _uiState.value.copy(isLoading = true)
                val concept = conceptRepository.getRandomConcept()
                _uiState.value = _uiState.value.copy(randomConcept = concept, isLoading = false)
            } catch (e: Exception) {
                e.printStackTrace()
                _uiState.value = _uiState.value.copy(isLoading = false)
            }
        }
    }

    fun loadAllConcepts() {
        viewModelScope.launch {
            try {
                _manageUiState.value = _manageUiState.value.copy(isLoading = true)
                conceptRepository.getAllConcepts().collect { allConcepts ->
                    val subjects = allConcepts.map { it.subject }.distinct().sorted()
                    val categories = allConcepts.map { it.category }.distinct().sorted()
                    
                    // 如果有筛选条件，应用筛选
                    val filteredConcepts = if (_manageUiState.value.selectedCategory != null || 
                        _manageUiState.value.selectedSubject != null ||
                        _manageUiState.value.selectedSubChapter != null) {
                        applyFiltersToList(allConcepts,
                            _manageUiState.value.selectedCategory,
                            _manageUiState.value.selectedSubject,
                            _manageUiState.value.selectedSubChapter)
                    } else {
                        allConcepts
                    }
                    
                    _manageUiState.value = _manageUiState.value.copy(
                        allConcepts = allConcepts,
                        concepts = filteredConcepts,
                        subjects = subjects,
                        categories = categories,
                        isLoading = false
                    )
                }
            } catch (e: Exception) {
                e.printStackTrace()
                _manageUiState.value = _manageUiState.value.copy(isLoading = false)
            }
        }
    }
    
    private fun applyFiltersToList(
        allConcepts: List<Concept>,
        category: String?,
        subject: String?,
        subChapter: String?
    ): List<Concept> {
        return when {
            category == null -> allConcepts
            subject == null -> allConcepts.filter { it.category == category }
            subChapter == null -> allConcepts.filter { it.category == category && it.subject == subject }
            else -> allConcepts.filter { it.category == category && it.subject == subject && it.subChapter == subChapter }
        }
    }

    fun clearFilters() {
        viewModelScope.launch {
            val allConcepts = _manageUiState.value.allConcepts.takeIf { it.isNotEmpty() } 
                ?: conceptRepository.getAllConceptsOnce()
            val subjects = allConcepts.map { it.subject }.distinct().sorted()
            val categories = allConcepts.map { it.category }.distinct().sorted()
            
            _manageUiState.value = _manageUiState.value.copy(
                allConcepts = allConcepts,
                concepts = allConcepts,
                subjects = subjects,
                categories = categories,
                selectedCategory = null,
                selectedSubject = null,
                selectedSubChapter = null,
                subChapters = emptyList(),
                isLoading = false
            )
        }
    }
    
    fun applyFilters(
        category: String?,
        subject: String?,
        subChapter: String?
    ) {
        viewModelScope.launch {
            _manageUiState.value = _manageUiState.value.copy(isLoading = true)
            
            val allConcepts = _manageUiState.value.allConcepts.takeIf { it.isNotEmpty() } 
                ?: conceptRepository.getAllConceptsOnce()
                
            val filteredConcepts = applyFiltersToList(allConcepts, category, subject, subChapter)
            
            val newSubjects: List<String>
            val newCategories: List<String>
            val newSubChapters: List<String>
            
            if (category == null) {
                // 没有选择分类，显示全部
                newSubjects = allConcepts.map { it.subject }.distinct().sorted()
                newCategories = allConcepts.map { it.category }.distinct().sorted()
                newSubChapters = emptyList()
            } else if (subject == null) {
                // 只选择了分类
                newSubjects = allConcepts.filter { it.category == category }
                    .map { it.subject }.distinct().sorted()
                newCategories = emptyList()
                newSubChapters = emptyList()
            } else if (subChapter == null) {
                // 选择了分类和科目
                newSubjects = emptyList()
                newCategories = emptyList()
                newSubChapters = allConcepts.filter { it.category == category && it.subject == subject }
                    .map { it.subChapter }.distinct().sorted()
            } else {
                // 选择了全部三级
                newSubjects = emptyList()
                newCategories = emptyList()
                newSubChapters = emptyList()
            }
            
            _manageUiState.value = _manageUiState.value.copy(
                allConcepts = allConcepts,
                concepts = filteredConcepts,
                subjects = newSubjects,
                categories = newCategories,
                subChapters = newSubChapters,
                selectedCategory = category,
                selectedSubject = subject,
                selectedSubChapter = subChapter,
                isLoading = false
            )
        }
    }

    fun toggleSelectConcept(id: Long) {
        val currentSelected = _manageUiState.value.selectedConcepts
        val newSelected = if (currentSelected.contains(id)) {
            currentSelected - id
        } else {
            currentSelected + id
        }
        _manageUiState.value = _manageUiState.value.copy(selectedConcepts = newSelected)
    }

    fun selectAll() {
        val allIds = _manageUiState.value.concepts.map { it.id }.toSet()
        _manageUiState.value = _manageUiState.value.copy(selectedConcepts = allIds)
    }

    fun clearSelection() {
        _manageUiState.value = _manageUiState.value.copy(selectedConcepts = emptySet())
    }

    fun deleteSelected() {
        viewModelScope.launch {
            val selectedIds = _manageUiState.value.selectedConcepts.toList()
            conceptRepository.deleteConcepts(selectedIds)
            clearSelection()
        }
    }

    fun searchConcepts(query: String) {
        viewModelScope.launch {
            _manageUiState.value = _manageUiState.value.copy(searchQuery = query, isLoading = true)
            if (query.isBlank()) {
                conceptRepository.getAllConcepts().collect { concepts ->
                    _manageUiState.value = _manageUiState.value.copy(concepts = concepts, isLoading = false)
                }
            } else {
                val results = conceptRepository.searchByTitle(query)
                _manageUiState.value = _manageUiState.value.copy(concepts = results, isLoading = false)
            }
        }
    }

    fun filterBySubject(subject: String?) {
        viewModelScope.launch {
            _manageUiState.value = _manageUiState.value.copy(selectedSubject = subject, isLoading = true)
            if (subject.isNullOrBlank()) {
                conceptRepository.getAllConcepts().collect { concepts ->
                    _manageUiState.value = _manageUiState.value.copy(concepts = concepts, isLoading = false)
                }
            } else {
                val results = conceptRepository.filterBySubject(subject)
                _manageUiState.value = _manageUiState.value.copy(concepts = results, isLoading = false)
            }
        }
    }

    fun filterByCategory(category: String?) {
        viewModelScope.launch {
            _manageUiState.value = _manageUiState.value.copy(selectedCategory = category, isLoading = true)
            if (category.isNullOrBlank()) {
                conceptRepository.getAllConcepts().collect { concepts ->
                    _manageUiState.value = _manageUiState.value.copy(concepts = concepts, isLoading = false)
                }
            } else {
                val results = conceptRepository.filterByCategory(category)
                _manageUiState.value = _manageUiState.value.copy(concepts = results, isLoading = false)
            }
        }
    }

    fun loadConceptById(id: Long) {
        viewModelScope.launch {
            _editUiState.value = _editUiState.value.copy(isLoading = true)
            val concept = conceptRepository.getConceptById(id)
            _editUiState.value = _editUiState.value.copy(
                concept = concept,
                isLoading = false
            )
        }
    }

    fun saveConcept(
        subject: String,
        category: String,
        subChapter: String,
        title: String,
        content: String,
        imagePath: String?,
        note: String,
        isEnabled: Boolean = true,
        id: Long? = null
    ) {
        viewModelScope.launch {
            _editUiState.value = _editUiState.value.copy(isLoading = true)
            val now = LocalDateTime.now().format(DateTimeFormatter.ISO_LOCAL_DATE_TIME)
            val imageBase64 = encodeImageToBase64(imagePath)
            val conceptEntity = if (id != null) {
                val existing = conceptRepository.getConceptById(id)
                existing?.copy(
                    subject = subject,
                    category = category,
                    subChapter = subChapter,
                    title = title,
                    content = content,
                    imagePath = imagePath,
                    imageBase64 = imageBase64,
                    note = note,
                    isEnabled = isEnabled,
                    lastModified = now
                ) ?: Concept(
                    id = id,
                    subject = subject,
                    category = category,
                    subChapter = subChapter,
                    title = title,
                    content = content,
                    imagePath = imagePath,
                    imageBase64 = imageBase64,
                    note = note,
                    isEnabled = isEnabled,
                    createTime = now,
                    lastModified = now
                )
            } else {
                Concept(
                    subject = subject,
                    category = category,
                    subChapter = subChapter,
                    title = title,
                    content = content,
                    imagePath = imagePath,
                    imageBase64 = imageBase64,
                    note = note,
                    isEnabled = isEnabled,
                    createTime = now,
                    lastModified = now
                )
            }

            if (id != null) {
                conceptRepository.updateConcept(conceptEntity)
            } else {
                conceptRepository.insertConcept(conceptEntity)
            }

            _editUiState.value = _editUiState.value.copy(
                isLoading = false,
                navigateBack = true
            )
        }
    }

    fun toggleConceptEnabled(id: Long, enabled: Boolean) {
        viewModelScope.launch {
            val concept = conceptRepository.getConceptById(id)
            concept?.let {
                val updatedConcept = it.copy(isEnabled = enabled)
                conceptRepository.updateConcept(updatedConcept)
            }
        }
    }

    fun clearEditState() {
        _editUiState.value = ConceptEditUiState()
    }
}
