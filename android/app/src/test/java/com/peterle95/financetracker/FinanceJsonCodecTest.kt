package com.peterle95.financetracker

import com.peterle95.financetracker.data.FinanceJsonCodec
import com.peterle95.financetracker.data.FinanceJsonFileStore
import com.peterle95.financetracker.domain.CategoryDefaults
import com.peterle95.financetracker.domain.TransactionType
import kotlinx.coroutines.runBlocking
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.jsonArray
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

class FinanceJsonCodecTest {
    @Test
    fun loadingJsonDocumentFromTextAppliesDefaultsAndPreservesFields() {
        val document = FinanceJsonCodec.parse(sampleJson)

        assertEquals(2, document.transactions.size)
        val expense = document.transactions.first { it.type == TransactionType.Expense }
        assertNull(expense.exportId)
        assertEquals("2026-06-09", expense.behaviorDate)
        assertEquals(CategoryDefaults.expense, document.categories.expenses)
        assertEquals(42.0, document.budgetSettings["bank_account_balance"]!!.jsonPrimitive.content.toDouble(), 0.0)
        assertTrue(document.topLevelExtra.containsKey("unexpected_root"))
        assertTrue(document.records.first().extraJson.containsKey("note"))
    }

    @Test
    fun addingTransactionPreservesUnknownFieldsAndBudgetSettings() {
        val document = FinanceJsonCodec.parse(sampleJson)
        val updated = FinanceJsonCodec.addTransaction(
            document = document,
            type = TransactionType.Expense,
            date = "2026-06-12",
            amount = 8.25,
            category = "Food",
            description = "Coffee",
            id = "android-uuid",
        )
        val root = Json.parseToJsonElement(FinanceJsonCodec.encode(updated)).jsonObject

        assertEquals("root", root["unexpected_root"]!!.jsonPrimitive.content)
        assertEquals(42.0, root["budget_settings"]!!.jsonObject["bank_account_balance"]!!.jsonPrimitive.content.toDouble(), 0.0)
        assertEquals("kept", root["expenses"]!!.jsonArray[0].jsonObject["note"]!!.jsonPrimitive.content)
        assertEquals("android-uuid", root["expenses"]!!.jsonArray[1].jsonObject["id"]!!.jsonPrimitive.content)
    }

    @Test
    fun deletingTransactionUsesExportedId() {
        val document = FinanceJsonCodec.parse(sampleJson)
        val updated = FinanceJsonCodec.deleteTransactionByExportId(document, "income-1")
        val root = Json.parseToJsonElement(FinanceJsonCodec.encode(updated)).jsonObject

        assertEquals(0, root["incomes"]!!.jsonArray.size)
        assertEquals(1, root["expenses"]!!.jsonArray.size)
    }

    @Test
    fun editingCategoriesWritesThemBackToJson() {
        val document = FinanceJsonCodec.parse(sampleJson)
        val updated = FinanceJsonCodec.updateCategories(
            document = document,
            type = TransactionType.Expense,
            categories = listOf("Groceries", "Travel", "Groceries"),
        )
        val root = Json.parseToJsonElement(FinanceJsonCodec.encode(updated)).jsonObject
        val categories = root["categories"]!!.jsonObject["Expense"]!!.jsonArray.map { it.jsonPrimitive.content }

        assertEquals(listOf("Groceries", "Travel"), categories)
    }

    @Test
    fun fileStoreReloadsLatestText() = runBlocking {
        var fileText = sampleJson
        val store = FinanceJsonFileStore(
            readText = { fileText },
            writeText = { fileText = it },
        )

        store.reload()
        assertEquals(2, store.document.value.transactions.size)

        fileText = FinanceJsonCodec.encode(
            FinanceJsonCodec.addTransaction(
                FinanceJsonCodec.parse(fileText),
                TransactionType.Income,
                "2026-06-20",
                20.0,
                "Gift",
                "Syncthing update",
                id = "desktop-change",
            ),
        )
        store.reload()

        assertEquals(3, store.document.value.transactions.size)
        assertTrue(store.document.value.transactions.any { it.exportId == "desktop-change" })
    }

    private val sampleJson = """
        {
          "expenses": [
            {
              "date": "2026-06-10",
              "amount": 12.5,
              "category": "Food",
              "description": "Lunch",
              "behavior_date": "2026-06-09",
              "note": "kept"
            }
          ],
          "incomes": [
            {
              "id": "income-1",
              "date": "2026-06-01",
              "amount": 1000,
              "category": "Salary",
              "description": "Pay"
            }
          ],
          "budget_settings": { "bank_account_balance": 42 },
          "unexpected_root": "root"
        }
    """.trimIndent()
}
