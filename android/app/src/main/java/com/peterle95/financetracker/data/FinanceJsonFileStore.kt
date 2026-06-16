package com.peterle95.financetracker.data

import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow

class FinanceJsonFileStore(
    private val readText: suspend () -> String,
    private val writeText: suspend (String) -> Unit,
) {
    private val _document = MutableStateFlow(FinanceDocument.empty())
    val document: StateFlow<FinanceDocument> = _document.asStateFlow()

    suspend fun reload(): FinanceDocument {
        val loaded = FinanceJsonCodec.parse(readText())
        _document.value = loaded
        return loaded
    }

    suspend fun mutate(transform: (FinanceDocument) -> FinanceDocument): FinanceDocument {
        val latest = FinanceJsonCodec.parse(readText())
        val updated = transform(latest)
        val updatedText = FinanceJsonCodec.encode(updated)
        writeText(updatedText)
        val written = FinanceJsonCodec.parse(updatedText)
        _document.value = written
        return written
    }
}
